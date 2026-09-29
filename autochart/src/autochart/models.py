"""Pesos dos modelos: arquivos locais com SHA-256 fixado, carregados sem rede.

Os arquivos foram baixados pela primeira vez num contêiner isolado (sandbox/), onde os hashes
foram registrados (SECURITY_LOG.md). Aqui só aceitamos arquivos com exatamente esses hashes.
Para baixar numa máquina nova: scripts/baixar-modelos.ps1 (confere os mesmos hashes).
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class ModelFile:
    relpath: str
    sha256: str
    url: str


MODEL_FILES = {
    "beat_this": ModelFile(
        "beat_this/final0.ckpt",
        "8c328b45f59d8dd3dff219253ff6a8d6482be57d0133a29140e2febbf8eb8331",
        "https://cloud.cp.jku.at/public.php/dav/files/7ik4RrBKTS273gp/final0.ckpt",
    ),
    "htdemucs_6s": ModelFile(
        "demucs/htdemucs_6s-5c90dfd2.safetensors",
        "d2a1745f0744721f6b8ca5bf469b67c651ea5ed1b52998cab033b2158609d411",
        "https://huggingface.co/adefossez/HTDemucs-6s/resolve/3c5ee475be622df764938de97e4281a7b07ffa58/5c90dfd2.safetensors",
    ),
}

EXPECTED_DEMUCS_CLASS = "demucs.htdemucs.HTDemucs"


class ModelError(RuntimeError):
    pass


def models_dir() -> Path:
    env = os.environ.get("AUTOCHART_MODELS")
    if env:
        return Path(env)
    # autochart/src/autochart/models.py → raiz do repositório
    return Path(__file__).resolve().parents[3] / "models"


def go_offline() -> None:
    """Impede downloads implícitos e telemetria das bibliotecas (usamos só arquivos locais)."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ.setdefault("TORCH_HOME", str(models_dir() / "torch-home"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


@lru_cache(maxsize=None)
def verified_path(key: str) -> Path:
    spec = MODEL_FILES[key]
    path = models_dir() / spec.relpath
    if not path.is_file():
        raise ModelError(f"Modelo '{key}' não encontrado em {path}. Rode scripts\\baixar-modelos.ps1.")
    digest = _sha256(path)
    if digest != spec.sha256:
        raise ModelError(f"Hash do modelo '{key}' não confere ({digest}); arquivo recusado: {path}")
    return path


def load_beat_this(device: str = "cpu"):
    """Beat This! com o checkpoint local: o caminho local usa torch.load(weights_only=True)."""
    go_offline()
    from beat_this.inference import Audio2Beats
    return Audio2Beats(checkpoint_path=str(verified_path("beat_this")), device=device, dbn=False)


def load_beat_this_frames(device: str = "cpu"):
    """Beat This! devolvendo as ativações por quadro (50/s), para picos com precisão sub-quadro."""
    go_offline()
    from beat_this.inference import Audio2Frames
    return Audio2Frames(checkpoint_path=str(verified_path("beat_this")), device=device)


def load_htdemucs_6s():
    """Demucs htdemucs_6s a partir do safetensors local.

    O carregador do Demucs instancia a classe indicada nos metadados do arquivo; por isso, além
    do hash, exigimos que essa classe seja a HTDemucs antes de carregar.
    """
    go_offline()
    from safetensors import safe_open
    from demucs.apply import BagOfModels
    from demucs.hf import load_safetensors_model

    path = verified_path("htdemucs_6s")
    with safe_open(str(path), framework="pt") as f:
        klass = (f.metadata() or {}).get("klass")
    if klass != EXPECTED_DEMUCS_CLASS:
        raise ModelError(f"Classe inesperada nos metadados do Demucs: {klass!r}")
    model = load_safetensors_model(path)
    # Mesmo "bag" do htdemucs_6s.yaml oficial: models: ['5c90dfd2'] (sem pesos nem segmento).
    return BagOfModels([model], None, None)
