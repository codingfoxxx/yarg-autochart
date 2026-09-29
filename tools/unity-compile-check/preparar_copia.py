"""Ajusta a cópia só-de-scripts do projeto para o verificador de compilação (compilar.py).

Nada aqui toca no fork: só em _work/unity-compilecheck.

1. Referências do NuGet: o NuGetForUnity (que o editor rodaria) não chega a rodar, porque o
   editor não compila com o Smart App Control ligado. As DLLs são restauradas com o SDK .NET
   (versões exatas do Assets/packages.config) e colocadas em Assets/Packages; este script
   acrescenta "-r:" para elas nos .rsp das assemblies do projeto, como o Unity faria para DLLs
   com referência automática. As de referência explícita só entram onde o asmdef pede.
2. Diferenças de API do Unity instalado (6000.6) em relação ao do projeto (6000.3), só para
   o código de terceiros compilar: VRM10 (GetInstanceID virou erro) e SoftMaskForUGUI
   (ILayoutElement ganhou maxWidth/maxHeight).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PROJETO = RAIZ / "_work" / "unity-compilecheck"

# referência explícita (autoReferenced=false no packages.config) -> assemblies que pedem no asmdef
EXPLICITAS = {"Microsoft.IO.Redist.dll": set(), "Microsoft.VisualStudio.SolutionPersistence.dll": {"YARG.Editor.Submodules"}}


def assemblies_do_projeto(dag_dir: Path) -> list[Path]:
    """.rsp de assemblies com código em Assets/ ou no YARG.Core (não mexe nos pacotes do Unity)."""
    alvos = []
    for rsp in dag_dir.glob("*.rsp"):
        if rsp.name.endswith(".mvfrm.rsp"):
            continue
        texto = rsp.read_text(encoding="utf-8")
        if re.search(r'^"?(Assets[/\\]|YARG\.Core[/\\])', texto, re.M):
            alvos.append(rsp)
    return alvos


def injetar_nuget(dag_dir: Path) -> None:
    dlls = sorted((PROJETO / "Assets" / "Packages").glob("*/lib/**/*.dll"))
    for rsp in assemblies_do_projeto(dag_dir):
        nome = rsp.stem
        linhas = rsp.read_text(encoding="utf-8").splitlines()
        existentes = set(linhas)
        novas = []
        for dll in dlls:
            if dll.name in EXPLICITAS and nome not in EXPLICITAS[dll.name]:
                continue
            linha = f'-r:"{dll.relative_to(PROJETO).as_posix()}"'
            if linha not in existentes:
                novas.append(linha)
        if novas:
            # as referências vêm antes da lista de fontes
            i = max((k for k, l in enumerate(linhas) if l.startswith("-r:")), default=0) + 1
            linhas[i:i] = novas
            rsp.write_text("\n".join(linhas) + "\n", encoding="utf-8")
            print(f"{nome}: +{len(novas)} referência(s) do NuGet")


def remendar(caminho: Path, trocas: list[tuple[str, str]]) -> None:
    texto = caminho.read_text(encoding="utf-8-sig")
    novo = texto
    for antes, depois in trocas:
        if depois not in novo:
            novo = novo.replace(antes, depois)
    if novo != texto:
        caminho.write_text(novo, encoding="utf-8")
        print("remendado:", caminho.relative_to(PROJETO))


def remendos_de_versao() -> None:
    cache = PROJETO / "Library" / "PackageCache"
    for vrm in cache.glob("com.vrmc.vrm@*"):
        remendar(vrm / "Runtime/Components/Expression/MorphTargetBindingMerger/MorphTargetIdentifier.cs",
                 [("targetRenderer.GetInstanceID();", "targetRenderer.GetHashCode();")])
        remendar(vrm / "Runtime/Components/SpringBone/VRM10SpringBoneCollider.cs",
                 [("GetInstanceID() == SelectedGuid", "GetHashCode() == SelectedGuid")])
    for sm in cache.glob("com.coffee.softmask-for-ugui@*"):
        extra = "float ILayoutElement.minWidth => 0;"
        membros = "float ILayoutElement.maxWidth => -1;\n        float ILayoutElement.maxHeight => -1;\n        " + extra
        remendar(sm / "Runtime/RectTransformFitter.cs", [(extra, membros)])
        remendar(sm / "Runtime/MaskingShape/TerminalMaskingShape.cs", [(extra, membros)])
        # APIs marcadas como erro na 6000.6; o comportamento não importa, só a compilação
        for cs in sm.glob("Runtime/**/*.cs"):
            texto = cs.read_text(encoding="utf-8-sig")
            novo = texto.replace("GetInstanceID()", "GetHashCode()")
            novo = re.sub(r"\((\w+) as IMeshModifier\)\.ModifyMesh\([^;]*\);", "/* removido na cópia */", novo)
            if novo != texto:
                cs.write_text(novo, encoding="utf-8")
                print("remendado:", cs.relative_to(PROJETO))


def remendos_codigo_do_jogo() -> None:
    """Diferenças de versão de pacote no código do YARG (reaplicado depois de cada sincronização).

    O Unity 6000.6 troca o Cinemachine 2.10 do projeto pelo 6.6, que mudou o namespace.
    """
    remendar(PROJETO / "Assets/Script/Gameplay/BackgroundManager.cs",
             [("using Cinemachine;", "using Unity.Cinemachine;")])
    # Object.GetInstanceID() virou erro na 6000.6
    remendar(PROJETO / "Assets/Script/Helpers/Extensions/ImageExtensions.cs",
             [("GetInstanceID()", "GetHashCode()")])


def main() -> None:
    dags = sorted((PROJETO / "Library" / "Bee").glob("*.dag.json"), key=lambda p: p.stat().st_mtime)
    nos = json.loads(dags[-1].read_text(encoding="utf-8"))["Nodes"]
    saida = next(n["Outputs"][0] for n in nos if n.get("Annotation", "").startswith("Csc "))
    dag_dir = PROJETO / Path(saida).parent
    injetar_nuget(dag_dir)
    remendos_de_versao()
    remendos_codigo_do_jogo()


if __name__ == "__main__":
    main()
