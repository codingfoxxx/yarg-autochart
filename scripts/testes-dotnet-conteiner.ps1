# Roda os testes .NET (engine do YARG.Core + código do fork sem Unity) num contêiner Linux
# oficial da Microsoft (mcr.microsoft.com/dotnet/sdk:10.0).
#
# Por quê: com o Smart App Control ligado, o Windows bloqueia as DLLs de teste recém-compiladas
# (sem assinatura e sem reputação), então "dotnet test" no Windows falha ao carregá-las.
# No contêiner o código roda isolado, sem tocar nessa proteção do Windows.
#
# Uso:  scripts\testes-dotnet-conteiner.ps1 [-Filtro "FullyQualifiedName~AnalogTrigger"]
param(
    [string]$Filtro = ""
)
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
$imagem = 'mcr.microsoft.com/dotnet/sdk:10.0@sha256:35d40304542c8689331f8cab17c65926cdf48fe711e289321d71924b230a7d29'

$filtroArg = if ($Filtro) { "--filter '$Filtro'" } else { "" }
$script = @"
set -e
mkdir -p /work/tests /work/YARG/YARG.Core /work/YARG/Assets/Script/Input/Bindings
cp -r /src/tests/EngineTests /work/tests/
cp -r /src/YARG/YARG.Core/YARG.Core /work/YARG/YARG.Core/
cp /src/YARG/YARG.Core/Directory.Build.props /work/YARG/YARG.Core/ 2>/dev/null || true
cp /src/YARG/Assets/Script/Input/Bindings/AnalogButtonHysteresis.cs /work/YARG/Assets/Script/Input/Bindings/
find /work -type d \( -name bin -o -name obj \) -prune -exec rm -r {} +
cd /work
dotnet test tests/EngineTests --nologo $filtroArg --logger 'console;verbosity=normal'
"@

docker run --rm `
    -v "${raiz}:/src:ro" `
    -v guitarhero-nuget:/root/.nuget/packages `
    -e DOTNET_CLI_TELEMETRY_OPTOUT=1 -e DOTNET_NOLOGO=1 `
    $imagem bash -c ($script -replace "`r", "")
exit $LASTEXITCODE
