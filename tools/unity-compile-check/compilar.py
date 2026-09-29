"""Verificação de compilação dos scripts do YARG sem o editor do Unity.

Por quê: com o Smart App Control ligado, o editor do Unity não consegue compilar
(o Windows bloqueia ferramentas .NET sem assinatura do próprio Unity, como o
ApiUpdater.MovedFromExtractor). O compilador C# que o Unity usa (Roslyn, dentro do
SDK .NET que vem com o editor) é assinado pela Microsoft e roda normalmente.

Como funciona: o editor, antes de falhar, grava o grafo de build (Library/Bee/*.dag.json)
com a linha de comando exata de cada compilação ("Csc ..."). Este script executa só
esses nós, na ordem das dependências, e mostra os erros. As outras etapas do grafo
(MovedFromExtractor, ILPostProcess, cópias) não são necessárias para saber se o código
compila e não são executadas.

Uso:
  python compilar.py [--projeto PASTA] [--sincronizar-de PASTA_DO_FORK] [--alvo Assembly-CSharp]

--sincronizar-de copia Assets/Script, Assets/Editor, Assets/Plugins e Assets/VLCUnity do fork
para a cópia do projeto antes de compilar (a cópia é criada uma vez pelo editor em modo batch).
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

PASTAS_SINCRONIZADAS = ("Script", "Editor", "Plugins", "VLCUnity")
ERRO = re.compile(r"\berror CS\d+")
AVISO = re.compile(r"\bwarning CS\d+")


def sincronizar(fork: Path, projeto: Path) -> list[str]:
    """Espelha as pastas de código do fork na cópia; devolve os .cs novos em Assets/Script."""
    novos = []
    for nome in PASTAS_SINCRONIZADAS:
        origem, destino = fork / "Assets" / nome, projeto / "Assets" / nome
        antes = {p.relative_to(destino).as_posix() for p in destino.rglob("*.cs")} if destino.exists() else set()
        for arq in origem.rglob("*"):
            if arq.is_dir():
                continue
            alvo = destino / arq.relative_to(origem)
            if not alvo.exists() or alvo.stat().st_mtime < arq.stat().st_mtime or alvo.stat().st_size != arq.stat().st_size:
                alvo.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(arq, alvo)
        for arq in list(destino.rglob("*")):
            if arq.is_file() and not (origem / arq.relative_to(destino)).exists():
                arq.unlink()
        if nome == "Script":
            depois = {p.relative_to(destino).as_posix() for p in destino.rglob("*.cs")}
            novos = sorted(depois - antes)
    return novos


def ajustar_fontes(projeto: Path, rsp: Path) -> tuple[int, int]:
    """Atualiza a lista de fontes de Assets/Script no .rsp do Assembly-CSharp (arquivos novos/removidos)."""
    linhas = rsp.read_text(encoding="utf-8").splitlines()
    fontes = {l.strip('"') for l in linhas if l.strip('"').startswith("Assets/Script/") and l.endswith('.cs"')}
    atuais = {
        p.relative_to(projeto).as_posix()
        for p in (projeto / "Assets" / "Script").rglob("*.cs")
        if "/Editor/" not in p.relative_to(projeto).as_posix()
    }
    novos, removidos = atuais - fontes, fontes - atuais
    if novos or removidos:
        linhas = [l for l in linhas if l.strip('"') not in removidos]
        linhas += [f'"{f}"' for f in sorted(novos)]
        rsp.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return len(novos), len(removidos)


def carregar_nos(projeto: Path) -> list[dict]:
    dags = sorted((projeto / "Library" / "Bee").glob("*.dag.json"), key=lambda p: p.stat().st_mtime)
    if not dags:
        sys.exit("Nenhum grafo do Bee encontrado: rode o editor em modo batch uma vez nesta cópia.")
    nos = json.loads(dags[-1].read_text(encoding="utf-8"))["Nodes"]
    csc = [n for n in nos if n.get("Annotation", "").startswith("Csc ")]
    produtor = {}
    for i, n in enumerate(csc):
        for o in n.get("Outputs", []):
            produtor[o] = i
    for i, n in enumerate(csc):
        n["_nome"] = re.search(r"/([^/]+)\.dll", n["Annotation"]).group(1)
        n["_deps"] = sorted({produtor[x] for x in n.get("Inputs", []) if x in produtor and produtor[x] != i})
    return csc


def fechamento(csc: list[dict], alvo: str | None) -> set[int]:
    if not alvo:
        return set(range(len(csc)))
    inicio = [i for i, n in enumerate(csc) if n["_nome"] == alvo]
    if not inicio:
        sys.exit(f"Assembly {alvo} não está no grafo.")
    visto, pilha = set(), inicio[:]
    while pilha:
        i = pilha.pop()
        if i in visto:
            continue
        visto.add(i)
        pilha.extend(csc[i]["_deps"])
    return visto


def atualizado(projeto: Path, n: dict) -> bool:
    saidas = [projeto / o for o in n["Outputs"]]
    if not all(s.exists() for s in saidas):
        return False
    t_saida = min(s.stat().st_mtime for s in saidas)
    for x in n["Inputs"]:
        p = Path(x) if os.path.isabs(x) else projeto / x
        if p.exists() and p.stat().st_mtime > t_saida:
            return False
    return True


def compilar(projeto: Path, n: dict) -> tuple[int, str]:
    for o in n["Outputs"]:
        (projeto / o).parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(n["Action"], cwd=projeto, shell=True, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def main() -> int:
    ap = argparse.ArgumentParser()
    raiz = Path(__file__).resolve().parents[2]
    ap.add_argument("--projeto", type=Path, default=raiz / "_work" / "unity-compilecheck")
    ap.add_argument("--sincronizar-de", type=Path)
    ap.add_argument("--alvo", default="Assembly-CSharp", help="assembly final (vazio = todas)")
    ap.add_argument("--paralelo", type=int, default=6)
    ap.add_argument("--mostrar-avisos", action="store_true")
    a = ap.parse_args()
    projeto = a.projeto.resolve()

    if a.sincronizar_de:
        novos = sincronizar(a.sincronizar_de.resolve(), projeto)
        if novos:
            print("arquivos novos em Assets/Script:", ", ".join(novos))
        sys.path.insert(0, str(Path(__file__).parent))
        import preparar_copia  # noqa: E402 (remendos de versão que a sincronização desfaz)
        preparar_copia.remendos_codigo_do_jogo()
    csc = carregar_nos(projeto)
    rsp = projeto / "Library/Bee/artifacts" / Path(csc[0]["Outputs"][0]).parent.name / "Assembly-CSharp.rsp"
    if rsp.exists():
        n_novos, n_rem = ajustar_fontes(projeto, rsp)
        if n_novos or n_rem:
            print(f"lista de fontes do Assembly-CSharp ajustada: +{n_novos} -{n_rem}")

    alvo = fechamento(csc, a.alvo or None)
    pendentes = {i for i in alvo if not atualizado(projeto, csc[i])}
    # quem depende de algo que vai recompilar também recompila
    mudou = True
    while mudou:
        mudou = False
        for i in alvo - pendentes:
            if any(d in pendentes for d in csc[i]["_deps"]):
                pendentes.add(i)
                mudou = True
    print(f"{len(alvo)} assemblies no alvo, {len(pendentes)} para compilar")

    feitos, falhas, erros_total = set(i for i in alvo if i not in pendentes), {}, 0
    t0 = time.time()
    with cf.ThreadPoolExecutor(max_workers=a.paralelo) as ex:
        rodando = {}
        while pendentes or rodando:
            prontos = [i for i in pendentes if all(d in feitos for d in csc[i]["_deps"] if d in alvo)]
            bloqueados = [i for i in pendentes if any(d in falhas for d in csc[i]["_deps"])]
            for i in bloqueados:
                pendentes.discard(i)
                falhas[i] = "dependência falhou"
            for i in prontos:
                pendentes.discard(i)
                rodando[ex.submit(compilar, projeto, csc[i])] = i
            if not rodando:
                break
            pronto, _ = cf.wait(rodando, return_when=cf.FIRST_COMPLETED)
            for f in pronto:
                i = rodando.pop(f)
                codigo, saida = f.result()
                erros = [l for l in saida.splitlines() if ERRO.search(l)]
                avisos = [l for l in saida.splitlines() if AVISO.search(l)]
                if codigo != 0 or erros:
                    falhas[i] = saida
                    erros_total += len(erros)
                    print(f"FALHOU  {csc[i]['_nome']}: {len(erros)} erro(s)")
                    for l in (erros or saida.splitlines())[:40]:
                        print("   ", l.strip()[:400])
                else:
                    feitos.add(i)
                    extra = f", {len(avisos)} aviso(s)" if avisos else ""
                    print(f"ok      {csc[i]['_nome']}{extra}")
                    if a.mostrar_avisos:
                        for l in avisos[:60]:
                            print("   ", l.strip()[:400])
    print(f"\n{len(feitos)} ok, {len(falhas)} com falha, {erros_total} erro(s), {time.time() - t0:.0f} s")
    return 0 if not falhas else 1


if __name__ == "__main__":
    sys.exit(main())
