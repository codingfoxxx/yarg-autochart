"""Seções da música (para o modo prática): fronteiras estruturais alinhadas a compassos."""
from __future__ import annotations

import numpy as np

from .tempomap import TempoMap


def detect_sections(y: np.ndarray, sr: int, tempo: TempoMap, first_tick: int, end_tick: int,
                    *, min_measures: int = 4, kernel_measures: int = 4) -> list[tuple[int, str]]:
    """Segmenta por novidade (matriz de autossimilaridade de croma + timbre por compasso).

    Rótulos: "Parte A", "Parte B"… com repetição ("Parte A 2") quando um trecho se parece com
    um anterior. O primeiro trecho, se vier antes das notas, vira "Intro".
    """
    import librosa

    if y.ndim == 2:
        y = y.mean(axis=1)
    hop = 2048
    chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=hop)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, hop_length=hop, n_mfcc=13)
    frame_times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=hop)

    starts = [s for s in tempo.measure_starts(end_tick) if s <= end_tick]
    if len(starts) < 2 * min_measures:
        return [(first_tick, "Parte A")]
    bounds = [tempo.tick_to_time(s) for s in starts] + [tempo.tick_to_time(end_tick)]
    feats = []
    for a, b in zip(bounds, bounds[1:]):
        m = (frame_times >= a) & (frame_times < b)
        if not np.any(m):
            m = np.argmin(np.abs(frame_times - a)) == np.arange(len(frame_times))
        c = chroma[:, m].mean(axis=1)
        t = mfcc[1:, m].mean(axis=1)
        v = np.concatenate([c / (np.linalg.norm(c) + 1e-9), 0.5 * t / (np.linalg.norm(t) + 1e-9)])
        feats.append(v)
    X = np.array(feats)
    X = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
    S = X @ X.T

    k = kernel_measures
    n = len(S)
    kernel = np.kron(np.array([[1, -1], [-1, 1]]), np.ones((k, k)))
    novelty = np.zeros(n)
    for i in range(k, n - k):
        novelty[i] = float(np.sum(S[i - k:i + k, i - k:i + k] * kernel))
    thr = novelty.mean() + 0.5 * novelty.std()
    peaks = []
    for i in range(1, n - 1):
        if novelty[i] > thr and novelty[i] >= novelty[i - 1] and novelty[i] >= novelty[i + 1]:
            if not peaks or i - peaks[-1] >= min_measures:
                peaks.append(i)
            elif novelty[i] > novelty[peaks[-1]]:
                peaks[-1] = i

    seg_starts = [0] + [p for p in peaks if p > 0]
    segments = list(zip(seg_starts, seg_starts[1:] + [n]))
    protos: list[tuple[str, np.ndarray]] = []
    counters: dict[str, int] = {}
    out: list[tuple[int, str]] = []
    for si, (a, b) in enumerate(segments):
        tick = int(starts[a])
        seg_end = int(starts[b]) if b < len(starts) else end_tick
        if si == 0 and seg_end <= first_tick and len(segments) > 1:
            out.append((tick, "Intro"))  # trecho inteiro antes da primeira nota
            continue
        v = X[a:b].mean(axis=0)
        v = v / (np.linalg.norm(v) + 1e-9)
        match = next((name for name, p in protos if float(v @ p) > 0.95), None)
        if match is None:
            match = f"Parte {chr(ord('A') + len(protos))}" if len(protos) < 26 else f"Parte {len(protos) + 1}"
            protos.append((match, v))
        counters[match] = counters.get(match, 0) + 1
        out.append((tick, match if counters[match] == 1 else f"{match} ({counters[match]})"))
    return out
