# Cria o ambiente Python da ferramenta (.venv, Python 3.11) a partir do lock com hashes.
#
# Os wheels do Windows são gerados e conferidos num contêiner isolado (sandbox\wheels-win.sh) e
# ficam em _work\sandbox\wheels-win. Com essa pasta presente, a instalação é offline e só aceita
# arquivos com os hashes do lock. Sem ela, baixa do PyPI (mesmos hashes, --require-hashes).
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$lock = Join-Path $root 'autochart\requirements-win.lock'
$wheels = Join-Path $root '_work\sandbox\wheels-win'
$venv = Join-Path $root '.venv'

if (-not (Test-Path -LiteralPath $venv)) {
    py -3.11 -m venv $venv
}
$py = Join-Path $venv 'Scripts\python.exe'
if (Test-Path -LiteralPath $wheels) {
    & $py -m pip install --no-index --find-links $wheels --require-hashes --no-deps -r $lock
} else {
    & $py -m pip install --require-hashes --no-deps -r $lock
}
# O pacote autochart entra no venv por um .pth (sem precisar de build).
Set-Content -Path (Join-Path $venv 'Lib\site-packages\autochart-src.pth') -Value (Join-Path $root 'autochart\src') -Encoding ASCII
& $py -c "import autochart, torch; print('autochart', autochart.__version__, '| torch', torch.__version__)"
& (Join-Path $PSScriptRoot 'baixar-modelos.ps1')
