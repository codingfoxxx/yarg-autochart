using NUnit.Framework;
using YARG.Core.Chart;
using YARG.Core.Engine.Guitar;
using YARG.Core.Game;
using YARG.Core.Input;

namespace GuitarHero.EngineTests;

/// <summary>
/// Auditoria da engine de 5 trastes do YARG.Core com inputs temporizados.
/// Tempos: charts a 120 BPM, então 1 batida = 0,5 s. Parâmetros = preset padrão do jogo
/// (janela estática de 140 ms = ±70 ms, tolerância de palhetada 50/25 ms, HOPO 80 ms, anti-ghosting).
/// </summary>
[TestFixture]
public class FiveFretTimingTests
{
    private const GuitarAction G = GuitarAction.GreenFret;
    private const GuitarAction R = GuitarAction.RedFret;
    private const GuitarAction Y = GuitarAction.YellowFret;
    private const GuitarAction B = GuitarAction.BlueFret;
    private const GuitarAction O = GuitarAction.OrangeFret;

    private static double Sec(double beat) => beat * 0.5; // 120 BPM

    /// <summary>Chart variado: palhetadas, acordes, corrida de semicolcheias (HOPOs naturais),
    /// tercinas, strum forçado (N 5), tap (N 6), nota aberta, sustains e duas frases de star power.</summary>
    public static string MixedChart() => ChartText.Build(120,
    [
        new(4, "G"), new(5, "R"), new(6, "Y"), new(7, "B"), new(8, "O"),
        new(9, "GR"), new(10, "RY"), new(11, "YB"),
        // semicolcheias (48 ticks <= 65): HOPO natural quando o traste muda
        new(12, "G"), new(12.25, "R"), new(12.5, "Y"), new(12.75, "R"), new(13, "G"),
        // semicolcheia com strum forçado
        new(14, "G"), new(14.25, "R", Flip: true),
        // tercinas (64 ticks <= 65): HOPO
        new(16, "Y"), new(16 + 1.0 / 3, "B"), new(16 + 2.0 / 3, "O"),
        new(18, "B", Tap: true), new(18.5, "Y", Tap: true),
        new(20, "open"),
        new(22, "G", LengthBeats: 2), new(25, "GR", LengthBeats: 1),
        new(28, "Y"), new(29, "B"), new(30, "Y"), new(31, "R"),
    ],
    starPower: [(4, 1.1), (9, 2.1)]);

    [Test]
    public void Parser_ProducesTheNoteTypesTheGeneratorRelieson()
    {
        var (notes, _) = ChartText.Load(MixedChart());
        string Type(double beat) => notes.Notes.Single(n => n.Tick == ChartText.ToTick(beat)).Type.ToString();

        using (Assert.EnterMultipleScope())
        {
            Assert.That(Type(4), Is.EqualTo("Strum"), "primeira nota");
            Assert.That(Type(5), Is.EqualTo("Strum"), "semínima (192 ticks > 65)");
            Assert.That(Type(9), Is.EqualTo("Strum"), "acorde nunca é HOPO natural");
            Assert.That(Type(12.25), Is.EqualTo("Hopo"), "semicolcheia com troca de traste");
            Assert.That(Type(13), Is.EqualTo("Hopo"), "semicolcheia R→G");
            Assert.That(Type(14.25), Is.EqualTo("Strum"), "HOPO natural invertido por N 5");
            Assert.That(Type(16 + 1.0 / 3), Is.EqualTo("Hopo"), "tercina (64 ticks)");
            Assert.That(Type(18), Is.EqualTo("Tap"), "N 6");
            Assert.That(notes.Notes.Single(n => n.Tick == ChartText.ToTick(20)).Fret, Is.EqualTo((int) FiveFretGuitarFret.Open));
            Assert.That(notes.Notes.Single(n => n.Tick == ChartText.ToTick(22)).IsSustain, Is.True);
        }
    }

    [TestCase(30)]
    [TestCase(60)]
    [TestCase(144)]
    [TestCase(240)]
    public void PerfectPlay_HitsEveryNote_AtAnyFrameRate(double fps)
    {
        var rig = new Rig(MixedChart());
        rig.Play(PlayerSim.Play(rig.Chart), fps);

        TestContext.Out.WriteLine($"{fps} fps: {rig.Summary()}");
        using (Assert.EnterMultipleScope())
        {
            Assert.That(rig.Stats.NotesHit, Is.EqualTo(rig.Stats.TotalNotes), "todas as notas acertadas");
            Assert.That(rig.Stats.Overstrums, Is.Zero, "sem overstrum");
            Assert.That(rig.Stats.MaxCombo, Is.EqualTo(rig.Stats.TotalNotes), "combo cheio");
            Assert.That(rig.Stats.StarPowerPhrasesHit, Is.EqualTo(2), "duas frases de star power");
        }
    }

