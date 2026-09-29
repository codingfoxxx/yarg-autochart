"""Validação com o próprio YARG.Core (tools/validator), chamada ao fim de cada geração.

O validador roda o scanner de músicas do jogo, carrega o chart com o parser do jogo e toca cada
dificuldade na engine de 5 trastes com jogadores simulados. Aqui também conferimos, nota a nota,
se o tipo que o YARG enxerga (palhetada/HOPO/tap) é o que o gerador pretendia.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from .chart import final_types
from .model import Note

_ROOT = Path(__file__).resolve().parents[3]
_TYPE_CODE = {"strum": "S", "hopo": "H", "tap": "T"}


def _dotnet() -> str | None:
    local = _ROOT / "_tools" / "dotnet" / "dotnet.exe"
    if local.is_file():
        return str(local)
    return shutil.which("dotnet")


def validate_with_yarg(folder: Path, diffs: dict[str, list[Note]], resolution: int,
                       timeout: int = 900) -> dict | None:
    """Devolve um resumo, ou None se o .NET/validador não estiverem disponíveis."""
    dotnet = _dotnet()
    project = _ROOT / "tools" / "validator"
    if not dotnet or not (project / "Validator.csproj").is_file():
        return None
    out_json = folder / "validacao-yarg.json"
    env = dict(os.environ)
    env.update({
        "YARG_VALIDAR_PASTA": str(folder),
        "YARG_VALIDAR_JSON": str(out_json),
        "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
        "DOTNET_NOLOGO": "1",
        "NUGET_PACKAGES": str(_ROOT / "_tools" / "nuget-packages"),
    })
    if Path(dotnet).parent.name == "dotnet":
        env["DOTNET_ROOT"] = str(Path(dotnet).parent)
    if out_json.exists():
        out_json.unlink()
    proc = subprocess.run([dotnet, "test", str(project), "--nologo", "-v", "q"], env=env,
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if not out_json.is_file():
        tail = "\n".join((proc.stdout + proc.stderr).strip().splitlines()[-15:])
        return {"ok": False, "erro": f"o validador não gerou resultado:\n{tail}"}

    data = json.loads(out_json.read_text(encoding="utf-8"))
    summary: dict = {"ok": bool(data.get("ok")), "rejeitada": data.get("rejeitadas") or ""}
    songs = data.get("musicas") or []
    if not songs:
        summary["ok"] = False
        summary["erro"] = "a música não foi encontrada pelo scanner do YARG"
        return summary
    song = songs[0]
    summary["dificuldades_no_jogo"] = song.get("dificuldades", [])
    per = {}
    for name, info in (song.get("por_dificuldade") or {}).items():
        sims = info.get("simulacao", {})
        expected = "".join(_TYPE_CODE[t] for t in final_types(diffs.get(name, []), resolution))
        per[name] = {
            "notas": info.get("notas"),
            "tipos_conferem": info.get("tipos") == expected,
            "perfeito_pct": sims.get("perfeito", {}).get("acertos_pct"),
            "humano_20ms_pct": sims.get("humano_20ms", {}).get("acertos_pct"),
            "humano_35ms_pct": sims.get("humano_35ms", {}).get("acertos_pct"),
            "estrelas_humano_35ms": sims.get("humano_35ms", {}).get("estrelas"),
        }
        if not per[name]["tipos_conferem"]:
            summary["ok"] = False
    summary["por_dificuldade"] = per
    return summary
