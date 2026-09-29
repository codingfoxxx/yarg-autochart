"""Análise do áudio: batidas, separação da guitarra, ataques (onsets) e alturas.

Cada função recebe áudio já decodificado (float32, 44,1 kHz) e devolve dados simples (arrays e
listas), para o resto do pipeline ser testável sem os modelos.
"""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import models
from .audio import SAMPLE_RATE, mono, write_wav

# ------------------------------------------------------------------------------------ batidas


@dataclass
class BeatResult:
    beats: np.ndarray
    downbeats: np.ndarray
    notes: list[str] = field(default_factory=list)

    @property
    def bpm(self) -> float:
        return float(60.0 / np.median(np.diff(self.beats))) if len(self.beats) > 1 else 0.0


BEAT_FPS = 50.0  # quadros por segundo das ativações do Beat This!


def track_beats(audio: np.ndarray, sr: int = SAMPLE_RATE, device: str = "cpu",
                min_bpm: float = 60.0, max_bpm: float = 200.0) -> BeatResult:
    """Beat This! no mix completo, com picos sub-quadro, limpeza e correção de oitava do tempo.

    Mesma regra de picos do pós-processamento "minimal" do Beat This! (máximo local em ±3
    quadros com logit > 0), mas com interpolação parabólica: o original arredonda para quadros
    de 20 ms, o que faria o grid do chart herdar esse ruído.
    """
    import torch

    a2f = models.load_beat_this_frames(device)
    with torch.no_grad():
        beat_logits, downbeat_logits = a2f(audio, sr)
    b = beat_logits.detach().float().cpu().numpy().reshape(-1)
    d = downbeat_logits.detach().float().cpu().numpy().reshape(-1)
    beats = subframe_peaks(b, BEAT_FPS)
    downs = subframe_peaks(d, BEAT_FPS)
    if len(beats):
        downs = np.unique(np.array([beats[int(np.argmin(np.abs(beats - x)))] for x in downs]))
    return clean_beats(beats, downs, min_bpm, max_bpm)


def subframe_peaks(logits: np.ndarray, fps: float, radius: int = 3) -> np.ndarray:
    from scipy.ndimage import maximum_filter1d

    x = np.asarray(logits, dtype=float)
    if x.size < 3:
        return np.array([])
    mx = maximum_filter1d(x, size=2 * radius + 1, mode="constant", cval=-1e9)
    cand = np.flatnonzero((x == mx) & (x > 0))
    if cand.size == 0:
        return np.array([])
    groups = np.split(cand, np.flatnonzero(np.diff(cand) > 1) + 1)  # platôs de quadros vizinhos
    times = []
    for g in groups:
        k = int(round(float(np.mean(g))))
        delta = 0.0
        if 0 < k < len(x) - 1:
            y0, y1, y2 = x[k - 1], x[k], x[k + 1]
            den = y0 - 2 * y1 + y2
            if den < 0:
                delta = float(np.clip(0.5 * (y0 - y2) / den, -0.5, 0.5))
        times.append((k + delta) / fps)
    return np.array(times)


def phase_offset(beats: np.ndarray, onset_times: np.ndarray, window: float = 0.04) -> tuple[float, float]:
    """Mediana (s) de ataque − batida para batidas com ataque a até ``window``; e a fração delas.

    Usado para alinhar a fase do grid aos ataques reais (bumbo/caixa costumam cair na batida).
    """
    if len(onset_times) == 0 or len(beats) == 0:
        return 0.0, 0.0
    idx = np.clip(np.searchsorted(onset_times, beats), 1, len(onset_times) - 1)
    prev, nxt = onset_times[idx - 1], onset_times[idx]
    nearest = np.where(np.abs(nxt - beats) < np.abs(prev - beats), nxt, prev)
    res = nearest - beats
    ok = np.abs(res) <= window
    if ok.sum() < 8:
        return 0.0, float(ok.mean())
    r = res[ok]
    spread = float(np.median(np.abs(r - np.median(r))))
    if spread > 0.015:
        return 0.0, float(ok.mean())
    return float(np.median(r)), float(ok.mean())


def _local_period(beats: np.ndarray, half_window: int = 8) -> np.ndarray:
    """Período local (mediana dos intervalos vizinhos) para cada intervalo entre batidas."""
    d = np.diff(beats)
    out = np.empty_like(d)
    for i in range(len(d)):
        out[i] = np.median(d[max(0, i - half_window):i + half_window + 1])
    return out


