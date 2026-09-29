"""Teste de fumaça da pilha de ML, feito DENTRO do contêiner isolado.

Gera um áudio sintético (clique a 120 BPM + "guitarra" em colcheias), roda Beat This!, Demucs
(htdemucs_6s) e Basic Pitch (ONNX), e registra versões, tempos e o SHA-256 de todo arquivo
baixado (pesos de modelo) em /work/smoke.json.
"""
import hashlib
import importlib.metadata as md
import json
import os
import time

import numpy as np
import soundfile as sf

OUT = {}
SR = 44100


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def make_test_audio(path, seconds=20.0):
    t = np.arange(int(seconds * SR)) / SR
    y = np.zeros_like(t)
    # clique em cada batida (120 BPM), acento no tempo forte de cada compasso 4/4
    for k in range(int(seconds / 0.5)):
        i = int(k * 0.5 * SR)
        y[i:i + 400] += np.hanning(800)[400:] * (1.0 if k % 4 == 0 else 0.6)
    # "guitarra": onda quadrada decaindo, em colcheias, melodia de 8 notas
    melody = [52, 55, 57, 59, 57, 55, 52, 50]
    for k in range(int(seconds / 0.25)):
        f0 = 440.0 * 2 ** ((melody[k % 8] - 69) / 12)
        n = int(0.22 * SR)
        tt = np.arange(n) / SR
        i0 = int(k * 0.25 * SR)
        y[i0:i0 + n] += 0.3 * np.exp(-tt * 8) * np.sign(np.sin(2 * np.pi * f0 * tt))
    stereo = np.stack([y, y], axis=1) * 0.5
    sf.write(path, stereo, SR)
    return stereo


def main():
    stereo = make_test_audio("/work/test.wav")

    # 1) Beat This! (batidas e tempos fortes)
    from beat_this.inference import File2Beats
    t0 = time.time()
    f2b = File2Beats(checkpoint_path="final0", device="cpu", dbn=False)
    beats, downbeats = f2b("/work/test.wav")
    OUT["beat_this"] = {
        "seconds": round(time.time() - t0, 2),
        "n_beats": int(len(beats)),
        "bpm_estimate": float(60.0 / np.median(np.diff(beats))) if len(beats) > 1 else None,
        "first_beats": [round(float(b), 3) for b in beats[:6]],
        "first_downbeats": [round(float(b), 3) for b in downbeats[:4]],
    }

    # 2) Demucs htdemucs_6s (stems: drums, bass, other, vocals, guitar, piano)
    import torch
    from demucs.apply import apply_model
    from demucs.pretrained import get_model
    t0 = time.time()
    model = get_model("htdemucs_6s")
    model.eval()
    wav = torch.tensor(stereo.T, dtype=torch.float32)[None]
    with torch.no_grad():
        sources = apply_model(model, wav, device="cpu", progress=False)
    guitar = sources[0, model.sources.index("guitar")].numpy()
    OUT["demucs"] = {
        "seconds": round(time.time() - t0, 2),
        "sources": list(model.sources),
        "shape": list(sources.shape),
        "guitar_rms": float(np.sqrt(np.mean(guitar ** 2))),
    }

    # 3) Basic Pitch via ONNX (sem TensorFlow)
    import basic_pitch
    from basic_pitch.inference import predict
    t0 = time.time()
    _, _, note_events = predict("/work/test.wav", basic_pitch.ICASSP_2022_MODEL_PATH)
    pitches = sorted({int(n[2]) for n in note_events})
    OUT["basic_pitch"] = {
        "seconds": round(time.time() - t0, 2),
        "model_path": str(basic_pitch.ICASSP_2022_MODEL_PATH),
        "n_notes": len(note_events),
        "pitches_detected": pitches[:20],
        "expected_pitches": [50, 52, 55, 57, 59],
    }

    # 4) Arquivos baixados (pesos) com hash
    files = []
    for root, _, names in os.walk("/work/cache"):
        for name in names:
            p = os.path.join(root, name)
            files.append({"path": p, "bytes": os.path.getsize(p), "sha256": sha256(p)})
    OUT["downloads"] = files
    OUT["versions"] = {p: md.version(p) for p in [
        "torch", "torchaudio", "beat-this", "demucs", "librosa", "basic-pitch", "onnxruntime",
        "numpy", "scipy", "soundfile", "mido", "einops", "rotary-embedding-torch", "soxr"]}

    with open("/work/smoke.json", "w") as f:
        json.dump(OUT, f, indent=2)
    print(json.dumps(OUT, indent=2))


if __name__ == "__main__":
    main()
