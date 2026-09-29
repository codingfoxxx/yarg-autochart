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


# Imagem oficial do SDK .NET (fixada por digest) para rodar o validador fora do Windows.
_IMAGEM_DOTNET = ("mcr.microsoft.com/dotnet/sdk:10.0@sha256:"
                  "35d40304542c8689331f8cab17c65926cdf48fe711e289321d71924b230a7d29")
# Sinais de que o Windows (Smart App Control / Controle de Aplicativo) barrou a DLL do validador.
_SINAIS_DE_BLOQUEIO = ("Failed to load the test assembly", "0x800711C7",
                       "Controle de Aplicativo", "Application Control policy")


def _bloqueado_pelo_windows(saida: str) -> bool:
    return any(s in saida for s in _SINAIS_DE_BLOQUEIO)


def _validar_no_conteiner(folder: Path, out_json: Path, timeout: int) -> str | None:
    """Roda o mesmo validador num contêiner Linux. Devolve None se deu certo, senão o motivo."""
    docker = shutil.which("docker")
    if not docker:
        return "Docker não encontrado"
    if subprocess.run([docker, "info"], capture_output=True, timeout=60).returncode != 0:
        return "Docker Desktop não está rodando"
    script = (
        "set -e; mkdir -p /work/tools /work/tests/EngineTests /work/YARG/YARG.Core; "
        "cp -r /src/tools/validator /work/tools/; "
        "cp /src/tests/EngineTests/Harness.cs /work/tests/EngineTests/; "
        "cp -r /src/YARG/YARG.Core/YARG.Core /work/YARG/YARG.Core/; "
        "cp /src/YARG/YARG.Core/Directory.Build.props /work/YARG/YARG.Core/ 2>/dev/null || true; "
        "find /work -type d \\( -name bin -o -name obj \\) -prune -exec rm -r {} +; "
        "dotnet test /work/tools/validator --nologo -v q"
    )
    musica = f"/musica/{folder.name}"
    cmd = [docker, "run", "--rm",
           "-v", f"{_ROOT}:/src:ro",
           "-v", f"{folder}:{musica}",
           "-v", "guitarhero-nuget:/root/.nuget/packages",
           "-e", f"YARG_VALIDAR_PASTA={musica}",
           "-e", f"YARG_VALIDAR_JSON={musica}/{out_json.name}",
           "-e", "DOTNET_CLI_TELEMETRY_OPTOUT=1", "-e", "DOTNET_NOLOGO=1",
           _IMAGEM_DOTNET, "bash", "-c", script]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if out_json.is_file():
        return None
    tail = "\n".join((proc.stdout + proc.stderr).strip().splitlines()[-10:])
    return f"o validador também falhou no contêiner:\n{tail}"


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
    onde = "Windows"
    if not out_json.is_file():
        saida = proc.stdout + proc.stderr
        if not _bloqueado_pelo_windows(saida):
            tail = "\n".join(saida.strip().splitlines()[-15:])
            return {"ok": False, "erro": f"o validador não gerou resultado:\n{tail}"}
        # O Smart App Control barra a DLL do validador recém-compilada: roda o mesmo código num contêiner.
        motivo = _validar_no_conteiner(folder, out_json, timeout)
        if motivo is not None:
            return {"ok": None, "indisponivel": "o Windows (Smart App Control) bloqueou o validador compilado "
                                                 f"nesta máquina e a alternativa em contêiner não rodou ({motivo})"}
        onde = "contêiner Linux (o Smart App Control bloqueou o validador no Windows)"

    data = json.loads(out_json.read_text(encoding="utf-8"))
    summary: dict = {"ok": bool(data.get("ok")), "rejeitada": data.get("rejeitadas") or "", "executado_em": onde}
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
