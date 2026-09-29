#!/usr/bin/env bash
# Roda DENTRO do contêiner descartável. Produz em /work/wheels-win os arquivos EXATOS que o
# PC (Windows, CPython 3.11, 64 bits) vai instalar, e em /work/requirements-win.lock os hashes.
# Pacotes que só existem como código-fonte são compilados AQUI (o setup.py deles nunca roda no PC).
set -euo pipefail
export PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
OUT=/work/wheels-win
rm -rf "$OUT" && mkdir -p "$OUT"

# Versões: as mesmas resolvidas no teste de fumaça (freeze-linux.txt), sem o sufixo +cpu
# (no Windows o wheel do PyPI já é só CPU), mais colorama (dependência do tqdm/click no Windows).
sed -e 's/+cpu//' /work/freeze-linux.txt | grep -v '^#' > /work/req-win.txt
echo "colorama==0.4.6" >> /work/req-win.txt

WIN_FLAGS=(--platform win_amd64 --python-version 3.11 --implementation cp --abi cp311 --abi abi3 --abi none)
: > /work/sdist-only.txt
while read -r req; do
  [ -z "$req" ] && continue
  if ! pip download --no-deps --only-binary=:all: "${WIN_FLAGS[@]}" -d "$OUT" "$req" -q 2>/dev/null; then
    echo "$req" >> /work/sdist-only.txt
  fi
done < /work/req-win.txt

echo "== Só código-fonte (compilados aqui, puros Python):"
cat /work/sdist-only.txt
while read -r req; do
  [ -z "$req" ] && continue
  pip wheel --no-deps -w "$OUT" "$req" -q
done < /work/sdist-only.txt

# Wheels compilados aqui têm que ser universais (py3-none-any), senão não servem no Windows.
if ls "$OUT"/*linux*.whl >/dev/null 2>&1; then
  echo "ERRO: wheel específico de Linux no conjunto do Windows:"; ls "$OUT"/*linux*.whl; exit 1
fi

cd "$OUT"
python - <<'PY' > /work/requirements-win.lock
import hashlib, pathlib, re
print("# Gerado por sandbox/wheels-win.sh (contêiner isolado). Instalar com:")
print("#   pip install --no-index --find-links <wheels-win> --require-hashes --no-deps -r requirements-win.lock")
for whl in sorted(pathlib.Path(".").glob("*.whl")):
    name, version = whl.name.split("-")[:2]
    digest = hashlib.sha256(whl.read_bytes()).hexdigest()
    print(f"{name.replace('_', '-').lower()}=={version} --hash=sha256:{digest}")
PY
echo "== $(ls "$OUT" | wc -l) wheels, $(du -sh "$OUT" | cut -f1)"