    /// <summary>
    /// Propriedade central da auditoria: com os mesmos inputs (timestamps), o resultado não pode
    /// depender da taxa de quadros nem do jitter entre quadros.
    /// </summary>
    [Test]
    public void HumanizedPlay_ResultIsIndependentOfFrameRate()
    {
        double[] rates = [24, 30, 60, 75, 144, 240, 1000];
        int differences = 0;
        for (int seed = 1; seed <= 40; seed++)
        {
            string chart = MixedChart();
            var reference = new Rig(chart);
            var inputs = PlayerSim.Play(reference.Chart, PlayerSim.Gaussian(sigma: 0.035, seed));
            reference.Play(inputs, 60);
            string expected = reference.Summary();

            foreach (double fps in rates)
            {
                foreach (int? jitter in new int?[] { null, seed * 7 })
                {
                    var rig = new Rig(chart);
                    rig.Play(PlayerSim.Play(rig.Chart, PlayerSim.Gaussian(sigma: 0.035, seed)), fps, jitterSeed: jitter);
                    if (rig.Summary() != expected)
                    {
                        differences++;
                        TestContext.Out.WriteLine($"seed {seed} @ {fps} fps (jitter {jitter}): {rig.Summary()}  vs 60 fps: {expected}");
                    }
                }
            }
        }
        Assert.That(differences, Is.Zero, "o resultado mudou com a taxa de quadros");
    }

    /// <summary>
    /// Varre o instante da palhetada em torno de uma nota isolada (trastes já apertados) e mede a
    /// janela efetiva. Janela nominal: ±70 ms; antes dela, a "tolerância curta" de 25 ms ainda
    /// deixa a palhetada valer quando a nota entra na janela.
    /// </summary>
    [Test]
    public void StrumWindow_EffectiveEdges()
    {
        var hits = new SortedDictionary<int, bool>();
        for (int ms = -130; ms <= 100; ms += 1)
        {
            var rig = new Rig(ChartText.Build(120, [new(4, "G")]));
            var inputs = new Inputs().Press(1.0, G).Strum(Sec(4) + ms / 1000.0).Release(3.5, G).Build();
            rig.Play(inputs, 240);
            hits[ms] = rig.Stats.NotesHit == 1;
        }

        int earliest = hits.First(kv => kv.Value).Key;
        int latest = hits.Last(kv => kv.Value).Key;
        bool contiguous = hits.Where(kv => kv.Key >= earliest && kv.Key <= latest).All(kv => kv.Value);
        TestContext.Out.WriteLine($"janela efetiva da palhetada: {earliest} ms até +{latest} ms (contínua: {contiguous})");

        using (Assert.EnterMultipleScope())
        {
            Assert.That(contiguous, Is.True, "a janela deve ser um intervalo contínuo");
            Assert.That(latest, Is.InRange(68, 70), "borda tardia = +70 ms");
            Assert.That(earliest, Is.InRange(-96, -94), "borda antecipada = -70 ms - 25 ms de tolerância curta");
        }
    }

    [TestCase(0.000, true)]
    [TestCase(0.030, true)]
    [TestCase(0.049, true)]
    [TestCase(0.060, false)]
    public void FretsPressedAfterStrum_CountOnlyWithinStrumLeniency(double fretDelay, bool shouldHit)
    {
        var rig = new Rig(ChartText.Build(120, [new(4, "R")]));
        double t = Sec(4);
        var inputs = new Inputs().Strum(t).Press(t + fretDelay, R).Release(3.5, R).Build();
        rig.Play(inputs, 240);

        Assert.That(rig.Stats.NotesHit == 1, Is.EqualTo(shouldHit),
            $"traste {fretDelay * 1000:0} ms depois da palhetada; {rig.Summary()}");
    }

    [Test]
    public void StrumChord_RequiresExactlyTheChordFrets()
    {
        double t = Sec(4);
        string chart = ChartText.Build(120, [new(4, "GR")]);

        var exact = new Rig(chart).Play(new Inputs().Press(1, G, R).Strum(t).Release(3.5, G, R).Build(), 240);
        var missing = new Rig(chart).Play(new Inputs().Press(1, G).Strum(t).Release(3.5, G).Build(), 240);
        var extra = new Rig(chart).Play(new Inputs().Press(1, G, R, Y).Strum(t).Release(3.5, G, R, Y).Build(), 240);

        using (Assert.EnterMultipleScope())
        {
            Assert.That(exact.Stats.NotesHit, Is.EqualTo(1), "G+R exato");
            Assert.That(missing.Stats.NotesHit, Is.Zero, "faltando traste");
            Assert.That(extra.Stats.NotesHit, Is.Zero, "traste a mais em acorde palhetado");
        }
    }

