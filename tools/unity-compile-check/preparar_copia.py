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
import os
import re
import shutil
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET
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


# Pastas do NuGet por ordem de preferência para o perfil .NET Framework do projeto (apiCompatibilityLevel 3),
# parecido com a escolha do NuGetForUnity.
_TFMS = ["net48", "net472", "net471", "net47", "net462", "net461", "net46", "net45",
         "netstandard2.1", "netstandard2.0", "netstandard1.6", "netstandard1.4"]
_META_PLUGIN = """fileFormatVersion: 2
guid: {guid}
PluginImporter:
  externalObjects: {{}}
  serializedVersion: 3
  iconMap: {{}}
  executionOrder: {{}}
  defineConstraints: []
  isPreloaded: 0
  isOverridable: 0
  isExplicitlyReferenced: {explicit}
  validateReferences: 1
  platformData:
  - first:
      Any:
    second:
      enabled: 1
      settings: {{}}
  userData:
  assetBundleName:
  assetBundleVariant:
"""


def restaurar_nuget(fork: Path) -> None:
    """Restaura os pacotes do Assets/packages.config (versões exatas) com o SDK .NET portátil e os
    coloca em Assets/Packages da cópia, no formato do NuGetForUnity."""
    pacotes = [(p.get("id"), p.get("version"))
               for p in ET.parse(fork / "Assets" / "packages.config").getroot().findall("package")
               if p.get("id") not in ("NETStandard.Library", "Microsoft.NETCore.Platforms")]
    trabalho = RAIZ / "_work" / "nuget-restore"
    trabalho.mkdir(parents=True, exist_ok=True)
    refs = "\n".join(f'    <PackageReference Include="{i}" Version="[{v}]" />' for i, v in pacotes)
    (trabalho / "restore.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk">\n  <PropertyGroup>\n    <TargetFramework>netstandard2.1</TargetFramework>\n'
        f'  </PropertyGroup>\n  <ItemGroup>\n{refs}\n  </ItemGroup>\n</Project>\n', encoding="utf-8")
    cache = RAIZ / "_tools" / "nuget-packages"
    env = dict(os.environ, DOTNET_ROOT=str(RAIZ / "_tools" / "dotnet"), NUGET_PACKAGES=str(cache),
               DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_NOLOGO="1")
    subprocess.run([str(RAIZ / "_tools" / "dotnet" / "dotnet.exe"), "restore", str(trabalho / "restore.csproj"), "-v", "q"],
                   env=env, check=True)
    destino = PROJETO / "Assets" / "Packages"
    for pid, ver in pacotes:
        raiz_pkg = cache / pid.lower() / ver
        saida = destino / f"{pid}.{ver}"
        if (raiz_pkg / "content").exists():  # sqlite-net traz código-fonte, não DLL
            (saida / "content").mkdir(parents=True, exist_ok=True)
            for cs in (raiz_pkg / "content").glob("*.cs"):
                shutil.copy2(cs, saida / "content" / cs.name)
            continue
        lib = raiz_pkg / "lib"
        dlls, tfm = list(lib.glob("*.dll")), ""
        if not dlls:
            tfm = next(t for t in _TFMS if (lib / t).exists())
            dlls = list((lib / tfm).glob("*.dll"))
        alvo = saida / "lib" / tfm
        alvo.mkdir(parents=True, exist_ok=True)
        for dll in dlls:
            shutil.copy2(dll, alvo / dll.name)
            (alvo / (dll.name + ".meta")).write_text(
                _META_PLUGIN.format(guid=uuid.uuid4().hex, explicit=1 if dll.name in EXPLICITAS else 0),
                encoding="utf-8", newline="\n")
        print(f"NuGet: {pid} {ver} ({tfm or 'lib'})")


def main() -> None:
    if "--nuget" in sys.argv:
        restaurar_nuget(RAIZ / "YARG")
        return
    dags = sorted((PROJETO / "Library" / "Bee").glob("*.dag.json"), key=lambda p: p.stat().st_mtime)
    nos = json.loads(dags[-1].read_text(encoding="utf-8"))["Nodes"]
    saida = next(n["Outputs"][0] for n in nos if n.get("Annotation", "").startswith("Csc "))
    dag_dir = PROJETO / Path(saida).parent
    injetar_nuget(dag_dir)
    remendos_de_versao()
    remendos_codigo_do_jogo()


if __name__ == "__main__":
    main()
