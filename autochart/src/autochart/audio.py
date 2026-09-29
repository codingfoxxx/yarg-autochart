"""Entrada e saída de áudio via ffmpeg.

O mesmo PCM decodificado alimenta a análise e o song.ogg gravado: assim o tempo das notas e o
áudio do jogo ficam alinhados por construção (o ffmpeg já descarta o atraso de codificação de MP3).
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import numpy as np

SAMPLE_RATE = 44100


class AudioError(RuntimeError):
    pass


def ffmpeg_path() -> str:
    exe = os.environ.get("AUTOCHART_FFMPEG") or shutil.which("ffmpeg")
    if not exe:
        raise AudioError("ffmpeg não encontrado no PATH (ou defina AUTOCHART_FFMPEG).")
    return exe


def decode(path: Path, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Decodifica qualquer formato suportado pelo ffmpeg para float32 estéreo (amostras, 2)."""
    cmd = [ffmpeg_path(), "-v", "error", "-nostdin", "-i", str(path),
           "-map", "0:a:0", "-f", "f32le", "-acodec", "pcm_f32le", "-ac", "2", "-ar", str(sr), "-"]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        raise AudioError(f"ffmpeg não conseguiu ler {path}: {proc.stderr.decode(errors='replace').strip()}")
    audio = np.frombuffer(proc.stdout, dtype=np.float32)
    if audio.size < sr:
        raise AudioError(f"áudio vazio ou curto demais: {path}")
    return audio.reshape(-1, 2).copy()


def encode_ogg(audio: np.ndarray, path: Path, sr: int = SAMPLE_RATE, quality: int = 6) -> None:
    """Grava Ogg Vorbis (formato que o YARG lê) a partir de float32 (amostras, 2)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.clip(audio, -1.0, 1.0).astype(np.float32).tobytes()
    cmd = [ffmpeg_path(), "-v", "error", "-nostdin", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "2",
           "-i", "-", "-c:a", "libvorbis", "-q:a", str(quality), str(path)]
    proc = subprocess.run(cmd, input=data, capture_output=True)
    if proc.returncode != 0:
        raise AudioError(f"ffmpeg não conseguiu gravar {path}: {proc.stderr.decode(errors='replace').strip()}")


def write_wav(audio: np.ndarray, path: Path, sr: int = SAMPLE_RATE) -> None:
    import soundfile as sf
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), audio, sr, subtype="FLOAT")


def pad_start(audio: np.ndarray, seconds: float, sr: int = SAMPLE_RATE) -> np.ndarray:
    n = int(round(seconds * sr))
    if n <= 0:
        return audio
    return np.concatenate([np.zeros((n, audio.shape[1]), dtype=audio.dtype), audio])


def mono(audio: np.ndarray) -> np.ndarray:
    return audio.mean(axis=1).astype(np.float32)


def rms_db(audio: np.ndarray) -> float:
    rms = float(np.sqrt(np.mean(np.square(audio), dtype=np.float64)))
    return 20.0 * np.log10(max(rms, 1e-12))