    [Test]
    public void SingleNote_AllowsLowerAnchors_ButNotHigherFrets()
    {
        double t = Sec(4);
        string chart = ChartText.Build(120, [new(4, "Y")]);

        var anchored = new Rig(chart).Play(new Inputs().Press(1, G, R, Y).Strum(t).Release(3.5, G, R, Y).Build(), 240);
        var higher = new Rig(chart).Play(new Inputs().Press(1, Y, B).Strum(t).Release(3.5, Y, B).Build(), 240);

        using (Assert.EnterMultipleScope())
        {
            Assert.That(anchored.Stats.NotesHit, Is.EqualTo(1), "G+R segurados abaixo do amarelo");
            Assert.That(higher.Stats.NotesHit, Is.Zero, "azul segurado acima do amarelo");
        }
    }

    [Test]
    public void Hopo_IsHitWithFretsOnly_WhenComboIsActive()
    {
        // G palhetado, R semicolcheia depois (HOPO natural)
        var rig = new Rig(ChartText.Build(120, [new(4, "G"), new(4.25, "R")]));
        double t0 = Sec(4), t1 = Sec(4.25);
        var inputs = new Inputs().Press(t0 - 0.02, G).Strum(t0).Press(t1, R).Release(3.5, G, R).Build();
        rig.Play(inputs, 240);

        using (Assert.EnterMultipleScope())
        {
            Assert.That(rig.Stats.NotesHit, Is.EqualTo(2), rig.Summary());
            Assert.That(rig.Stats.Overstrums, Is.Zero);
        }
    }

    [Test]
    public void Hopo_AfterAMiss_RequiresStrum()
    {
        // G não é tocado (erro); R (HOPO) apertado sem palhetar não pode valer com combo 0.
        var rig = new Rig(ChartText.Build(120, [new(4, "G"), new(4.25, "R")]));
        var inputs = new Inputs().Press(Sec(4.25), R).Release(3.5, R).Build();
        rig.Play(inputs, 240);

        Assert.That(rig.Stats.NotesHit, Is.Zero, rig.Summary());
    }

    [Test]
    public void Strum_RightAfterHopo_IsEatenWithoutOverstrum()
    {
        var rig = new Rig(ChartText.Build(120, [new(4, "G"), new(4.25, "R")]));
        double t0 = Sec(4), t1 = Sec(4.25);
        // palhetada "de reflexo" 40 ms depois do HOPO (dentro da tolerância de 80 ms)
        var inputs = new Inputs().Press(t0 - 0.02, G).Strum(t0).Press(t1, R).Strum(t1 + 0.040).Release(3.5, G, R).Build();
        rig.Play(inputs, 240);

        using (Assert.EnterMultipleScope())
        {
            Assert.That(rig.Stats.NotesHit, Is.EqualTo(2), rig.Summary());
            Assert.That(rig.Stats.Overstrums, Is.Zero, "a palhetada extra é absorvida pela tolerância de HOPO");
        }
    }

    [Test]
    public void Ghosting_AWrongHigherFret_BlocksTheNextHopo()
    {
        // G palhetado; antes do HOPO em Y, o jogador encosta em B (errado, acima) e depois vai para Y.
        var rig = new Rig(ChartText.Build(120, [new(4, "G"), new(4.25, "Y")]));
        double t0 = Sec(4), t1 = Sec(4.25);
        var inputs = new Inputs().Press(t0 - 0.02, G).Strum(t0)
            .Press(t1 - 0.03, B).Release(t1 - 0.01, B).Press(t1, Y)
            .Release(3.5, G, Y).Build();
        rig.Play(inputs, 240);

        using (Assert.EnterMultipleScope())
        {
            Assert.That(rig.Stats.GhostInputs, Is.GreaterThan(0), "o azul conta como ghost input");
            Assert.That(rig.Stats.NotesHit, Is.EqualTo(1), "com anti-ghosting, o HOPO não vale sem palhetar");
        }
    }

