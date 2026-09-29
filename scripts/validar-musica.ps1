# Valida uma pasta de música (ou a biblioteca inteira) com o próprio YARG.Core:
# scanner de músicas do jogo, leitura do chart e partida simulada na engine de 5 trastes.
#   .\validar-musica.ps1 "C:\Dev\GuitarHero\songs\Artista - Música"
param([Parameter(Mandatory = $true, Position = 0)] [string] $Pasta, [string] $Json)
$root = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'dev-env.ps1')
$env:YARG_VALIDAR_PASTA = (Resolve-Path -LiteralPath $Pasta).Path
if ($Json) { $env:YARG_VALIDAR_JSON = $Json } else { Remove-Item Env:YARG_VALIDAR_JSON -ErrorAction SilentlyContinue }
# Roda via "dotnet test": com o Smart App Control do Windows ativo, o validador só carrega como
# dependência de um hospedeiro assinado pela Microsoft (ver tools\validator\Validator.csproj).
dotnet test (Join-Path $root 'tools\validator') --nologo --logger "console;verbosity=detailed" |
    Where-Object { $_ -match '^\s{2,}\S' -and $_ -notmatch 'Test run|Iniciando|Starting' }
exit $LASTEXITCODE
