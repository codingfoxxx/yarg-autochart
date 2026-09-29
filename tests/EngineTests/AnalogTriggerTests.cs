using NUnit.Framework;
using YARG.Core.Input;
using YARG.Input;

namespace GuitarHero.EngineTests;

/// <summary>
/// Histerese dos gatilhos analógicos do controle (mudança do fork em
/// YARG/Assets/Script/Input/Bindings/AnalogButtonHysteresis.cs, compilado aqui como link).
/// </summary>
public class AnalogTriggerTests
{
    private const GuitarAction G = GuitarAction.GreenFret;
    private static double Sec(double beats) => beats * 0.5; // 120 BPM

    [Test]
    public void WithoutHysteresis_IsExactlyTheUpstreamRule()
    {
        float[] pressPoints = [-0.5f, 0f, 0.1f, 0.5f, 0.9f, 1f];
        foreach (bool wasPressed in new[] { false, true })
        foreach (float pp in pressPoints)
        for (int i = -100; i <= 120; i++)
        {
            float v = i / 100f;
            Assert.That(AnalogButtonHysteresis.IsPressed(wasPressed, v, pp, AnalogButtonHysteresis.NO_HYSTERESIS),
                Is.EqualTo(v >= pp), $"estava={wasPressed} valor={v} ponto={pp}");
        }
    }

    [Test]
    public void WithHysteresis_ReleasesOnlyBelowTheReleasePoint()
    {
        const float pp = 0.5f, rt = 0.75f; // solta abaixo de 0,375
        bool s = false;
        (float Value, bool Expected)[] sequence =
        [
            (0.49f, false), (0.50f, true), (0.45f, true), (0.38f, true), (0.376f, true),
            (0.374f, false), (0.45f, false), (0.499f, false), (0.5f, true),
        ];
        foreach (var (value, expected) in sequence)
        {
            s = AnalogButtonHysteresis.IsPressed(s, value, pp, rt);
            Assert.That(s, Is.EqualTo(expected), $"valor {value}");
        }
    }

    [TestCase(float.NaN)]
    [TestCase(0f)]
    [TestCase(-0.5f)]
    [TestCase(1.5f)]
    public void InvalidReleaseThreshold_DisablesHysteresis(float rt)
    {
        Assert.That(AnalogButtonHysteresis.SanitizeReleaseThreshold(rt), Is.EqualTo(1f));
    }

    [Test]
    public void BindingsFileFormat_IsIndependentOfTheSystemLanguage()
    {
        using (Assert.EnterMultipleScope())
        {
            Assert.That(AnalogButtonHysteresis.Format(0.75f), Is.EqualTo("0.75"));
            Assert.That(AnalogButtonHysteresis.TryParse("0.75", out float ok), Is.True);
            Assert.That(ok, Is.EqualTo(0.75f));
            // vírgula decimal (formato de outro idioma) é recusada em vez de virar 75
            Assert.That(AnalogButtonHysteresis.TryParse("0,75", out float bad), Is.False);
            Assert.That(bad, Is.EqualTo(1f));
        }
    }

    /// <summary>
    /// Sustain longo segurado com um gatilho em que o dedo relaxa e fica perto do meio do curso
    /// (0,5 ± 0,06, oscilando a 3 Hz, com ruído). Sem histerese, cada passagem por 0,5 vira uma
    /// soltura; se durar mais que a tolerância de 25 ms, a engine derruba o sustain.
    /// </summary>
    [Test]
    public void TriggerHoveringAroundThePressPoint_KeepsTheSustainOnlyWithHysteresis()
    {
        string chart = ChartText.Build(120, [new(4, "G", LengthBeats: 8)]);
        double start = Sec(4), end = Sec(12);
        int droppedUpstream = 0, droppedFork = 0, releasesUpstream = 0, releasesFork = 0;

        for (int seed = 1; seed <= 20; seed++)
        {
            var signal = TriggerSignal.PressThenHover(start - 0.03, start + 0.4, end + 0.05, hover: 0.5, drift: 0.06, noise: 0.01, seed);
            // referência: o mesmo movimento lido com ponto de acionamento quase zero = sustain segurado inteiro
            var full = new Rig(chart).Play(WithStrum(TriggerSignal.ToEvents(signal, G, 0.01f, 1f), start), 240);

            var upstream = TriggerSignal.ToEvents(signal, G, pressPoint: 0.5f, releaseThreshold: 1f);
            var fork = TriggerSignal.ToEvents(signal, G, pressPoint: 0.5f, releaseThreshold: 0.75f);
            var rigUpstream = new Rig(chart).Play(WithStrum(upstream, start), 240);
            var rigFork = new Rig(chart).Play(WithStrum(fork, start), 240);

            releasesUpstream += upstream.Count(e => !e.Button);
            releasesFork += fork.Count(e => !e.Button);
            if (rigUpstream.Stats.SustainScore < full.Stats.SustainScore) droppedUpstream++;
            if (rigFork.Stats.SustainScore < full.Stats.SustainScore) droppedFork++;
            Assert.That(rigFork.Stats.NotesHit, Is.EqualTo(1));
        }

        TestContext.Out.WriteLine($"20 execuções: sustain derrubado sem histerese {droppedUpstream}×, com histerese {droppedFork}×; " +
                                  $"solturas geradas {releasesUpstream} × {releasesFork}");
        using (Assert.EnterMultipleScope())
        {
            Assert.That(droppedFork, Is.Zero, "com histerese o sustain nunca cai");
            Assert.That(droppedUpstream, Is.GreaterThan(0), "sem histerese o cenário derruba o sustain");
            Assert.That(releasesFork, Is.EqualTo(20), "com histerese só a soltura final");
        }
    }

