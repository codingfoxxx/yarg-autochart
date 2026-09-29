import unittest

import numpy as np

from autochart.tempomap import TempoEvent, TempoMap, TimeSignature, build_tempo_map


class TempoMapConversions(unittest.TestCase):
    def test_tick_time_roundtrip_across_tempo_changes(self):
        tm = TempoMap([TempoEvent(0, 120000), TempoEvent(768, 90000)], [TimeSignature(0, 4)])
        self.assertAlmostEqual(tm.tick_to_time(768), 2.0)             # 4 batidas a 120 BPM
        self.assertAlmostEqual(tm.tick_to_time(768 + 192), 2.0 + 60 / 90)
        for tick in (0, 100, 768, 900, 5000):
            self.assertAlmostEqual(tm.time_to_tick(tm.tick_to_time(tick)), tick, places=6)

    def test_rejects_invalid_maps(self):
        with self.assertRaises(ValueError):
            TempoMap([TempoEvent(10, 120000)], [TimeSignature(0, 4)])
        with self.assertRaises(ValueError):
            TempoMap([TempoEvent(0, 0)], [TimeSignature(0, 4)])


class BuildFromBeats(unittest.TestCase):
    def test_steady_tempo_with_detector_noise_gives_single_bpm(self):
        rng = np.random.default_rng(1)
        beats = 1.5 + np.arange(300) * (60 / 124) + rng.normal(0, 0.007, 300)  # ruído de 7 ms
        downbeats = beats[::4]
        tm, rep = build_tempo_map(beats, downbeats)
        self.assertEqual(rep.tempo_changes, 1)  # só o evento do lead-in
        self.assertAlmostEqual(tm.tempos[-1].bpm, 124.0, delta=0.05)
        self.assertLess(rep.median_error_ms, 8.0)

    def test_real_tempo_drift_is_followed(self):
        ibi = np.linspace(60 / 165, 60 / 176, 400)  # acelera 165 → 176 BPM
        beats = 1.5 + np.concatenate([[0], np.cumsum(ibi[:-1])])
        tm, rep = build_tempo_map(beats, beats[::4])
        self.assertGreater(rep.tempo_changes, 1)
        self.assertLess(rep.p95_error_ms, 12.0)

    def test_pickup_measure_keeps_downbeats_on_bar_lines(self):
        beats = 1.5 + np.arange(64) * 0.5
        downbeats = beats[3::4]  # primeiro tempo forte na 4ª batida detectada
        tm, rep = build_tempo_map(beats, downbeats)
        k0 = rep.lead_in_beats
        first_downbeat_tick = (k0 + 3) * tm.resolution
        self.assertIn(first_downbeat_tick, tm.measure_starts(first_downbeat_tick + 1))
        ticks = [s.tick for s in tm.timesigs]
        self.assertEqual(len(ticks), len(set(ticks)), "no máximo uma fórmula por tick")

    def test_waltz_detected_as_three_four(self):
        beats = 1.5 + np.arange(90) * (60 / 175)
        tm, _ = build_tempo_map(beats, beats[1::3])
        self.assertEqual(tm.timesigs[-1].numerator, 3)


if __name__ == "__main__":
    unittest.main()
