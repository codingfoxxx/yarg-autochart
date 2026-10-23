#!/bin/bash
# Compila o fork do YARG para macOS (Mono, universal) pela linha de comando do Unity.
#
# Uso:  scripts/build-jogo-mac.sh [saída] [versão]
#       saída padrão: _builds/YARG.app   versão padrão: 6000.3.5f2
#
# Antes: Unity 6000.3.5f2 em /Applications/Unity/Hub/Editor/<versão>, licença ativada pelo Unity Hub
# (login feito uma vez), git lfs pull no submódulo YARG e Blender em /Applications (sem ele alguns
# modelos de nota ficam sem malha, mas o build sai). A primeira vez importa o projeto inteiro
# (pasta Library, 5-8 GB).
set -euo pipefail

raiz="$(cd "$(dirname "$0")/.." && pwd)"
projeto="$raiz/YARG"
saida="${1:-$raiz/_builds/YARG.app}"
versao="${2:-6000.3.5f2}"
unity="/Applications/Unity/Hub/Editor/$versao/Unity.app/Contents/MacOS/Unity"
log="$(dirname "$saida")/build.log"

livre_gb() { df -g "$raiz" | awk 'NR==2 {print $4}'; }

# --- pré-requisitos ---
[ -x "$unity" ] || { echo "Unity $versao não encontrado em $unity" >&2; exit 1; }
[ -f "$HOME/Library/Unity/licenses/UnityEntitlementLicense.xml" ] || echo "Aviso: licença do Unity não encontrada; faça login no Unity Hub." >&2
[ "$(livre_gb)" -ge 12 ] || { echo "Só $(livre_gb) GB livres; o primeiro build precisa de ~12 GB." >&2; exit 1; }
[ -d /Applications/Blender.app ] || echo "Aviso: Blender não encontrado; os modelos .blend (notas 'Rectangular') ficarão sem malha." >&2
if head -c 40 "$projeto/Assets/Art/Meshes/Obsolete/Notes.blend" 2>/dev/null | grep -q git-lfs; then
    echo "Arquivos do LFS faltando: rode 'git lfs pull' em $projeto" >&2; exit 1
fi

# Pacotes NuGet (Assets/Packages, fora do git): em modo batch o NuGetForUnity não chega a restaurá-los
# (ver BUILD.md), então restaura antes com o SDK .NET portátil de _tools/dotnet.
if [ ! -d "$projeto/Assets/Packages/ZString.2.5.1" ]; then
    echo "Restaurando os pacotes NuGet do jogo..."
    python3 "$raiz/tools/unity-compile-check/preparar_copia.py" --nuget-no-fork
fi

mkdir -p "$(dirname "$saida")"
echo "Compilando $projeto com Unity $versao -> $saida (log: $log)"
inicio=$(date +%s)
"$unity" -batchmode -quit -projectPath "$projeto" -buildTarget OSXUniversal \
    -buildOSXUniversalPlayer "$saida" -logFile "$log" &
pid=$!
while kill -0 $pid 2>/dev/null; do
    if [ "$(livre_gb)" -lt 3 ]; then
        kill $pid; echo "Disco abaixo de 3 GB durante o build; interrompido." >&2; exit 1
    fi
    sleep 30
    echo "  $(( ($(date +%s) - inicio) / 60 )) min, disco livre $(livre_gb) GB"
done
codigo=0; wait $pid || codigo=$?

# --- resultado ---
echo
if [ $codigo -eq 0 ] && [ -d "$saida" ]; then
    echo "Build OK: $saida"
else
    echo "Build falhou (código $codigo). Log: $log" >&2
fi
erros=$(grep -o -E 'error CS[0-9]+[^\r]*' "$log" 2>/dev/null | sort -u | head -20 || true)
[ -n "$erros" ] && { echo "Erros de C#:"; echo "$erros" | sed 's/^/  /'; }
exit $codigo
