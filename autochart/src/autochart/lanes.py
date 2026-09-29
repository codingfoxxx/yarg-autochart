"""Escolha dos trastes: contorno melódico → trastes jogáveis.

Para cada nota há um conjunto de "estados" (traste único, ou formato de acorde) e o caminho de
menor custo é achado por programação dinâmica (Viterbi). O custo combina:
- posição: notas graves do trecho perto do verde, agudas perto do laranja;
- movimento: subir a altura → mover para a direita, com salto proporcional ao intervalo;
- direção errada e "ficar parado quando a altura mudou" são penalizados;
- ergonomia: saltos grandes entre notas rápidas são caros.
Depois, compassos com o mesmo riff (mesmo ritmo e intervalos) recebem o mesmo desenho.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class LaneParams:
    n_lanes: int = 5
    max_chord: int = 3
    forbidden_pairs: frozenset = field(default_factory=frozenset)  # (traste mais baixo, mais alto)
    w_pos: float = 0.35
    w_motion: float = 1.0
    w_dir: float = 2.5
    w_static: float = 1.2
    w_jump_fast: float = 2.0
    window_s: float = 4.0


def desired_step(dp: float, n_lanes: int) -> int:
    """Quantos trastes mover para uma variação de altura ``dp`` (semitons)."""
    a = abs(dp)
    if a < 0.5:
        step = 0
    elif a <= 2.5:
        step = 1
    elif a <= 5.5:
        step = 2
    elif a <= 9.5:
        step = 3
    else:
        step = 4
    return int(np.sign(dp)) * min(step, n_lanes - 1)


def candidate_states(size: int, params: LaneParams) -> list[tuple[int, ...]]:
    n = params.n_lanes
    if size <= 1:
        return [(lane,) for lane in range(n)]
    shapes = [(0, 1), (0, 2)] if size == 2 else [(0, 1, 2)]
    out = []
    for base in range(n):
        for shape in shapes:
            lanes = tuple(base + o for o in shape)
            if lanes[-1] >= n or (lanes[0], lanes[-1]) in params.forbidden_pairs:
                continue
            out.append(lanes)
    return out or [(lane,) for lane in range(n)]


def _targets(pitches: np.ndarray, times: np.ndarray, n_lanes: int, window: float) -> np.ndarray:
    """Posição desejada (0..n-1) de cada nota pelo ranking da altura na vizinhança."""
    out = np.empty(len(pitches))
    for i, (p, t) in enumerate(zip(pitches, times)):
        mask = np.abs(times - t) <= window
        local = pitches[mask]
        if len(local) <= 1 or np.ptp(local) < 0.5:
            out[i] = (n_lanes - 1) / 2
            continue
        less = np.sum(local < p - 0.25)
        equal = np.sum(np.abs(local - p) <= 0.25)
        frac = (less + 0.5 * (equal - 1)) / (len(local) - 1)
        out[i] = frac * (n_lanes - 1)
    return out


def assign_lanes(pitches: list[float], times: list[float], sizes: list[int], params: LaneParams,
                 wide: list[bool] | None = None) -> list[tuple[int, ...]]:
    n = len(pitches)
    if n == 0:
        return []
    p = np.asarray(pitches, float)
    t = np.asarray(times, float)
    targets = _targets(p, t, params.n_lanes, params.window_s)
    states = [candidate_states(min(sizes[i], params.max_chord), params) for i in range(n)]
    centers = [np.array([np.mean(s) for s in st]) for st in states]

    cost = params.w_pos * np.abs(centers[0] - targets[0])
    if wide and wide[0]:
        cost = cost + np.array([0.0 if s[-1] - s[0] >= 2 else 0.3 for s in states[0]])
    back: list[np.ndarray] = []
    for i in range(1, n):
        dp = p[i] - p[i - 1]
        want = desired_step(dp, params.n_lanes)
        gap = t[i] - t[i - 1]
        move = centers[i][:, None] - centers[i - 1][None, :]  # (atual, anterior)
        trans = params.w_motion * np.abs(move - want)
        if abs(dp) >= 0.5:
            wrong_dir = (np.sign(move) != np.sign(dp)) & (move != 0)
            trans = trans + params.w_dir * wrong_dir + params.w_static * (move == 0)
        if gap < 0.15:
            trans = trans + params.w_jump_fast * np.maximum(0.0, np.abs(move) - 1)
        elif gap < 0.25:
            trans = trans + params.w_jump_fast * np.maximum(0.0, np.abs(move) - 2)
        total = trans + cost[None, :]
        best_prev = np.argmin(total, axis=1)
        emission = params.w_pos * np.abs(centers[i] - targets[i])
        if wide and wide[i]:
            emission = emission + np.array([0.0 if s[-1] - s[0] >= 2 else 0.3 for s in states[i]])
        cost = total[np.arange(len(states[i])), best_prev] + emission
        back.append(best_prev)

    idx = int(np.argmin(cost))
    path = [idx]
    for bp in reversed(back):
        idx = int(bp[idx])
        path.append(idx)
    path.reverse()
    return [states[i][k] for i, k in enumerate(path)]


def enforce_repeats(ticks: list[int], lanes: list[tuple[int, ...]], pitches: list[float],
                    sizes: list[int], measure_starts: list[int]) -> tuple[list[tuple[int, ...]], float]:
    """Compassos com o mesmo riff recebem o desenho da primeira ocorrência.

    Devolve (trastes, fração de compassos repetidos que já estavam ou ficaram consistentes).
    """
    if not ticks:
        return lanes, 1.0
    starts = np.asarray(measure_starts)
    by_measure: dict[int, list[int]] = {}
    for i, tick in enumerate(ticks):
        m = int(np.searchsorted(starts, tick, side="right")) - 1
        by_measure.setdefault(m, []).append(i)

    first: dict[tuple, list[int]] = {}
    out = list(lanes)
    repeated = changed = 0
    for m in sorted(by_measure):
        idx = by_measure[m]
        if len(idx) < 2:
            continue
        base = pitches[idx[0]]
        sig = tuple((ticks[i] - int(starts[m]), int(round(pitches[i] - base)), sizes[i]) for i in idx)
        if sig in first:
            repeated += 1
            src = first[sig]
            if [out[j] for j in src] != [out[i] for i in idx]:
                changed += 1
                for j, i in zip(src, idx):
                    out[i] = out[j]
        else:
            first[sig] = idx
    consistency = 1.0 - (changed / repeated) if repeated else 1.0
    return out, consistency