    [Test]
    public void Sustain_HeldToTheEnd_ScoresMoreThanReleasedEarly()
    {
        string chart = ChartText.Build(120, [new(4, "G", LengthBeats: 4)]);
        double t = Sec(4);
        var full = new Rig(chart).Play(new Inputs().Press(t - 0.02, G).Strum(t).Release(Sec(8) + 0.05, G).Build(), 240);
        var early = new Rig(chart).Play(new Inputs().Press(t - 0.02, G).Strum(t).Release(Sec(5), G).Build(), 240);

        TestContext.Out.WriteLine($"sustain inteiro: {full.Summary()} | solto cedo: {early.Summary()}");
        using (Assert.EnterMultipleScope())
        {
            Assert.That(full.Stats.SustainScore, Is.GreaterThan(early.Stats.SustainScore));
            Assert.That(early.Stats.NotesHit, Is.EqualTo(1), "soltar o sustain não conta como erro de nota");
        }
    }

    [Test]
    public void Sustain_ReleaseGapShorterThanDropLeniency_KeepsTheSustain()
    {
        // Soltar e reapertar em 15 ms (tolerância padrão: 25 ms) não deve derrubar o sustain.
        string chart = ChartText.Build(120, [new(4, "G", LengthBeats: 4)]);
        double t = Sec(4);
        var blip = new Rig(chart).Play(new Inputs().Press(t - 0.02, G).Strum(t)
            .Release(Sec(6), G).Press(Sec(6) + 0.015, G).Release(Sec(8) + 0.05, G).Build(), 240);
        var full = new Rig(chart).Play(new Inputs().Press(t - 0.02, G).Strum(t).Release(Sec(8) + 0.05, G).Build(), 240);

        Assert.That(blip.Stats.SustainScore, Is.EqualTo(full.Stats.SustainScore),
            $"blip: {blip.Summary()} sustainScore={blip.Stats.SustainScore} | inteiro: {full.Summary()} sustainScore={full.Stats.SustainScore}");
    }

    [TestCase(0.035)]
    [TestCase(0.100)]
    public void Sustain_ReleaseGapLongerThanDropLeniency_DropsTheSustain(double gap)
    {
        string chart = ChartText.Build(120, [new(4, "G", LengthBeats: 4)]);
        double t = Sec(4);
        var dropped = new Rig(chart).Play(new Inputs().Press(t - 0.02, G).Strum(t)
            .Release(Sec(6), G).Press(Sec(6) + gap, G).Release(Sec(8) + 0.05, G).Build(), 240);
        var full = new Rig(chart).Play(new Inputs().Press(t - 0.02, G).Strum(t).Release(Sec(8) + 0.05, G).Build(), 240);

        Assert.That(dropped.Stats.SustainScore, Is.LessThan(full.Stats.SustainScore), dropped.Summary());
    }

    [Test]
    public void StarPower_TwoCompletePhrases_EnableActivation()
    {
        var rig = new Rig(ChartText.Build(120,
            [new(4, "G"), new(5, "R"), new(8, "Y"), new(9, "B"), new(12, "G"), new(13, "R")],
            starPower: [(4, 1.1), (8, 1.1)]));
        var inputs = PlayerSim.Play(rig.Chart).ToList();
        var sp = new Inputs().StarPower(Sec(10)).Build();
        rig.Play(inputs.Concat(sp).OrderBy(i => i.Time).ToList(), 240);

        using (Assert.EnterMultipleScope())
        {
            Assert.That(rig.Stats.StarPowerPhrasesHit, Is.EqualTo(2));
            Assert.That(rig.Stats.StarPowerActivationCount, Is.EqualTo(1), "ativou com 50% da barra");
        }
    }

    [Test]
    public void StarPower_MissingANoteInThePhrase_GivesNothing()
    {
        var rig = new Rig(ChartText.Build(120, [new(4, "G"), new(5, "R")], starPower: [(4, 1.1)]));
        // Só toca a primeira nota da frase.
        var inputs = new Inputs().Press(Sec(4) - 0.02, G).Strum(Sec(4)).Release(Sec(4) + 0.2, G).Build();
        rig.Play(inputs, 240);

        using (Assert.EnterMultipleScope())
        {
            Assert.That(rig.Stats.StarPowerPhrasesHit, Is.Zero);
            Assert.That(rig.Stats.StarPowerTickAmount, Is.Zero);
        }
    }

    [Test]
    public void Overstrum_FarFromNotes_BreaksTheCombo()
    {
        var rig = new Rig(ChartText.Build(120, [new(4, "G"), new(8, "R")]));
        var inputs = new Inputs().Press(Sec(4) - 0.02, G).Strum(Sec(4)).Release(Sec(4) + 0.1, G)
            .Strum(Sec(6))                                   // palhetada no vazio
            .Press(Sec(8) - 0.02, R).Strum(Sec(8)).Release(Sec(8) + 0.1, R).Build();
        rig.Play(inputs, 240);

        using (Assert.EnterMultipleScope())
        {
            Assert.That(rig.Stats.Overstrums, Is.EqualTo(1));
            Assert.That(rig.Stats.NotesHit, Is.EqualTo(2));
            Assert.That(rig.Stats.MaxCombo, Is.EqualTo(1), "o combo recomeça depois do overstrum");
        }
    }

