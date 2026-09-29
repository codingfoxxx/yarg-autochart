using System.Globalization;
using System.Text;
using YARG.Core;
using YARG.Core.Chart;
using YARG.Core.Engine.Guitar;
using YARG.Core.Engine.Guitar.Engines;
using YARG.Core.Game;
using YARG.Core.Input;

namespace GuitarHero.EngineTests;

/// <summary>Uma nota (ou acorde) de um chart de teste, posicionada em batidas.</summary>
/// <param name="Frets">"G", "R", "Y", "B", "O" combinados (ex.: "GR") ou "open".</param>
/// <param name="Flip">Emite <c>N 5</c> (inverte HOPO/strum natural).</param>
/// <param name="Tap">Emite <c>N 6</c>.</param>
public readonly record struct ChartNote(double Beat, string Frets, double LengthBeats = 0, bool Flip = false, bool Tap = false);

/// <summary>Monta um .chart de teste (resolução 192, BPM fixo, 4/4) e o carrega com o parser do YARG.Core.</summary>
public static class ChartText
{
    public const int Resolution = 192;

    public static string Build(double bpm, IEnumerable<ChartNote> notes, IEnumerable<(double StartBeat, double LengthBeats)>? starPower = null)
    {
        var lines = new List<(long Tick, int Order, string Text)>();
        foreach (var n in notes)
        {
            long tick = ToTick(n.Beat);
            long len = ToTick(n.LengthBeats);
            foreach (int fret in FretNumbers(n.Frets))
            {
                lines.Add((tick, 0, $"N {fret} {len}"));
            }
            if (n.Flip) lines.Add((tick, 1, "N 5 0"));
            if (n.Tap) lines.Add((tick, 1, "N 6 0"));
        }
        foreach (var (start, length) in starPower ?? [])
        {
            lines.Add((ToTick(start), 2, $"S 2 {ToTick(length)}"));
        }

        var sb = new StringBuilder();
        sb.Append("[Song]\r\n{\r\n  Name = \"teste\"\r\n  Resolution = ").Append(Resolution).Append("\r\n  Offset = 0\r\n}\r\n");
        sb.Append("[SyncTrack]\r\n{\r\n  0 = TS 4\r\n  0 = B ")
          .Append(((long) Math.Round(bpm * 1000)).ToString(CultureInfo.InvariantCulture)).Append("\r\n}\r\n");
        sb.Append("[Events]\r\n{\r\n}\r\n");
        sb.Append("[ExpertSingle]\r\n{\r\n");
        foreach (var (tick, _, text) in lines.OrderBy(l => l.Tick).ThenBy(l => l.Order))
        {
            sb.Append("  ").Append(tick.ToString(CultureInfo.InvariantCulture)).Append(" = ").Append(text).Append("\r\n");
        }
        sb.Append("}\r\n");
        return sb.ToString();
    }

    public static (InstrumentDifficulty<GuitarNote> Notes, SyncTrack Sync) Load(string chartText)
    {
        var chart = SongChart.FromDotChart(ParseSettings.Default_Chart, chartText);
        return (chart.FiveFretGuitar.GetDifficulty(Difficulty.Expert), chart.SyncTrack);
    }

    public static long ToTick(double beats) => (long) Math.Round(beats * Resolution);

    private static IEnumerable<int> FretNumbers(string frets)
    {
        if (frets.Equals("open", StringComparison.OrdinalIgnoreCase))
        {
            yield return 7;
            yield break;
        }
        foreach (char c in frets.ToUpperInvariant())
        {
            yield return c switch
            {
                'G' => 0, 'R' => 1, 'Y' => 2, 'B' => 3, 'O' => 4,
                _ => throw new ArgumentException($"Traste desconhecido: {c}"),
            };
        }
    }
}

/// <summary>
/// Monta a engine de 5 trastes do jeito que o jogo monta (preset padrão) e a roda com um laço de
/// frames igual ao do jogo: a cada frame, enfileira os inputs cujo timestamp já passou e chama
/// <c>Update</c> com o tempo do frame.
/// </summary>
public sealed class Rig
{
    // Mesmos limiares de estrela do FiveFretGuitarPlayer do jogo.
    public static readonly float[] StarThresholds = [0.06f, 0.12f, 0.2f, 0.47f, 0.78f, 1.15f];
    public static readonly float[] SoloStarThresholds = [0.05f, 0.1f, 0.2f, 0.35f, 0.65f, 0.95f];

