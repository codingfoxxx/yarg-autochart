"""As quatro dificuldades: seleção de notas, trastes, sustains e intenção de HOPO.

Regras (resumo de docs/pesquisa/estado-da-arte-autochart.md §G, adaptadas):
- Expert: transcrição quase literal, com intervalo mínimo e todos os tipos de acorde (até 3 notas).
- Hard: sem semicolcheias contínuas; acordes de até 2 notas.
- Medium: ~semínimas; 4 trastes; acordes de 2 notas em formatos simples; sem HOPO.
- Easy: ~mínimas; 3 trastes; sem acordes; sem HOPO.
Cada dificuldade é subconjunto da anterior (Expert ⊇ Hard ⊇ Medium ⊇ Easy).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .lanes import LaneParams, assign_lanes, enforce_repeats
from .model import Event, Note
from .quantize import Quantized
from .tempomap import TempoMap


@dataclass(frozen=True)
class Profile:
    name: str
    n_lanes: int
    max_chord: int
    min_gap_beats: float       # intervalo mínimo entre notas, em batidas
    min_gap_s: float           # e em segundos (vale o maior)
    sustain_min_s: float       # sustain mais curto que isso vira nota simples
    sustain_gap_beats: float   # folga entre o fim do sustain e a próxima nota
    hopos: bool                # permite HOPO (natural ou forçado)
    forbidden_pairs: frozenset = frozenset()


PROFILES = {
    "Expert": Profile("Expert", 5, 3, 0.25, 0.070, 0.30, 0.25, True),
    "Hard": Profile("Hard", 5, 2, 0.50, 0.140, 0.30, 0.25, True, frozenset({(0, 4)})),
    "Medium": Profile("Medium", 4, 2, 1.00, 0.280, 0.35, 0.375, False, frozenset({(0, 3), (0, 4), (1, 4)})),
    "Easy": Profile("Easy", 3, 1, 2.00, 0.550, 0.40, 0.50, False),
}


def metrical_weight(tick: int, tempo: TempoMap) -> float:
    """Peso métrico da posição: tempo forte > batida > colcheia > semicolcheia/tercina."""
    res = tempo.resolution
    starts = tempo.measure_starts(tick)
    if starts and starts[-1] == tick:
        return 4.0
    if tick % res == 0:
        return 3.0
    if tick % (res // 2) == 0:
        return 2.0
    if tick % (res // 4) == 0 or tick % (res // 3) == 0:
        return 1.0
    return 0.5


def select(candidates: list[int], ticks: list[int], priorities: list[float], tempo: TempoMap,
           profile: Profile, density: float = 1.0) -> list[int]:
    """Escolhe um subconjunto de ``candidates`` respeitando o intervalo mínimo do perfil.

    Processa por prioridade (peso métrico × força); ``density`` < 1 aumenta o intervalo mínimo.
    """
    density = float(np.clip(density, 0.2, 1.5))
    order = sorted(candidates, key=lambda i: (-priorities[i], ticks[i]))
    chosen: list[int] = []
    chosen_times: list[float] = []
    for i in order:
        t = tempo.tick_to_time(ticks[i])
        spb = 60.0 / tempo.bpm_at_tick(ticks[i])
        gap = max(profile.min_gap_beats * spb, profile.min_gap_s) / density
        if chosen_times:
            j = int(np.searchsorted(chosen_times, t))
            if (j < len(chosen_times) and chosen_times[j] - t < gap - 1e-6) or \
               (j > 0 and t - chosen_times[j - 1] < gap - 1e-6):
                continue
        chosen.append(i)
        chosen_times.insert(int(np.searchsorted(chosen_times, t)), t)
    return sorted(chosen, key=lambda i: ticks[i])


def _sustain_length(note_tick: int, next_tick: int | None, event: Event, tempo: TempoMap,
                    profile: Profile) -> int:
    if event.duration < profile.sustain_min_s:
        return 0
    res = tempo.resolution
    start_t = tempo.tick_to_time(note_tick)
    end_tick = int(tempo.time_to_tick(start_t + event.duration))
    if next_tick is not None:
        end_tick = min(end_tick, next_tick - int(profile.sustain_gap_beats * res))
    step = res // 4
    end_tick = (end_tick // step) * step  # termina no grid de semicolcheia
    length = end_tick - note_tick
    if length <= 0 or tempo.tick_to_time(end_tick) - start_t < profile.sustain_min_s:
        return 0
    return length


def _hopo_intent(prev: Note | None, note: Note, event: Event, profile: Profile, tempo: TempoMap) -> bool | None:
    if not profile.hopos:
        return False
    if prev is None or note.is_chord:
        return None
    if profile.name == "Hard":
        return False if prev.is_chord else None
    gap_beats = (note.tick - prev.tick) / tempo.resolution
    if event.attack >= 1.3 and gap_beats >= 0.25:
        return False  # ataque acentuado: palhetada
    if event.attack <= 0.5 and gap_beats <= 0.5 and prev.lanes != note.lanes:
        return True   # sem ataque novo (ligado): HOPO
    return None


def build_difficulties(quantized: list[Quantized], tempo: TempoMap, *, density: float = 1.0,
                       difficulties: tuple[str, ...] = ("Expert", "Hard", "Medium", "Easy"),
                       enforce_riffs: bool = True) -> tuple[dict[str, list[Note]], dict[str, float]]:
    """Gera as notas de cada dificuldade. Devolve (notas por dificuldade, consistência de riffs)."""
    ticks = [q.tick for q in quantized]
    events = [q.event for q in quantized]
    priorities = [metrical_weight(t, tempo) * (0.5 + min(e.strength, 2.0)) for t, e in zip(ticks, events)]
    end_tick = (max(ticks) if ticks else 0) + 8 * tempo.resolution
    measure_starts = tempo.measure_starts(end_tick)

    out: dict[str, list[Note]] = {}
    consistency: dict[str, float] = {}
    pool = list(range(len(quantized)))
    for name in ("Expert", "Hard", "Medium", "Easy"):
        prof = PROFILES[name]
        pool = select(pool, ticks, priorities, tempo, prof, density if name == "Expert" else 1.0)
        if name not in difficulties:
            continue
        sel = pool
        pitches = [float(events[i].pitch if events[i].pitch is not None else 60.0) for i in sel]
        times = [tempo.tick_to_time(ticks[i]) for i in sel]
        sizes = [min(events[i].polyphony, prof.max_chord) for i in sel]
        params = LaneParams(n_lanes=prof.n_lanes, max_chord=prof.max_chord, forbidden_pairs=prof.forbidden_pairs)
        lanes = assign_lanes(pitches, times, sizes, params)
        if enforce_riffs:
            lanes, consistency[name] = enforce_repeats([ticks[i] for i in sel], lanes, pitches, sizes, measure_starts)
        notes: list[Note] = []
        for k, i in enumerate(sel):
            notes.append(Note(tick=ticks[i], lanes=tuple(sorted(lanes[k])), time=times[k],
                              strength=events[i].strength, pitch=pitches[k], source_index=i))
        for k, n in enumerate(notes):
            nxt = notes[k + 1].tick if k + 1 < len(notes) else None
            n.length = _sustain_length(n.tick, nxt, events[n.source_index], tempo, prof)
            n.hopo = _hopo_intent(notes[k - 1] if k else None, n, events[n.source_index], prof, tempo)
        out[name] = notes
    return out, consistency