    /// <summary>
    /// Documenta o comportamento de input atrasado: se um evento chega à engine com timestamp
    /// anterior ao último Update, ela o empurra para o tempo atual (aviso "forced to move an input time").
    /// No jogo isso só acontece se o evento do dispositivo for entregue depois do frame em que ocorreu.
    /// </summary>
    [Test]
    public void LateDeliveredInput_IsMovedToTheCurrentTime()
    {
        var rig = new Rig(ChartText.Build(120, [new(4, "G")]));
        double t = Sec(4);
        var hold = GameInput.Create(1.0, G, true);
        rig.Engine.QueueInput(ref hold);
        rig.Engine.Update(t + 0.060);                      // a engine já chegou a +60 ms
        var strum = GameInput.Create(t + 0.050, GuitarAction.StrumDown, true); // palhetada em +50 ms, entregue atrasada
        rig.Engine.QueueInput(ref strum);
        rig.Engine.Update(t + 0.065);
        rig.Engine.Update(t + 1.0);

        TestContext.Out.WriteLine($"acerto registrado em t={rig.Hits.Single().Time - t:+0.000;-0.000} s (evento em +0.050 s)");
        Assert.That(rig.Hits.Single().Time, Is.GreaterThanOrEqualTo(t + 0.060), "o evento atrasado é julgado no tempo em que chegou");
    }

    // ------------------------------------------------------------------ problemas conhecidos

    /// <summary>
    /// Suspeita #7 (confirmada no código): no overstrum, os pontos do sustain em andamento entram em
    /// CommittedScore sem multiplicador e sem somar em SustainScore; no fim normal do sustain eles passam
    /// por AddScore (com multiplicador). Este teste afirma o comportamento consistente e hoje FALHA.
    /// </summary>
    [Test, Explicit("Problema conhecido do upstream (GuitarEngine.Overstrum)"), Category("KnownIssue")]
    public void KnownIssue_SustainPointsLostToOverstrum_UseTheMultiplier()
    {
        // 30 notas para chegar a 4x, depois um sustain longo interrompido por overstrum.
        var notes = Enumerable.Range(0, 30).Select(i => new ChartNote(4 + i * 0.5, i % 2 == 0 ? "G" : "R")).ToList();
        notes.Add(new ChartNote(20, "Y", LengthBeats: 8));
        string chart = ChartText.Build(120, notes);

        Rig Run(bool overstrum)
        {
            var rig = new Rig(chart);
            var inputs = PlayerSim.Play(rig.Chart).Where(i => i.Time < Sec(20) - 0.1).ToList();
            var tail = new Inputs().Press(Sec(20) - 0.02, Y).Strum(Sec(20));
            if (overstrum) tail.Strum(Sec(24));              // overstrum no meio do sustain
            else tail.Release(Sec(24), Y);                     // soltar no mesmo ponto
            tail.Release(Sec(29), Y);
            rig.Play(inputs.Concat(tail.Build()).OrderBy(i => i.Time).ToList(), 240);
            return rig;
        }

        var released = Run(overstrum: false);
        var overstrummed = Run(overstrum: true);
        TestContext.Out.WriteLine($"soltou: {released.Summary()} sustain={released.Stats.SustainScore}");
        TestContext.Out.WriteLine($"overstrum: {overstrummed.Summary()} sustain={overstrummed.Stats.SustainScore}");
        Assert.That(overstrummed.Stats.SustainScore, Is.EqualTo(released.Stats.SustainScore));
    }

    /// <summary>
    /// Suspeita #8 (confirmada no código): FiveFretGuitarPreset.Copy() não copia SustainDropLeniency,
    /// então "Copy of ..." no menu de presets volta esse valor ao padrão. Hoje FALHA.
    /// </summary>
    [Test, Explicit("Problema conhecido do upstream (EnginePreset.Instruments.cs)"), Category("KnownIssue")]
    public void KnownIssue_PresetCopy_KeepsSustainDropLeniency()
    {
        var preset = EnginePreset.Default.FiveFretGuitar.Copy();
        preset.SustainDropLeniency = 0.045;
        Assert.That(preset.Copy().SustainDropLeniency, Is.EqualTo(0.045));
    }
}