    /// <summary>Apertar e soltar o gatilho por inteiro (uso normal): a histerese não muda o jogo.</summary>
    [Test]
    public void FullPressesAndReleases_PlayTheSameWithAndWithoutHysteresis()
    {
        var notes = Enumerable.Range(0, 16).Select(i => new ChartNote(4 + i, i % 2 == 0 ? "G" : "R")).ToList();
        string chart = ChartText.Build(120, notes);

        var inputs = new List<(double Time, GuitarAction Action, bool Down)>();
        var greenSignal = new List<TriggerSample>();
        for (int i = 0; i < 16; i++)
        {
            double t = Sec(4 + i);
            if (i % 2 == 0)
                greenSignal.AddRange(TriggerSignal.FullPress(t - 0.06, t + 0.25));
            else
            {
                inputs.Add((t - 0.03, GuitarAction.RedFret, true));
                inputs.Add((t + 0.25, GuitarAction.RedFret, false));
            }
            inputs.Add((t, GuitarAction.StrumDown, true));
            inputs.Add((t + 0.03, GuitarAction.StrumDown, false));
        }

        IReadOnlyList<GameInput> Merge(IEnumerable<GameInput> trigger) =>
            inputs.Select(x => GameInput.Create(x.Time, x.Action, x.Down)).Concat(trigger).OrderBy(e => e.Time).ToList();

        var upstream = new Rig(chart).Play(Merge(TriggerSignal.ToEvents(greenSignal, G, 0.5f, 1f)), 240);
        var fork = new Rig(chart).Play(Merge(TriggerSignal.ToEvents(greenSignal, G, 0.5f, 0.75f)), 240);

        TestContext.Out.WriteLine($"sem histerese: {upstream.Summary()} | com histerese: {fork.Summary()}");
        using (Assert.EnterMultipleScope())
        {
            Assert.That(fork.Stats.NotesHit, Is.EqualTo(16));
            Assert.That(fork.Summary(), Is.EqualTo(upstream.Summary()));
        }
    }

    private static IReadOnlyList<GameInput> WithStrum(IReadOnlyList<GameInput> frets, double strumAt) =>
        frets.Concat([GameInput.Create(strumAt, GuitarAction.StrumDown, true), GameInput.Create(strumAt + 0.03, GuitarAction.StrumDown, false)])
             .OrderBy(e => e.Time).ToList();
}

public readonly record struct TriggerSample(double Time, float Value);

/// <summary>Sinal de um gatilho de controle Xbox como o jogo o recebe: XInput a 250 Hz, 8 bits.</summary>
public static class TriggerSignal
{
    public const double PollInterval = 1.0 / 250;

    private static float Quantize(double v) => (float) (Math.Round(Math.Clamp(v, 0, 1) * 255) / 255);

    /// <summary>Aperta até o fim em ~24 ms, segura, e a partir de <paramref name="hoverFrom"/> relaxa para perto de <paramref name="hover"/>.</summary>
    public static List<TriggerSample> PressThenHover(double pressAt, double hoverFrom, double releaseAt,
        double hover, double drift, double noise, int seed)
    {
        var rnd = new Random(seed);
        double phase = rnd.NextDouble() * 2 * Math.PI;
        var samples = new List<TriggerSample>();
        for (double t = pressAt - 0.02; t <= releaseAt + 0.06; t += PollInterval)
        {
            double v;
            if (t < pressAt) v = 0;
            else if (t < pressAt + 0.024) v = (t - pressAt) / 0.024;
            else if (t < hoverFrom) v = 1;
            else if (t < releaseAt)
            {
                double relax = Math.Min(1, (t - hoverFrom) / 0.15); // desce de 1 até o meio em 150 ms
                double target = hover + drift * Math.Sin(2 * Math.PI * 3 * (t - hoverFrom) + phase) + noise * Gauss(rnd);
                v = 1 + (target - 1) * relax;
            }
            else v = Math.Max(0, 0.5 - (t - releaseAt) / 0.02);
            samples.Add(new(t, Quantize(v)));
        }
        return samples;
    }

    /// <summary>Aperto e soltura completos, rápidos (~24 ms e ~16 ms).</summary>
    public static List<TriggerSample> FullPress(double pressAt, double releaseAt)
    {
        var samples = new List<TriggerSample>();
        for (double t = pressAt - 0.01; t <= releaseAt + 0.03; t += PollInterval)
        {
            double v = t < pressAt ? 0
                : t < pressAt + 0.024 ? (t - pressAt) / 0.024
                : t < releaseAt ? 1
                : Math.Max(0, 1 - (t - releaseAt) / 0.016);
            samples.Add(new(t, Quantize(v)));
        }
        return samples;
    }

    /// <summary>
    /// Converte amostras em eventos de traste como o binding do jogo: estado com histerese e debounce
    /// de 5 ms depois de cada aperto (modo "Press" padrão do SingleButtonBinding).
    /// </summary>
    public static List<GameInput> ToEvents(IReadOnlyList<TriggerSample> samples, GuitarAction action,
        float pressPoint, float releaseThreshold, double debounce = 0.005)
    {
        var events = new List<GameInput>();
        bool pressed = false, emitted = false;
        double debounceUntil = double.MinValue;
        foreach (var s in samples)
        {
            pressed = AnalogButtonHysteresis.IsPressed(pressed, s.Value, pressPoint, releaseThreshold);
            if (s.Time < debounceUntil || pressed == emitted)
                continue;
            emitted = pressed;
            events.Add(GameInput.Create(s.Time, action, pressed));
            if (pressed)
                debounceUntil = s.Time + debounce;
        }
        return events;
    }

    private static double Gauss(Random r) =>
        Math.Sqrt(-2 * Math.Log(1 - r.NextDouble())) * Math.Cos(2 * Math.PI * r.NextDouble());
}
