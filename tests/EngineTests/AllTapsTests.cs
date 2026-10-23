using NUnit.Framework;
using YARG.Core;
using YARG.Core.Chart;
using YARG.Core.Game;
using YARG.Core.Input;

namespace GuitarHero.EngineTests;

/// <summary>
/// Jogar no controle sem palhetar: com o modificador AllTaps (que o fork liga nos perfis de controle),
/// só apertar os trastes no tempo acerta todas as notas; sem ele, as notas de palhetada viram Miss.
/// </summary>
[TestFixture]
public class AllTapsTests
{
    private static readonly GuitarAction[] FretActions =
        [GuitarAction.GreenFret, GuitarAction.RedFret, GuitarAction.YellowFret, GuitarAction.BlueFret, GuitarAction.OrangeFret];

    // Notas soltas, acordes, repetição da mesma nota (que não vira HOPO) e um sustain.
    private static string Chart() => ChartText.Build(120,
    [
        new(4, "G"), new(5, "R"), new(6, "R"), new(7, "Y"),
        new(8, "GR"), new(9, "GR"), new(10, "YB"), new(11, "O"),
        new(12, "B", LengthBeats: 2), new(15, "G"), new(15.5, "R"), new(16, "Y"),
    ]);

    private static YargProfile Profile(Modifier modifier)
    {
        var profile = new YargProfile { GameMode = GameMode.FiveFretGuitar };
        if (modifier != Modifier.None) profile.AddSingleModifier(modifier);
        return profile;
    }

    /// <summary>Jogador de controle: aperta os trastes de cada nota no tempo e solta antes da próxima; nunca palheta.</summary>
    private static IReadOnlyList<GameInput> FretsOnly(InstrumentDifficulty<GuitarNote> chart)
    {
        var inputs = new Inputs();
        var notes = chart.Notes;
        for (int n = 0; n < notes.Count; n++)
        {
            var note = notes[n];
            int mask = note.NoteMask & 0b11111;
            double next = n + 1 < notes.Count ? notes[n + 1].Time : note.TimeEnd + 1;
            double release = note.IsSustain ? note.TimeEnd : Math.Min(note.Time + 0.08, next - 0.02);
            for (int i = 0; i < 5; i++)
            {
                if ((mask & (1 << i)) == 0) continue;
                inputs.Press(note.Time, FretActions[i]);
                inputs.Release(release, FretActions[i]);
            }
        }
        return inputs.Build();
    }

    private static Rig PlayFretsOnly((InstrumentDifficulty<GuitarNote> Notes, SyncTrack Sync) loaded, Modifier modifier)
    {
        Profile(modifier).ApplyModifiers(loaded.Notes, loaded.Sync);
        var rig = new Rig(loaded);
        return rig.Play(FretsOnly(rig.Chart));
    }

    [Test]
    public void WithAllTaps_FretsAloneHitEveryNote()
    {
        var rig = PlayFretsOnly(ChartText.Load(Chart()), Modifier.AllTaps);
        TestContext.Out.WriteLine("AllTaps: " + rig.Summary());
        Assert.That(rig.Stats.NotesHit, Is.EqualTo(rig.Stats.TotalNotes), rig.Summary());
        Assert.That(rig.Misses, Is.Empty);
    }

    [Test]
    public void WithoutAllTaps_FretsAloneMissStrumNotes()
    {
        var rig = PlayFretsOnly(ChartText.Load(Chart()), Modifier.None);
        TestContext.Out.WriteLine("sem modificador: " + rig.Summary());
        // O sintoma do jogo: os trastes acendem, mas a nota de palhetada não conta.
        Assert.That(rig.Stats.NotesHit, Is.LessThan(rig.Stats.TotalNotes / 2), rig.Summary());
    }

    /// <summary>
    /// Mesma conferência numa música de verdade: YARG_SONG=pasta da música (com notes.mid ou notes.chart),
    /// YARG_DIFFICULTY=Easy|Medium|Hard|Expert (padrão Hard). Sem a variável, o teste é ignorado.
    /// </summary>
    [Test]
    public void RealSong_WithAllTaps_FretsAloneHitAlmostEverything()
    {
        string? folder = Environment.GetEnvironmentVariable("YARG_SONG");
        if (string.IsNullOrEmpty(folder)) Assert.Ignore("YARG_SONG não definido");

        string file = new[] { "notes.mid", "notes.chart" }.Select(f => Path.Combine(folder!, f)).First(File.Exists);
        var difficulty = Enum.Parse<Difficulty>(Environment.GetEnvironmentVariable("YARG_DIFFICULTY") ?? "Hard");
        var song = SongChart.FromFile(ParseSettings.Default, file);

        var with = PlayFretsOnly((song.FiveFretGuitar.GetDifficulty(difficulty), song.SyncTrack), Modifier.AllTaps);
        song = SongChart.FromFile(ParseSettings.Default, file);
        var without = PlayFretsOnly((song.FiveFretGuitar.GetDifficulty(difficulty), song.SyncTrack), Modifier.None);

        TestContext.Out.WriteLine($"{Path.GetFileName(folder)} ({difficulty})");
        TestContext.Out.WriteLine("  com AllTaps: " + with.Summary());
        TestContext.Out.WriteLine("  sem:         " + without.Summary());
        Assert.That(with.Stats.NotesHit, Is.GreaterThanOrEqualTo(with.Stats.TotalNotes * 0.98), with.Summary());
    }
}