    public YargFiveFretGuitarEngine Engine { get; }
    public InstrumentDifficulty<GuitarNote> Chart { get; }
    public SyncTrack Sync { get; }
    public GuitarStats Stats => Engine.EngineStats;

    /// <summary>(tick da nota, tempo da engine no acerto)</summary>
    public List<(uint Tick, double Time)> Hits { get; } = [];
    public List<uint> Misses { get; } = [];
    public List<double> OverstrumTimes { get; } = [];

    public Rig(string chartText, GuitarEngineParameters? parameters = null)
        : this(ChartText.Load(chartText), parameters)
    {
    }

    public Rig((InstrumentDifficulty<GuitarNote> Notes, SyncTrack Sync) loaded, GuitarEngineParameters? parameters = null)
    {
        (Chart, Sync) = loaded;
        Engine = new YargFiveFretGuitarEngine(Chart, Sync, parameters ?? DefaultParameters(), isBot: false);
        // O jogo sempre chama SetSpeed logo após criar a engine (TrackPlayer). Sem isso SongSpeed fica 0
        // e, por exemplo, a tolerância de soltura do sustain vira zero.
        Engine.SetSpeed(1.0);
        Engine.OnNoteHit += (_, note) => Hits.Add((note.Tick, Engine.CurrentTime));
        Engine.OnNoteMissed += (_, note) => Misses.Add(note.Tick);
        Engine.OnOverstrum += () => OverstrumTimes.Add(Engine.CurrentTime);
    }

    public static GuitarEngineParameters DefaultParameters() =>
        EnginePreset.Default.FiveFretGuitar.Create(StarThresholds, SoloStarThresholds, isBass: false);

    /// <summary>Tempo do fim do chart (última nota, com sustain) + folga.</summary>
    public double EndTime(double slack = 1.0)
    {
        double end = 0;
        foreach (var n in Chart.Notes)
        {
            end = Math.Max(end, n.TimeEnd);
            foreach (var c in n.ChildNotes) end = Math.Max(end, c.TimeEnd);
        }
        return end + slack;
    }

    /// <param name="fps">Taxa de quadros simulada.</param>
    /// <param name="jitterSeed">Se informado, varia cada frame em ±10% (como o ReplayAnalyzer do YARG).</param>
    public Rig Play(IReadOnlyList<GameInput> inputs, double fps = 60, double? endTime = null, double startTime = -1.0, int? jitterSeed = null)
    {
        var rnd = jitterSeed is int seed ? new Random(seed) : null;
        double end = endTime ?? EndTime();
        double dt = 1.0 / fps;
        double t = startTime;
        int next = 0;
        while (true)
        {
            while (next < inputs.Count && inputs[next].Time <= t)
            {
                var gi = inputs[next++];
                Engine.QueueInput(ref gi);
            }
            Engine.Update(t);
            if (t >= end) break;
            double step = rnd is null ? dt : dt * (0.9 + 0.2 * rnd.NextDouble());
            t = Math.Min(t + step, end);
        }
        return this;
    }

    /// <summary>Resumo comparável entre execuções.</summary>
    public string Summary() =>
        $"hit={Stats.NotesHit}/{Stats.TotalNotes} over={Stats.Overstrums} ghost={Stats.GhostInputs} " +
        $"maxCombo={Stats.MaxCombo} score={Stats.TotalScore} sp={Stats.StarPowerTickAmount}";
}

/// <summary>Constrói sequências de inputs com timestamp (como o jogo entrega à engine).</summary>
public sealed class Inputs
{
    private readonly List<GameInput> _list = [];
    private int _order;
    private readonly List<(double Time, int Order, GameInput Input)> _pending = [];

    public Inputs Fret(double time, GuitarAction fret, bool down)
    {
        _pending.Add((time, _order++, GameInput.Create(time, fret, down)));
        return this;
    }

    public Inputs Press(double time, params GuitarAction[] frets)
    {
        foreach (var f in frets) Fret(time, f, true);
        return this;
    }

