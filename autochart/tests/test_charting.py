"""Quantização, trastes, dificuldades e star power com dados sintéticos (sem modelos)."""
import unittest

import numpy as np

from autochart.chart import final_types
from autochart.difficulty import PROFILES, build_difficulties, min_gap
from autochart.lanes import LaneParams, assign_lanes, enforce_repeats
from autochart.model import Event
from autochart.quantize import quantize, rhythm_profile
from autochart.report import playability_violations
from autochart.starpower import place_star_power
from autochart.tempomap import TempoEvent, TempoMap, TimeSignature


def tempo(bpm=120.0) -> TempoMap:
    return TempoMap([TempoEvent(0, int(bpm * 1000))], [TimeSignature(0, 4)])


class Rhythm(unittest.TestCase):
    def test_straight_eighths_with_human_jitter_do_not_become_triplets(self):
        rng = np.random.default_rng(3)
        pos = np.arange(0, 200, 0.5) + rng.normal(0, 0.06, 400)  # ±30 ms a 120 BPM
        prof = rhythm_profile(pos, np.ones_like(pos), np.full(len(pos), 0.5))
        self.assertEqual(prof.allowed, (1, 2))

    def test_real_triplets_are_detected(self):
        rng = np.random.default_rng(4)
        pos = np.arange(0, 100, 1 / 3) + rng.normal(0, 0.01, 300)
        prof = rhythm_profile(pos, np.ones_like(pos), np.full(len(pos), 0.5))
        self.assertIn(3, prof.allowed)

    def test_quantize_snaps_and_merges(self):
        tm = tempo(120)
        events = [Event(1.0 + 0.012, 1.0), Event(1.25 - 0.01, 0.8), Event(1.26, 0.5)]  # último cai no mesmo tick
        q, _ = quantize(events, tm)
        self.assertEqual([x.tick for x in q], [384, 480])
        self.assertAlmostEqual(q[0].error_ms, -12.0, delta=0.5)


class Lanes(unittest.TestCase):
    def test_rising_melody_moves_right_and_repeats_stay(self):
        pitches = [50, 52, 55, 57, 59, 59, 57, 55]
        times = [i * 0.3 for i in range(8)]
        lanes = assign_lanes(pitches, times, [1] * 8, LaneParams())
        flat = [l[0] for l in lanes]
        self.assertEqual(flat, sorted(flat[:5]) + flat[5:])        # sobe nas 5 primeiras
        self.assertEqual(flat[4], flat[5])                          # nota repetida, mesmo traste
        self.assertGreater(flat[4], flat[7])                        # desce no fim

    def test_chords_fit_inside_available_lanes(self):
        lanes = assign_lanes([40, 45, 50], [0, 0.5, 1.0], [2, 3, 2], LaneParams(n_lanes=4, max_chord=2))
        for l in lanes:
            self.assertLessEqual(len(l), 2)
            self.assertTrue(all(0 <= x < 4 for x in l))

    def test_repeated_riffs_get_identical_shapes(self):
        ticks = [0, 192, 384, 576, 768, 960, 1152, 1344]
        pitches = [50, 53, 55, 53, 50, 53, 55, 53]
        lanes = [(0,), (1,), (2,), (1,), (1,), (2,), (4,), (2,)]
        out, consistency = enforce_repeats(ticks, lanes, pitches, [1] * 8, [0, 768, 1536])
        self.assertEqual(out[:4], out[4:])
        self.assertLess(consistency, 1.0)


class Difficulties(unittest.TestCase):
    def _song(self):
        rng = np.random.default_rng(7)
        tm = tempo(140)
        spb = 60 / 140
        events = []
        for k in range(400):  # colcheias com semicolcheias ocasionais, alturas em contorno
            t = 8 * spb + k * spb / 2 + (spb / 4 if k % 7 == 3 else 0)  # começa na batida 8
            ev = Event(t, float(rng.uniform(0.3, 1.5)), pitch=float(50 + 7 * np.sin(k / 5)),
                       polyphony=2 if k % 9 == 0 else 1, duration=0.6 if k % 11 == 0 else 0.1)
            events.append(ev)
        q, _ = quantize(events, tm)
        return tm, build_difficulties(q, tm)[0]

    def test_subset_monotonic_and_rules(self):
        tm, diffs = self._song()
        order = ["Easy", "Medium", "Hard", "Expert"]
        for low, high in zip(order, order[1:]):
            self.assertLessEqual({n.tick for n in diffs[low]}, {n.tick for n in diffs[high]})
            self.assertLess(len(diffs[low]), len(diffs[high]))
        sp = place_star_power(diffs, tm)
        self.assertGreaterEqual(len(sp), 2)
        for name, notes in diffs.items():
            self.assertEqual(playability_violations(name, notes, tm, sp), [], name)
        self.assertTrue(all(len(n.lanes) == 1 and n.lanes[0] < 3 for n in diffs["Easy"]))
        self.assertTrue(all(t == "strum" for t in final_types(diffs["Medium"])))

    def test_min_gap_uses_local_tempo(self):
        tm = TempoMap([TempoEvent(0, 120000), TempoEvent(1920, 60000)], [TimeSignature(0, 4)])
        self.assertAlmostEqual(min_gap(PROFILES["Hard"], tm, 0), 0.25)
        self.assertAlmostEqual(min_gap(PROFILES["Hard"], tm, 3000), 0.5)


if __name__ == "__main__":
    unittest.main()
