#!/usr/bin/env bash
# Roda DENTRO de um contêiner python:3.11-slim descartável (ver sandbox/README.md).
# /sandbox = estes scripts (somente leitura); /work = saídas (pasta montada do host).
set -euo pipefail
export PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1
export TORCH_HOME=/work/cache/torch XDG_CACHE_HOME=/work/cache HF_HOME=/work/cache/hf
mkdir -p /work/log /work/cache
python --version

echo "== PyTorch (CPU, índice oficial download.pytorch.org)"
# Fixado em 2.8.0: no PC (Windows 11 com Smart App Control ativo), as DLLs do torch 2.14 são
# bloqueadas por falta de assinatura/reputação; as do 2.8.0 carregam (testado em 2026-09-29).
pip install --index-url https://download.pytorch.org/whl/cpu "torch==2.8.0" "torchaudio==2.8.0"

echo "== Pacotes da ferramenta (PyPI)"
pip install "beat-this==1.1.0" "demucs==4.1.0" "librosa==0.11.0" soundfile mido onnxruntime
# basic-pitch exige TensorFlow no Python 3.11 fora do macOS; usamos só o backend ONNX:
pip install --no-deps "basic-pitch==0.4.0"
pip install resampy mir_eval pretty_midi scikit-learn scipy typing_extensions

pip freeze > /work/freeze-linux.txt

echo "== Onde o Beat This! e o Demucs buscam os pesos"
grep -rn -E "https?://[^\"' ]+" "$(python -c 'import beat_this,os;print(os.path.dirname(beat_this.__file__))')" | grep -vi "arxiv\|github.com/CPJKU/beat_this/blob" | head -20 || true
grep -rn -E "ROOT_URL|https?://[^\"' ]+\.th" "$(python -c 'import demucs,os;print(os.path.dirname(demucs.__file__))')" | head -10 || true

echo "== Teste de fumaça"
python /sandbox/smoke.py
