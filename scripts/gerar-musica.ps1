# Gera uma música para o YARG a partir de um arquivo de áudio.
#   .\gerar-musica.ps1 "C:\Músicas\minha música.mp3" [-Titulo "..."] [-Artista "..."] [-Saida "C:\...\songs"]
# Também é chamado pelo gerar-musica.bat quando você arrasta um áudio em cima dele.
param(
    [Parameter(Mandatory = $true, Position = 0)] [string] $Audio,
    [string] $Titulo,
    [string] $Artista,
    [string] $Saida,
    [switch] $SemPerguntas
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $py)) {
    Write-Host "Ambiente Python não encontrado. Rode primeiro: scripts\preparar-ambiente.ps1" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path -LiteralPath $Audio)) {
    Write-Host "Arquivo não encontrado: $Audio" -ForegroundColor Red
    exit 1
}
$nome = [IO.Path]::GetFileNameWithoutExtension($Audio)
if (-not $SemPerguntas) {
    if (-not $Titulo) { $Titulo = Read-Host "Nome da música [$nome]" }
    if (-not $Artista) { $Artista = Read-Host "Artista [Desconhecido]" }
}
if (-not $Titulo) { $Titulo = $nome }
if (-not $Artista) { $Artista = 'Desconhecido' }

. (Join-Path $PSScriptRoot 'dev-env.ps1')
$cliArgs = @('-m', 'autochart', 'gerar', $Audio, '--titulo', $Titulo, '--artista', $Artista)
if ($Saida) { $cliArgs += @('--saida', $Saida) }
& $py @cliArgs
$code = $LASTEXITCODE
Write-Host ""
if ($code -eq 0) {
    Write-Host "Pronto! No YARG: Configurações > Song Manager > Refresh All Caches (músicas novas só aparecem depois disso)." -ForegroundColor Green
} else {
    Write-Host "A geração terminou com avisos ou erros (código $code). Veja o relatorio.md na pasta da música." -ForegroundColor Yellow
}
exit $code
