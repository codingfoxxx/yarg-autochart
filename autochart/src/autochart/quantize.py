"""Quantização: cada ataque detectado vai para um tick do grid.

Escolhe, para cada evento, a subdivisão mais simples que explique bem o tempo dele
(semínima < colcheia < semicolcheia < fusa), com tercinas preferidas nos compassos que soam
"em swing". O erro (ms) entre o ataque real e o tick escolhido vira métrica de qualidade.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .model import Event
from .tempomap import TempoMap

# Custo extra (ms) por complexidade de subdivisão: (compasso reto, compasso em tercina)
_PENALTY = {1: (0.0, 0.0), 2: (1.0, 6.0), 4: (3.0, 12.0), 8: (14.0, 22.0), 3: (9.0, 1.0), 6: (16.0, 4.0)}


@dataclass
class Quantized:
    tick: int
    event: Event
    subdivision: int
    error_ms: float  # tempo do tick − tempo do ataque


def _measure_index(starts: list[int], tick: float) -> int:
    return max(0, int(np.searchsorted(starts, tick, side="right")) - 1)


def quantize(events: list[Event], tempo: TempoMap, *, allow_32nds: bool = False) -> list[Quantized]:
    if not events:
        return []
    res = tempo.resolution
    positions = [tempo.time_to_tick(e.time) / res for e in events]  # em batidas
    end_tick = int(max(positions) * res) + 4 * res
    starts = tempo.measure_starts(end_tick)

    # 1) Detecta compassos "em tercina": ataques fora da batida explicados melhor por tercinas.
    straight_err: dict[int, float] = {}
    triplet_err: dict[int, float] = {}
    offbeats: dict[int, int] = {}
    for e, p in zip(events, positions):
        frac = p - np.floor(p)
        if min(frac, 1 - frac) < 0.08:  # em cima da batida: não informa
            continue
        m = _measure_index(starts, p * res)
        es = abs(p * 4 - round(p * 4)) / 4
        et = abs(p * 3 - round(p * 3)) / 3
        straight_err[m] = straight_err.get(m, 0.0) + es * e.strength
        triplet_err[m] = triplet_err.get(m, 0.0) + et * e.strength
        offbeats[m] = offbeats.get(m, 0) + 1
    triplet_measures = {m for m in offbeats
                        if offbeats[m] >= 2 and triplet_err[m] < 0.6 * straight_err[m]}

    # 2) Escolhe a subdivisão de menor custo para cada evento.
    subdivisions = [1, 2, 4, 3, 6] + ([8] if allow_32nds else [])
    out: list[Quantized] = []
    for e, p in zip(events, positions):
        tick_f = p * res
        m = _measure_index(starts, tick_f)
        swing = m in triplet_measures
        spb = tempo.seconds_per_beat_at(tick_f)
        best = None
        for s in subdivisions:
            grid = round(p * s) / s
            err_ms = abs(p - grid) * spb * 1000.0
            cost = err_ms + _PENALTY[s][1 if swing else 0]
            if best is None or cost < best[0]:
                best = (cost, s, grid)
        _, s, grid = best
        tick = int(round(grid * res))
        out.append(Quantized(tick, e, s, (tempo.tick_to_time(tick) - e.time) * 1000.0))

    # 3) Funde eventos que caíram no mesmo tick (fica o mais forte; polifonia = máxima).
    out.sort(key=lambda q: (q.tick, -q.event.strength))
    merged: list[Quantized] = []
    for q in out:
        if merged and merged[-1].tick == q.tick:
            keep = merged[-1]
            keep.event.polyphony = max(keep.event.polyphony, q.event.polyphony)
            keep.event.duration = max(keep.event.duration, q.event.duration)
            continue
        merged.append(q)
    return merged
