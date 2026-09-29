"""Eventos musicais: junta os ataques (onsets) com as notas transcritas (altura, polifonia, duração)."""
from __future__ import annotations

import bisect

import numpy as np

from .analysis import Onsets, PitchNote
from .model import Event

# Intervalos (semitons acima da nota mais grave) que uma única nota distorcida produz sozinha como
# harmônicos: não indicam acorde. A quinta (+7) não está aqui: é a assinatura do power chord.
HARMONIC_INTERVALS = {12, 19, 24, 28, 31, 34, 36}


def chord_size(pitches: list[int], amplitudes: list[float]) -> tuple[int, int]:
    """(tamanho do acorde 1..3, altura da nota mais grave) a partir das notas simultâneas."""
    if not pitches:
        return 1, -1
    root = min(pitches)
    peak = max(amplitudes)
    tones = set()
    for p, a in zip(pitches, amplitudes):
        interval = p - root
        if interval <= 0 or interval in HARMONIC_INTERVALS or a < 0.45 * peak:
            continue
        tones.add(interval % 12)
    return min(1 + len(tones), 3), root


def make_bleed_ratio(target: np.ndarray, others: list[np.ndarray], sr: int, window: float = 0.12):
    """Função (início, altura MIDI) → energia dos outros stems ÷ energia do stem-alvo naquela altura.

    Mede a fundamental e 2 harmônicos numa janela curta após o início. Razão alta = a nota está
    muito mais forte em outro instrumento (órgão, piano…): provável vazamento no stem-alvo.
    """
    t = target.mean(axis=1) if target.ndim == 2 else target
    o = sum((x.mean(axis=1) if x.ndim == 2 else x) for x in others) if others else np.zeros_like(t)
    n = int(window * sr)
    hann = np.hanning(n)
    idx = np.arange(n)

    def energy(y: np.ndarray, a: int, f0: float) -> float:
        seg = y[a:a + n]
        if len(seg) < n:
            return 0.0
        seg = seg * hann
        total = 0.0
        for h in (1, 2, 3):
            w = np.exp(-2j * np.pi * f0 * h * idx / sr)
            total += abs(np.dot(seg, w)) ** 2
        return total

    def ratio(start: float, pitch: float) -> float:
        a = max(0, int(start * sr))
        f0 = 440.0 * 2 ** ((pitch - 69.0) / 12.0)
        return energy(o, a, f0) / (energy(t, a, f0) + 1e-12)

    return ratio


def build_events(onsets: Onsets, notes: list[PitchNote], *, match_before: float = 0.05,
                 match_after: float = 0.08, legato_min_amplitude: float = 0.4,
                 missed_min_amplitude: float = 0.5, legato_max_interval: int = 5,
                 legato_min_gap: float = 0.06, bleed_ratio=None,
                 bleed_max_transcribed: float = 4.0, bleed_max_onset: float = 8.0) -> list[Event]:
    starts = [n.start for n in notes]
    used: set[int] = set()
    events: list[Event] = []
    rejected_bleed = 0

    for t, strength in zip(onsets.times, onsets.strengths):
        lo = bisect.bisect_left(starts, t - match_before)
        hi = bisect.bisect_right(starts, t + match_after)
        idx = [i for i in range(lo, hi) if i not in used]
        if idx:
            used.update(idx)
            size, root = chord_size([notes[i].pitch for i in idx], [notes[i].amplitude for i in idx])
            if size == 1:
                best = max(idx, key=lambda i: notes[i].amplitude)
                pitch = float(notes[best].pitch)
            else:
                pitch = float(root)
            duration = max(notes[i].end for i in idx) - t
            if bleed_ratio is not None and bleed_ratio(float(t), pitch) >= bleed_max_onset:
                rejected_bleed += 1
                continue
            events.append(Event(time=float(t), strength=float(strength), pitch=pitch, polyphony=size,
                                duration=max(0.0, duration)))
        else:
            events.append(Event(time=float(t), strength=float(strength)))

    # Notas transcritas sem ataque detectado. Só viram evento em dois casos:
    # - ligado (hammer-on / pull-off): outra nota termina quando esta começa (±40 ms), a um
    #   intervalo pequeno (≤ 5 semitons) — é uma transição de nota, não uma nota por cima de outra;
    # - ataque perdido: amplitude alta e subida real no envelope de ataques perto do início.
    # O resto (vazamento de outros instrumentos no stem, harmonia sustentada) é descartado.
    event_times = np.array(sorted(e.time for e in events)) if events else np.array([])
    env, env_t = onsets.envelope, onsets.frame_times
    env_level = float(np.percentile(env, 80)) if len(env) else 0.0
    for i, n in enumerate(notes):
        if i in used or n.amplitude < legato_min_amplitude:
            continue
        if event_times.size and np.min(np.abs(event_times - n.start)) < legato_min_gap:
            continue
        legato = any(o.pitch != n.pitch and o.start < n.start - 0.03 and abs(o.end - n.start) <= 0.04
                     and abs(o.pitch - n.pitch) <= legato_max_interval
                     for o in notes[max(0, i - 8):i])
        if legato:
            attack = 0.4
        else:
            j = int(np.searchsorted(env_t, n.start))
            local = float(np.max(env[max(0, j - 4):j + 5])) if len(env) else 0.0
            if n.amplitude < missed_min_amplitude or local < env_level:
                continue
            attack = 0.8
        if bleed_ratio is not None and bleed_ratio(n.start, float(n.pitch)) >= bleed_max_transcribed:
            rejected_bleed += 1
            continue
        events.append(Event(time=n.start, strength=0.25, pitch=float(n.pitch), polyphony=1,
                            duration=n.end - n.start, attack=attack, from_onset=False))

    events.sort(key=lambda e: e.time)
    _relative_attack(events)
    build_events.rejected_bleed = rejected_bleed  # para o relatório
    return events


def _relative_attack(events: list[Event], window: float = 2.0) -> None:
    """Nitidez do ataque de cada evento em relação à mediana dos vizinhos (±window s)."""
    times = np.array([e.time for e in events])
    strengths = np.array([e.strength for e in events])
    for k, e in enumerate(events):
        if not e.from_onset:  # veio só da transcrição: nitidez já definida
            continue
        lo = bisect.bisect_left(times, e.time - window)
        hi = bisect.bisect_right(times, e.time + window)
        med = float(np.median(strengths[lo:hi])) if hi > lo else 1.0
        e.attack = float(e.strength / max(med, 1e-6))


def fill_missing_pitch(events: list[Event], brightness: np.ndarray | None = None) -> float:
    """Completa alturas ausentes. Devolve a fração de eventos que tinham altura.

    Sem altura, usa o brilho espectral (se fornecido) como aproximação do contorno; senão repete
    a última altura conhecida.
    """
    known = sum(1 for e in events if e.pitch is not None)
    last = None
    for k, e in enumerate(events):
        if e.pitch is None:
            if brightness is not None and not np.isnan(brightness[k]):
                e.pitch = float(brightness[k])
            elif last is not None:
                e.pitch = last
        if e.pitch is not None:
            last = e.pitch
    for e in events:  # começo sem nenhuma referência
        if e.pitch is None:
            e.pitch = last if last is not None else 60.0
    return known / len(events) if events else 0.0
