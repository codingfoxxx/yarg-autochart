"""Frases de star power: ~1 a cada 40 tempos, ~1 compasso cada, em trechos marcantes.

Regras (RBN "Overdrive"): espaçadas, sem sobreposição, nenhuma nos ~8 compassos finais, as
mesmas janelas em todas as dificuldades e com pelo menos uma nota em cada uma.
"""
from __future__ import annotations

import bisect

from .model import Note
from .tempomap import TempoMap


def place_star_power(diffs: dict[str, list[Note]], tempo: TempoMap, *, every_beats: float = 40.0,
                     min_expert_notes: int = 3, section_ticks: list[int] | None = None,
                     tail_measures: int = 8) -> list[tuple[int, int]]:
    expert = diffs.get("Expert") or next((v for v in diffs.values() if v), [])
    if len(expert) < min_expert_notes:
        return []
    res = tempo.resolution
    first_tick = expert[0].tick
    end_tick = max(n.tick + n.length for n in expert)
    starts = tempo.measure_starts(end_tick + 8 * res)
    measures = [(a, b) for a, b in zip(starts, starts[1:]) if b > first_tick]
    usable = measures[:-tail_measures] if len(measures) > tail_measures + 2 else measures[:-1]
    if not usable:
        return []

    tick_lists = {d: [n.tick for n in v] for d, v in diffs.items() if v}
    sections = set(section_ticks or [])

    def count(d: str, a: int, b: int) -> int:
        ticks = tick_lists[d]
        return bisect.bisect_left(ticks, b) - bisect.bisect_left(ticks, a)

    candidates = []
    for mi, (a, b) in enumerate(usable):
        counts = {d: count(d, a, b) for d in tick_lists}
        if any(c == 0 for c in counts.values()) or counts.get("Expert", min_expert_notes) < min_expert_notes:
            continue
        exp_notes = [n for n in expert if a <= n.tick < b]
        score = len(exp_notes) + 3.0 * any(n.length > 0 for n in exp_notes) + 4.0 * (a in sections)
        candidates.append((mi, a, b, score))
    if not candidates:
        return []

    total_beats = (usable[-1][1] - first_tick) / res
    target = max(2, round(total_beats / every_beats))
    span = (usable[-1][1] - first_tick) / target
    chosen: list[tuple[int, int]] = []
    last_mi = -10
    for k in range(target):
        lo, hi = first_tick + k * span, first_tick + (k + 1) * span
        slot = [c for c in candidates if lo <= c[1] < hi and c[0] - last_mi >= 3]
        if not slot:
            continue
        mi, a, b, _ = max(slot, key=lambda c: (c[3], -c[1]))
        notes_in = [n for v in diffs.values() for n in v if a <= n.tick < b]
        start = min(n.tick for n in notes_in)
        last = max(n.tick for n in notes_in)
        chosen.append((start, last - start + 1))  # fim exclusivo: cobre o tick da última nota
        last_mi = mi
    return chosen
