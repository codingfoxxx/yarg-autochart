using NUnit.Framework;
using YARG.Menu.Calibrator;

namespace GuitarHero.EngineTests;

/// <summary>
/// Cálculo da calibração guiada do fork (YARG/Assets/Script/Menu/Calibrator/CalibrationMath.cs,
/// compilado aqui como link). A música de calibração do YARG tem 80 BPM e 15 s.
/// </summary>
public class CalibrationMathTests
{
    private const double Spb = 60.0 / 80.0;

    private static List<double> Taps(double delay, int beats = 20, double sigma = 0, int seed = 1, params int[] missed)
    {
        var rnd = new Random(seed);
        var taps = new List<double>();
        for (int b = 0; b < beats; b++)
        {
            if (missed.Contains(b)) continue;
            double noise = sigma * Math.Sqrt(-2 * Math.Log(1 - rnd.NextDouble())) * Math.Cos(2 * Math.PI * rnd.NextDouble());
            taps.Add(b * Spb + delay + noise);
        }
        return taps;
    }

    /// <summary>Filtro do calibrador original: descarta o toque que não estiver 1 batida depois do anterior.</summary>
    private static List<double> UpstreamFilter(List<double> times)
    {
        var t = new List<double>(times);
        for (int i = t.Count - 1; i > 1; i--)
        {
            if (Math.Abs(t[i] - (t[i - 1] + Spb)) > 0.05)
                t.RemoveAt(i);
        }
        return t;
    }

    [Test]
    public void SteadyTaps_GiveTheirDelay()
    {
        Assert.That(CalibrationMath.TryCalculate(Taps(0.040), Spb, out var r), Is.True);
        using (Assert.EnterMultipleScope())
        {
            Assert.That(r.Delay, Is.EqualTo(0.040).Within(1e-9));
            Assert.That(r.Used, Is.EqualTo(20));
            Assert.That(r.Discarded, Is.Zero);
            Assert.That(r.Consistency, Is.EqualTo(CalibrationMath.Consistency.Good));
        }
    }

    /// <summary>
    /// 400 jogadores simulados com erro humano de 15 ms: uma passada da música (20 batidas, como no
    /// original) contra duas passadas (40 batidas, como no fork). Mede o quanto o resultado erra.
    /// </summary>
    [Test]
    public void TwoPasses_AreMoreAccurateThanOne()
    {
        double Percentile95(int beats)
        {
            var errors = new List<double>();
            for (int seed = 1; seed <= 400; seed++)
            {
                Assert.That(CalibrationMath.TryCalculate(Taps(0.030, beats, sigma: 0.015, seed: seed), Spb, out var r), Is.True);
                errors.Add(Math.Abs(r.Delay - 0.030));
            }
            errors.Sort();
            return errors[(int) (0.95 * errors.Count)];
        }

        double one = Percentile95(20), two = Percentile95(40);
        TestContext.Out.WriteLine($"erro do resultado (95% dos jogadores): 1 passada {one * 1000:0.0} ms, 2 passadas {two * 1000:0.0} ms");
        using (Assert.EnterMultipleScope())
        {
            Assert.That(two, Is.LessThan(one * 0.85), "dobrar os toques reduz o erro em ~1/raiz(2)");
            Assert.That(two, Is.LessThan(0.0075));
        }
    }

    [Test]
    public void MissedBeats_DoNotDiscardTheNextGoodTap()
    {
        var taps = Taps(0.025, sigma: 0.005, missed: [5, 12]);
        Assert.That(CalibrationMath.TryCalculate(taps, Spb, out var r), Is.True);
        using (Assert.EnterMultipleScope())
        {
            Assert.That(r.Used, Is.EqualTo(18), "todos os 18 toques são bons");
            Assert.That(UpstreamFilter(taps), Has.Count.EqualTo(16), "o filtro original perdia o toque depois de cada falha");
        }
    }

    [Test]
    public void StrayPresses_AreDiscarded()
    {
        var taps = Taps(0.020, sigma: 0.006);
        taps.Add(7 * Spb + 0.200);  // toque duplo atrasado
        taps.Add(11 * Spb - 0.150); // toque adiantado
        taps.Sort();
        Assert.That(CalibrationMath.TryCalculate(taps, Spb, out var r), Is.True);
        using (Assert.EnterMultipleScope())
        {
            Assert.That(r.Discarded, Is.EqualTo(2));
            Assert.That(r.Delay, Is.EqualTo(0.020).Within(0.004));
        }
    }

    [Test]
    public void TooFewTaps_IsRejected()
    {
        Assert.That(CalibrationMath.TryCalculate(Taps(0.02, beats: 8), Spb, out _), Is.False);
        Assert.That(CalibrationMath.TryCalculate(Taps(0.02, beats: 9), Spb, out _), Is.True);
        Assert.That(CalibrationMath.TryCalculate([], Spb, out _), Is.False);
    }

    [Test]
    public void ErraticTaps_AreReportedAsPoor()
    {
        Assert.That(CalibrationMath.TryCalculate(Taps(0.03, sigma: 0.045, seed: 3), Spb, out var r), Is.True);
        Assert.That(r.Consistency, Is.EqualTo(CalibrationMath.Consistency.Poor), $"dispersão {r.Spread * 1000:0} ms");
    }

    [Test]
    public void DelayNearHalfABeat_IsRejectedAsUnreliable()
    {
        // 375 ms = meia batida a 80 BPM: com ruído, metade dos toques "dobra" para a batida seguinte
        Assert.That(CalibrationMath.TryCalculate(Taps(0.375, beats: 40, sigma: 0.012, seed: 5), Spb, out var r), Is.True);
        TestContext.Out.WriteLine($"usados {r.Used}, descartados {r.Discarded}");
        Assert.That(r.IsReliable, Is.False);
    }

    [Test]
    public void OrdinaryTapping_IsReliable()
    {
        // 200 jogadores com erro de 20 ms e atrasos de 0 a 250 ms: nenhum resultado recusado
        for (int seed = 1; seed <= 200; seed++)
        {
            double delay = (seed % 26) * 0.010;
            Assert.That(CalibrationMath.TryCalculate(Taps(delay, beats: 40, sigma: 0.020, seed: seed), Spb, out var r), Is.True);
            Assert.That(r.IsReliable, Is.True, $"atraso {delay * 1000:0} ms, usados {r.Used}, descartados {r.Discarded}");
        }
    }

    [Test]
    public void StrayPresses_UpToAQuarter_AreStillReliable()
    {
        var taps = Taps(0.040, beats: 40, sigma: 0.010, seed: 7);
        for (int i = 0; i < 10; i++) taps.Add((3 + 3 * i) * Spb + 0.25); // 10 toques soltos em 50
        taps.Sort();
        Assert.That(CalibrationMath.TryCalculate(taps, Spb, out var r), Is.True);
        Assert.That(r.IsReliable, Is.True, $"usados {r.Used}, descartados {r.Discarded}");
        Assert.That(r.Delay, Is.EqualTo(0.040).Within(0.005));
    }

    [TestCase(25, 10, 15)]
    [TestCase(-5, 20, -25)]
    [TestCase(40, 40, 0)]
    public void ProfileAlternative_MovesOnlyTheDifference(int global, int currentAudio, long expected)
    {
        // Salvar no perfil = mesma compensação total que salvar global, mantendo a calibração de áudio atual.
        Assert.That(CalibrationMath.ProfileInputCalibration(global, currentAudio), Is.EqualTo(expected));
        Assert.That(currentAudio + CalibrationMath.ProfileInputCalibration(global, currentAudio), Is.EqualTo(global));
    }
}