def clean_beats(beats: np.ndarray, downbeats: np.ndarray, min_bpm: float = 60.0,
                max_bpm: float = 200.0) -> BeatResult:
    notes: list[str] = []
    beats = np.unique(np.round(beats, 4))
    if len(beats) < 4:
        return BeatResult(beats, downbeats, ["poucas batidas detectadas"])

    # Regulariza pelo período local: remove batidas que criam intervalos curtos demais
    # (< 0,75 do local) e preenche buracos (≥ 1,5 do local), até estabilizar.
    removed = inserted = 0
    for _ in range(4):
        changed = False
        period = _local_period(beats)
        d = np.diff(beats)
        keep = np.ones(len(beats), dtype=bool)
        i = 0
        while i < len(d):
            if d[i] < 0.75 * period[i]:
                # remove a batida (i ou i+1) que pior se encaixa nos vizinhos
                prev = beats[i - 1] if i > 0 else beats[i] - period[i]
                nxt = beats[i + 2] if i + 2 < len(beats) else beats[i + 1] + period[i]
                err_i = abs((beats[i] - prev) - period[i]) + abs((nxt - beats[i]) - 2 * period[i]) * 0.5
                err_j = abs((beats[i + 1] - prev) - 2 * period[i]) * 0.5 + abs((nxt - beats[i + 1]) - period[i])
                keep[i if err_i > err_j else i + 1] = False
                removed += 1
                changed = True
                i += 2
                continue
            i += 1
        beats = beats[keep]
        d = np.diff(beats)
        period = _local_period(beats)
        filled = [beats[0]]
        for k in range(len(d)):
            ratio = d[k] / period[k]
            if ratio >= 1.5:
                n = int(round(ratio))
                filled.extend(beats[k] + d[k] * j / n for j in range(1, n))
                inserted += n - 1
                changed = True
            filled.append(beats[k + 1])
        beats = np.array(filled)
        if not changed:
            break
    # Trechos inteiros em meio tempo (o detector trocou de nível métrico por várias batidas): o
    # período local também dobra e a regra acima não vê. Compara com o período global.
    global_period = float(np.median(np.diff(beats)))
    d = np.diff(beats)
    filled = [beats[0]]
    halftime = 0
    for k in range(len(d)):
        ratio = d[k] / global_period
        n = 2 if 1.8 <= ratio <= 2.25 else 3 if 2.7 <= ratio <= 3.3 else 1
        if n > 1:
            filled.extend(beats[k] + d[k] * j / n for j in range(1, n))
            halftime += n - 1
        filled.append(beats[k + 1])
    beats = np.array(filled)
    inserted += halftime
    if removed or inserted:
        notes.append(f"batidas corrigidas: {removed} espúrias removidas, {inserted} inseridas"
                     + (f" (das quais {halftime} em trecho de meio tempo)" if halftime else ""))

    bpm = 60.0 / float(np.median(np.diff(beats)))
    if bpm > max_bpm:
        # Metade do tempo: fica a paridade que contém mais tempos fortes.
        idx = [int(np.argmin(np.abs(beats - d))) for d in downbeats]
        even = sum(1 for i in idx if i % 2 == 0)
        phase = 0 if even >= len(idx) - even else 1
        beats = beats[phase::2]
        notes.append(f"tempo detectado {bpm:.0f} BPM > {max_bpm:.0f}: usando a metade")
    elif bpm < min_bpm:
        mids = (beats[:-1] + beats[1:]) / 2
        beats = np.sort(np.concatenate([beats, mids]))
        notes.append(f"tempo detectado {bpm:.0f} BPM < {min_bpm:.0f}: usando o dobro")
    return BeatResult(beats, np.asarray(downbeats, float), notes)


# ------------------------------------------------------------------------------------ separação

def separate(audio: np.ndarray, sr: int = SAMPLE_RATE, device: str = "cpu",
             shifts: int = 1, overlap: float = 0.25) -> dict[str, np.ndarray]:
    """Separa em 6 stems (drums, bass, other, vocals, guitar, piano), cada um (amostras, 2)."""
    import torch
    from demucs.apply import apply_model

    if sr != SAMPLE_RATE:
        raise ValueError("o Demucs htdemucs_6s trabalha a 44,1 kHz")
    model = models.load_htdemucs_6s()
    wav = torch.from_numpy(np.ascontiguousarray(audio.T))  # (2, amostras)
    ref = wav.mean(0)
    mean, std = ref.mean(), ref.std() + 1e-8
    wav = (wav - mean) / std  # mesma normalização da linha de comando do Demucs
    torch.set_num_threads(max(1, (os.cpu_count() or 4) - 1))
    with torch.no_grad():
        sources = apply_model(model, wav[None], device=device, shifts=shifts, split=True,
                              overlap=overlap, progress=False)[0]
    sources = sources * std + mean
    return {name: sources[i].numpy().T.astype(np.float32) for i, name in enumerate(model.sources)}


