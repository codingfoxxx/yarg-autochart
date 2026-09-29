import unittest

from autochart.chart import final_types, hopo_threshold, natural_hopo, render_chart, render_song_ini, validate_notes
from autochart.model import Note, SongMeta
from autochart.tempomap import TempoEvent, TempoMap, TimeSignature


def tempo120() -> TempoMap:
    return TempoMap([TempoEvent(0, 120000)], [TimeSignature(0, 4)])


class HopoRule(unittest.TestCase):
    """Mesma regra do YARG (MoonNote.cs) para .chart em resolução 192."""

    def test_threshold_matches_yarg_formula(self):
        self.assertEqual(hopo_threshold(192), 65)
        self.assertEqual(hopo_threshold(480), 162)

    def test_natural_hopo_cases(self):
        thr = 65
        g = Note(0, (0,))
        self.assertTrue(natural_hopo(g, Note(48, (1,)), thr))          # semicolcheia, traste diferente
        self.assertTrue(natural_hopo(g, Note(65, (1,)), thr))          # exatamente no limiar (inclusivo)
        self.assertFalse(natural_hopo(g, Note(66, (1,)), thr))
        self.assertFalse(natural_hopo(g, Note(48, (0,)), thr))         # mesmo traste
        self.assertFalse(natural_hopo(g, Note(48, (1, 2)), thr))       # acorde nunca é HOPO natural
        self.assertTrue(natural_hopo(Note(0, (0, 1)), Note(48, (0,)), thr))  # depois de acorde, mesmo traste
        self.assertFalse(natural_hopo(None, Note(0, (1,)), thr))

    def test_intent_is_honored_through_flips(self):
        notes = [Note(0, (0,)), Note(48, (1,), hopo=False), Note(240, (2,), hopo=True), Note(288, (3,))]
        self.assertEqual(final_types(notes), ["strum", "strum", "hopo", "hopo"])
        text = render_chart(SongMeta("t"), tempo120(), {"Expert": notes})
        self.assertIn("48 = N 5 0", text)    # HOPO natural virou palhetada
        self.assertIn("240 = N 5 0", text)   # palhetada natural virou HOPO
        self.assertNotIn("288 = N 5 0", text)  # HOPO natural sem inversão


class ChartFormat(unittest.TestCase):
    def test_song_then_synctrack_first_and_sorted(self):
        notes = [Note(0, (0,)), Note(192, (1, 2), length=96)]
        text = render_chart(SongMeta("Título \"x\""), tempo120(), {"Expert": notes, "Easy": [Note(0, (0,))]},
                            star_power=[(0, 193)], sections=[(0, "Intro")])
        lines = [l.strip() for l in text.splitlines()]
        self.assertEqual(lines[0], "[Song]")
        self.assertEqual(lines.index("[SyncTrack]"), lines.index("}") + 1)
        self.assertIn("Resolution = 192", lines)
        self.assertIn('Name = "Título \'x\'"', lines)
        self.assertIn("192 = N 1 96", lines)
        self.assertIn("192 = N 2 96", lines)
        self.assertIn("0 = S 2 193", lines)
        start = lines.index("[ExpertSingle]") + 2
        body = lines[start:lines.index("}", start)]
        ticks = [int(l.split(" = ")[0]) for l in body if " = " in l]
        self.assertEqual(ticks, sorted(ticks))

    def test_song_ini(self):
        ini = render_song_ini(SongMeta("Nome", artist="Artista", song_length_ms=1000))
        self.assertTrue(ini.startswith("[song]\r\n"))
        self.assertIn("name = Nome", ini)
        self.assertIn("song_length = 1000", ini)

    def test_validation_catches_format_problems(self):
        bad = [Note(10, (0,), length=200), Note(100, (1,)), Note(100, (2,)), Note(300, (5,))]
        problems = " | ".join(validate_notes(bad))
        self.assertIn("atravessa", problems)
        self.assertIn("não é maior", problems)
        self.assertIn("inválidos", problems)


if __name__ == "__main__":
    unittest.main()
