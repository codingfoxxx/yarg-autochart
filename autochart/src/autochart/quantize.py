"""Quantização: cada ataque detectado vai para um tick do grid.

1. Vocabulário rítmico da música: no histograma da posição dos ataques dentro da batida, mede
   quanto "peso" existe em cada subdivisão (semicolcheias em 1/4 e 3/4, tercinas em 1/3 e 2/3,
   sextinas, fusas). Só entram subdivisões com evidência — como um charter humano, que sabe se
   a música é reta ou em swing. Isso impede que a imprecisão humana (±30-40 ms) seja "explicada"
   por subdivisões densas.
2. Cada evento vai para a subdivisão permitida de menor custo (erro em ms + complexidade).
   Em passagens rápidas (ataques a menos de 3/8 de batida), semicolcheias são sempre permitidas.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .model import Event
from .tempomap import TempoMap

# Custo extra (ms) por complexidade de subdivisão.
_PENALTY = {1: 0.0, 2: 1.0, 4: 3.0, 3: 4.0, 6: 8.0, 8: 12.0}
# Pontos de cada subdivisão que não pertencem às mais simples (fração da batida).
_OWN_POINTS = {4: (0.25, 0.75), 3: (1 / 3, 2 / 3), 6: (1 / 6, 5 / 6), 8: (0.125, 0.375, 0.625, 0.875)}


@dataclass
class Quantized:
    tick: int
    event: Event
    subdivision: int
    error_ms: float  # tempo do tick − tempo do ataque


@dataclass
class RhythmProfile:
    evidence: dict[int, float]   # fração do peso dos ataques perto dos pontos próprios de cada subdivisão
    allowed: tuple[int, ...]

    def describe(self) -> str:
        names = {1: "semínimas", 2: "colcheias", 4: "semicolcheias", 3: "tercinas", 6: "sextinas", 8: "fusas"}
        return ", ".join(names[s] for s in self.allowed)


def rhythm_profile(positions: np.ndarray, weights: np.ndarray, spb: np.ndarray | None = None,
                   threshold: float = 0.05, window: float = 0.035, peak_ratio: float = 1.6,
                   precise_ms: float = 10.0, precise_frac: float = 0.5) -> RhythmProfile:
    """Quais subdivisões a música realmente usa. Uma subdivisão entra se passar num dos testes:

    - pico local: nos pontos próprios dela (ex.: 1/3 e 2/3 para tercinas) a densidade de ataques
      é ≥ ``peak_ratio`` × a das janelas vizinhas — a imprecisão humana em volta da batida se
      espalha de forma decrescente e não forma pico;
    - precisão: dos ataques que ficariam mais perto dos pontos próprios dela, pelo menos
      ``precise_frac`` caem a ≤ ``precise_ms`` — espalhamento aleatório se distribui até a metade
      do espaçamento, notas reais caem em cima (dentro do ruído do detector).
    Em ambos, os ataques envolvidos precisam somar ≥ ``threshold`` do peso total.
    """
    frac = positions - np.floor(positions)
    total = float(np.sum(weights)) or 1.0
    if spb is None:
        spb = np.full(len(positions), 0.5)

    def mass(center: float, half: float) -> float:
        dist = np.abs((frac - center + 0.5) % 1.0 - 0.5)  # distância circular
        return float(np.sum(weights[dist <= half]))

    evidence: dict[int, float] = {}
    allowed = [1, 2]
    for s in (4, 3, 6, 8):
        points = _OWN_POINTS[s]
        # teste de pico
        peak_mass = 0.0
        for p in points:
            center = mass(p, window)
            flanks = (mass(p - 2 * window, window) + mass(p + 2 * window, window)) / 2.0
            if center >= peak_ratio * flanks:
                peak_mass += center
        # teste de precisão: ataques cujo ponto mais próximo (entre as permitidas + s) é próprio de s
        grid = sorted({k / t for t in allowed + [s] for k in range(t + 1)})
        g = np.array(grid)
        nearest = g[np.argmin(np.abs(frac[:, None] - g[None, :]), axis=1)]
        own = np.isin(np.round(nearest, 6), np.round(np.array(points), 6))
        err_ms = np.abs(frac - nearest) * spb * 1000.0
        own_mass = float(np.sum(weights[own]))
        precise = own_mass > 0 and float(np.sum(weights[own & (err_ms <= precise_ms)])) >= precise_frac * own_mass
        evidence[s] = max(peak_mass, own_mass if precise else 0.0) / total
        prerequisite = s in (4, 3) or (s == 6 and 3 in allowed) or (s == 8 and 4 in allowed)
        if prerequisite and evidence[s] >= threshold:
            allowed.append(s)
    return RhythmProfile(evidence, tuple(allowed))


def quantize(events: list[Event], tempo: TempoMap, *, profile: RhythmProfile | None = None
             ) -> tuple[list[Quantized], RhythmProfile]:
    if not events:
        return [], profile or RhythmProfile({}, (1, 2))
    res = tempo.resolution
    positions = np.array([tempo.time_to_tick(e.time) / res for e in events])  # em batidas
    weights = np.array([max(e.strength, 0.05) for e in events])
    if profile is None:
        spb = np.array([tempo.seconds_per_beat_at(p * res) for p in positions])
        profile = rhythm_profile(positions, weights, spb)

    out: list[Quantized] = []
    for k, (e, p) in enumerate(zip(events, positions)):
        allowed = set(profile.allowed)
        gap = min(p - positions[k - 1] if k else 9.0, positions[k + 1] - p if k + 1 < len(positions) else 9.0)
        if gap < 0.375:
            allowed.add(4)  # passagem rápida: precisa de semicolcheias
        if gap < 0.3 and 3 in allowed:
            allowed.add(6)
        spb = tempo.seconds_per_beat_at(p * res)
        best = None
        for s in sorted(allowed):
            grid = round(p * s) / s
            err_ms = abs(p - grid) * spb * 1000.0
            cost = err_ms + _PENALTY[s]
            if best is None or cost < best[0]:
                best = (cost, s, grid)
        _, s, grid = best
        tick = int(round(grid * res))
        out.append(Quantized(tick, e, s, (tempo.tick_to_time(tick) - e.time) * 1000.0))

    # Funde eventos que caíram no mesmo tick (fica o mais forte; polifonia = máxima).
    out.sort(key=lambda q: (q.tick, -q.event.strength))
    merged: list[Quantized] = []
    for q in out:
        if merged and merged[-1].tick == q.tick:
            keep = merged[-1]
            keep.event.polyphony = max(keep.event.polyphony, q.event.polyphony)
            keep.event.duration = max(keep.event.duration, q.event.duration)
            continue
        merged.append(q)
    return merged, profile
