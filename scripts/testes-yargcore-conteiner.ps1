# Roda a suíte oficial de testes do YARG.Core (YARG.Core.UnitTests) num contêiner Linux oficial da
# Microsoft, a partir da cópia de trabalho do submódulo. Ver testes-dotnet-conteiner.ps1 para o motivo.
#
# Uso:  scripts\testes-yargcore-conteiner.ps1 [-Filtro "FullyQualifiedName~Guitar"]
param(
    [string]$Filtro = ""
)
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
$imagem = 'mcr.microsoft.com/dotnet/sdk:10.0@sha256:35d40304542c8689331f8cab17c65926cdf48fe711e289321d71924b230a7d29'

$filtroArg = if ($Filtro) { "--filter '$Filtro'" } else { "" }
$script = @"
set -e
mkdir -p /work
cp -r /src/YARG/YARG.Core /work/
find /work -type d \( -name bin -o -name obj \) -prune -exec rm -r {} +
cd /work/YARG.Core
dotnet test YARG.Core.UnitTests/YARG.Core.UnitTests.csproj --nologo $filtroArg --logger 'console;verbosity=minimal'
"@

docker run --rm `
    -v "${raiz}:/src:ro" `
    -v guitarhero-nuget:/root/.nuget/packages `
    -e DOTNET_CLI_TELEMETRY_OPTOUT=1 -e DOTNET_NOLOGO=1 `
    $imagem bash -c ($script -replace "`r", "")
exit $LASTEXITCODE