    public Inputs Release(double time, params GuitarAction[] frets)
    {
        foreach (var f in frets) Fret(time, f, false);
        return this;
    }

    /// <summary>Palhetada para baixo: aperta em <paramref name="time"/> e solta 30 ms depois.</summary>
    public Inputs Strum(double time, double duration = 0.030, GuitarAction direction = GuitarAction.StrumDown)
    {
        _pending.Add((time, _order++, GameInput.Create(time, direction, true)));
        _pending.Add((time + duration, _order++, GameInput.Create(time + duration, direction, false)));
        return this;
    }

    public Inputs StarPower(double time, double duration = 0.05)
    {
        _pending.Add((time, _order++, GameInput.Create(time, GuitarAction.StarPower, true)));
        _pending.Add((time + duration, _order++, GameInput.Create(time + duration, GuitarAction.StarPower, false)));
        return this;
    }

    public IReadOnlyList<GameInput> Build() =>
        _pending.OrderBy(p => p.Time).ThenBy(p => p.Order).Select(p => p.Input).ToList();
}

/// <summary>
/// Gera os inputs de um jogador "humano" para um chart: aperta os trastes um pouco antes da
/// palhetada, faz HOPO/tap só com os trastes, segura sustains e aplica um erro de tempo por nota.
/// </summary>
public static class PlayerSim
{
    private static readonly GuitarAction[] FretActions =
        [GuitarAction.GreenFret, GuitarAction.RedFret, GuitarAction.YellowFret, GuitarAction.BlueFret, GuitarAction.OrangeFret];

    /// <param name="timingError">Erro (s) aplicado a cada nota; 0 = perfeito.</param>
    /// <param name="fretLead">Quanto antes da palhetada os trastes são apertados.</param>
    /// <param name="strumHopos">Se verdadeiro, também palheta HOPOs (como um jogador cauteloso).</param>
    public static IReadOnlyList<GameInput> Play(InstrumentDifficulty<GuitarNote> chart, Func<GuitarNote, double>? timingError = null,
        double fretLead = 0.015, bool strumHopos = false)
    {
        var inputs = new Inputs();
        int held = 0;
        foreach (var note in chart.Notes)
        {
            double err = timingError?.Invoke(note) ?? 0;
            double t = note.Time + err;
            int mask = note.NoteMask & 0b11111;              // aberta = nenhum traste
            bool strum = note.IsStrum || strumHopos;
            double fretTime = strum ? t - fretLead : t;

            // Solta o que não faz parte da nota, depois aperta o que falta (pull-off antes de hammer-on).
            for (int i = 0; i < 5; i++)
            {
                int bit = 1 << i;
                if ((held & bit) != 0 && (mask & bit) == 0) inputs.Release(fretTime, FretActions[i]);
            }
            for (int i = 0; i < 5; i++)
            {
                int bit = 1 << i;
                if ((mask & bit) != 0 && (held & bit) == 0) inputs.Press(fretTime, FretActions[i]);
            }
            held = mask;

            if (strum) inputs.Strum(t);

            // Sustain: segura até o fim; nota sem sustain: solta pouco antes da próxima (se a próxima mudar trastes).
            double releaseAt = note.IsSustain ? note.TimeEnd + err : double.NaN;
            if (!double.IsNaN(releaseAt))
            {
                for (int i = 0; i < 5; i++)
                {
                    if ((mask & (1 << i)) != 0) inputs.Release(releaseAt, FretActions[i]);
                }
                held = 0;
            }
        }
        for (int i = 0; i < 5; i++)
        {
            if ((held & (1 << i)) != 0) inputs.Release(chart.Notes[^1].TimeEnd + 0.5, FretActions[i]);
        }
        return inputs.Build();
    }

    /// <summary>Erro gaussiano reprodutível (Box-Muller), em segundos.</summary>
    public static Func<GuitarNote, double> Gaussian(double sigma, int seed)
    {
        var rnd = new Random(seed);
        return _ =>
        {
            double u1 = 1.0 - rnd.NextDouble(), u2 = rnd.NextDouble();
            return sigma * Math.Sqrt(-2.0 * Math.Log(u1)) * Math.Cos(2 * Math.PI * u2);
        };
    }
}
