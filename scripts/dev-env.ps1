# Carrega o ambiente de desenvolvimento do projeto na sessão atual do PowerShell:
#   . C:\Dev\GuitarHero\scripts\dev-env.ps1
# Usa o .NET SDK portátil de _tools\dotnet (instalado pelo projeto) e guarda os pacotes
# NuGet dentro da pasta do projeto.
$root = Split-Path -Parent $PSScriptRoot
$env:DOTNET_ROOT = Join-Path $root '_tools\dotnet'
if (-not ($env:PATH -split ';' | Where-Object { $_ -eq $env:DOTNET_ROOT })) {
    $env:PATH = "$env:DOTNET_ROOT;$env:PATH"
}
$env:DOTNET_CLI_TELEMETRY_OPTOUT = '1'
$env:DOTNET_NOLOGO = '1'
$env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE = '1'
$env:NUGET_PACKAGES = Join-Path $root '_tools\nuget-packages'
