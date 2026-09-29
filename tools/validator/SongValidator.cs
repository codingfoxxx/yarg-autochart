using System.Text;
using System.Text.Json;
using GuitarHero.EngineTests;
using YARG.Core;
using YARG.Core.Chart;
using YARG.Core.Song;
using YARG.Core.Song.Cache;

namespace GuitarHero.Validator;

/// <summary>
/// Valida pastas de música com o YARG.Core: scanner da biblioteca (como "Refresh All Caches"),
/// leitura do chart pelo parser do jogo e partida simulada na engine de 5 trastes.
/// </summary>
public static class SongValidator
{
    private static readonly Difficulty[] Diffs = [Difficulty.Easy, Difficulty.Medium, Difficulty.Hard, Difficulty.Expert];
    private static readonly (string Name, double Sigma)[] Players = [("perfeito", 0.0), ("humano_20ms", 0.020), ("humano_35ms", 0.035)];

    /// <param name="folder">Biblioteca (varre tudo) ou pasta de uma música (com song.ini).</param>
    /// <returns>(ok, texto legível); ok = nenhuma rejeição e jogador perfeito com 100% em tudo.</returns>
    public static (bool Ok, string Text) Run(string folder, string? jsonOut)
    {
        var log = new StringBuilder();
        string target = Path.GetFullPath(folder).TrimEnd('\\', '/');
        if (!Directory.Exists(target))
        {
            return (false, $"pasta não encontrada: {target}");
        }
        bool single = File.Exists(Path.Combine(target, "song.ini"));
        string root = single ? Path.GetDirectoryName(target)! : target;

        string tmp = Path.Combine(Path.GetTempPath(), "yarg-validar-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(tmp);
        string badPath = Path.Combine(tmp, "badsongs.txt");
        var cache = CacheHandler.RunScan(false, Path.Combine(tmp, "songcache.bin"), badPath, false, [root]);
        var entries = cache.Entries.Values.SelectMany(v => v)
            .Where(e => !single || Path.GetFullPath(e.ActualLocation).TrimEnd('\\', '/').Equals(target, StringComparison.OrdinalIgnoreCase))
            .OrderBy(e => e.ActualLocation)
            .ToList();
        string bad = File.Exists(badPath) ? File.ReadAllText(badPath) : "";
        if (single)
        {
            bad = string.Join("\n", bad.Split('\n').Where(l => l.Contains(target, StringComparison.OrdinalIgnoreCase)));
        }

        bool ok = true;
        var report = new List<object>();
        foreach (var entry in entries)
        {
            var part = entry[Instrument.FiveFretGuitar];
            var available = Diffs.Where(d => part[d]).ToList();
            log.AppendLine($"{entry.Artist} - {entry.Name}");
            log.AppendLine($"  dificuldades detectadas pelo scanner do YARG: {string.Join(", ", available)}");
            var perDiff = new Dictionary<string, object>();
            foreach (var d in available)
            {
                var chart = entry.LoadChart();
                if (chart is null)
                {
                    log.AppendLine("  ERRO: o YARG não conseguiu carregar o chart");
                    ok = false;
                    break;
                }
                var notes = chart.FiveFretGuitar.GetDifficulty(d);
                var types = new StringBuilder(notes.Notes.Count);
                int chords = 0, sustains = 0;
                foreach (var n in notes.Notes)
                {
                    types.Append(n.Type switch { GuitarNoteType.Hopo => 'H', GuitarNoteType.Tap => 'T', _ => 'S' });
                    if (n.ChildNotes.Count > 0) chords++;
                    if (n.IsSustain) sustains++;
                }
                int starPower = notes.Phrases.Count(p => p.Type == PhraseType.StarPower);

                var sims = new Dictionary<string, object>();
                var line = new StringBuilder();
                foreach (var (name, sigma) in Players)
                {
                    var fresh = entry.LoadChart()!;
                    var rig = new Rig((fresh.FiveFretGuitar.GetDifficulty(d), fresh.SyncTrack));
                    var inputs = PlayerSim.Play(rig.Chart, sigma > 0 ? PlayerSim.Gaussian(sigma, seed: 42) : null);
                    rig.Play(inputs, fps: 60);
                    double pct = rig.Stats.TotalNotes > 0 ? 100.0 * rig.Stats.NotesHit / rig.Stats.TotalNotes : 0;
                    sims[name] = new
                    {
                        acertos_pct = Math.Round(pct, 1),
                        overstrums = rig.Stats.Overstrums,
                        combo_max = rig.Stats.MaxCombo,
                        pontos = rig.Stats.TotalScore,
                        estrelas = Math.Round(rig.Stats.Stars, 2),
                    };
                    line.Append($"  {name} {pct:0.0}%");
                    if (name == "perfeito" && rig.Stats.NotesHit != rig.Stats.TotalNotes)
                    {
                        ok = false;
                        log.AppendLine($"  ERRO: jogador perfeito não acertou tudo em {d}: {rig.Summary()}");
                    }
                }
                string t = types.ToString();
                log.AppendLine($"  {d,-6} notas {notes.Notes.Count,4} | acordes {chords,4} | sustains {sustains,4} | " +
                               $"HOPO {t.Count(c => c == 'H'),4} | tap {t.Count(c => c == 'T'),3} | SP {starPower,2} |{line}");
                perDiff[d.ToString()] = new { notas = notes.Notes.Count, acordes = chords, sustains, star_power = starPower, tipos = t, simulacao = sims };
            }
            report.Add(new { pasta = entry.ActualLocation, nome = entry.Name.ToString(), artista = entry.Artist.ToString(),
                             dificuldades = available.Select(d => d.ToString()).ToList(), por_dificuldade = perDiff });
        }
        if (!string.IsNullOrWhiteSpace(bad))
        {
            ok = false;
            log.AppendLine("REJEITADAS pelo scanner (badsongs.txt):");
            log.AppendLine(bad.Trim());
        }
        if (entries.Count == 0)
        {
            ok = false;
            log.AppendLine("Nenhuma música encontrada pelo scanner do YARG.Core.");
        }
        if (jsonOut is not null)
        {
            var doc = new { ok, musicas = report, rejeitadas = bad.Trim() };
            File.WriteAllText(jsonOut, JsonSerializer.Serialize(doc, new JsonSerializerOptions { WriteIndented = true }));
        }
        try { Directory.Delete(tmp, true); } catch (IOException) { }
        log.AppendLine(ok ? "RESULTADO: OK" : "RESULTADO: FALHOU");
        return (ok, log.ToString());
    }
}