# ------------------------------------------------------------------------------------ ataques

@dataclass
class Onsets:
    times: np.ndarray       # s
    strengths: np.ndarray   # relativo (1 ≈ ataque típico forte)
    envelope: np.ndarray    # função de detecção por quadro
    frame_times: np.ndarray


ONSET_HOP = 220  # 5 ms a 44,1 kHz


def detect_onsets(y: np.ndarray, sr: int = SAMPLE_RATE, sensitivity: float = 0.5,
                  min_interval: float = 0.045, latency_correction: float = 0.0) -> Onsets:
    """Fluxo espectral estilo SuperFlux (librosa: lag=2, max_size=3) com escolha de picos.

    ``sensitivity`` (0..1): maior = mais ataques (limiar ``delta`` menor).
    """
    import librosa

    if y.ndim == 2:
        y = mono(y)
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=2048, hop_length=ONSET_HOP,
                                       fmin=27.5, fmax=16000.0, n_mels=138)
    env = librosa.onset.onset_strength(S=librosa.power_to_db(S, ref=np.max), sr=sr,
                                       hop_length=ONSET_HOP, lag=2, max_size=3)
    delta = float(np.interp(np.clip(sensitivity, 0.0, 1.0), [0.0, 0.5, 1.0], [0.20, 0.07, 0.02]))
    frames = librosa.onset.onset_detect(onset_envelope=env, sr=sr, hop_length=ONSET_HOP, units="frames",
                                        delta=delta, wait=max(1, int(min_interval * sr / ONSET_HOP)))
    frame_times = librosa.frames_to_time(np.arange(len(env)), sr=sr, hop_length=ONSET_HOP)
    times = refine_onsets(y, sr, frame_times[frames]) + latency_correction
    peaks = env[frames]
    scale = float(np.percentile(peaks, 90)) if len(peaks) else 1.0
    strengths = peaks / max(scale, 1e-9)
    return Onsets(times, strengths, env, frame_times)


def refine_onsets(y: np.ndarray, sr: int, times: np.ndarray, before: float = 0.035,
                  after: float = 0.060, smooth: float = 0.0015) -> np.ndarray:
    """Ajusta cada ataque para o meio da subida do envelope de amplitude.

    O pico do fluxo espectral vem adiantado (a janela de 46 ms "vê" a nota chegando). Aqui, numa
    janela curta em volta do ataque, o novo tempo é o primeiro instante (após o vale anterior) em
    que o envelope passa da metade entre o vale e o pico seguinte. Sem subida clara, mantém o tempo.
    """
    env = np.abs(y).astype(np.float64)
    k = max(1, int(smooth * sr))
    env = np.convolve(env, np.ones(k) / k, mode="same")
    out = np.array(times, dtype=float)
    nb, na = int(before * sr), int(after * sr)
    for i, t in enumerate(times):
        c = int(round(t * sr))
        a, b = max(0, c - nb), min(len(env), c + na)
        seg = env[a:b]
        if len(seg) < 16:
            continue
        valley = int(np.argmin(seg[: max(1, c - a)]))          # vale antes do ataque
        peak = valley + int(np.argmax(seg[valley:]))
        lo, hi = seg[valley], seg[peak]
        if hi < 1e-6 or hi - lo < 0.25 * hi:
            continue                                             # sem subida clara (ligado)
        half = lo + 0.5 * (hi - lo)
        cross = valley + int(np.argmax(seg[valley:peak + 1] >= half))
        out[i] = (a + cross) / sr
    return out


# ------------------------------------------------------------------------------------ alturas

@dataclass
class PitchNote:
    start: float
    end: float
    pitch: int
    amplitude: float


def transcribe(y: np.ndarray, sr: int = SAMPLE_RATE, min_freq: float = 60.0,
               max_freq: float = 1600.0) -> list[PitchNote]:
    """Notas (início, fim, altura MIDI) com o Basic Pitch via ONNX (sem TensorFlow)."""
    models.go_offline()
    import basic_pitch
    from basic_pitch.inference import predict

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "stem.wav"
        write_wav(y if y.ndim == 2 else np.stack([y, y], axis=1), path, sr)
        _, _, events = predict(str(path), basic_pitch.ICASSP_2022_MODEL_PATH,
                               onset_threshold=0.5, frame_threshold=0.3, minimum_note_length=58.0,
                               minimum_frequency=min_freq, maximum_frequency=max_freq, melodia_trick=True)
    return sorted((PitchNote(float(e[0]), float(e[1]), int(e[2]), float(e[3])) for e in events),
                  key=lambda n: (n.start, n.pitch))
