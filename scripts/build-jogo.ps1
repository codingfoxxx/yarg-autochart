# Compila o fork do YARG (Windows, Mono) pela linha de comando do Unity.
#
# Uso:  scripts\build-jogo.ps1 [-Saida C:\Dev\GuitarHero\_builds\YARG] [-Versao 6000.3.5f2]
#
# Antes: Unity 6000.3.5f2 instalado pelo Hub, Hub aberto (a licença vem dele), Blender instalado
# (sem ele alguns modelos de nota ficam sem malha, mas o build sai). A primeira vez importa o
# projeto inteiro (pasta Library, 5-8 GB) e pode levar de 30 a 60 minutos.
param(
    [string]$Saida = (Join-Path (Split-Path -Parent $PSScriptRoot) '_builds\YARG'),
    [string]$Versao = '6000.3.5f2',
    [int]$DiscoMinimoGB = 12
)
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
$projeto = Join-Path $raiz 'YARG'
$unity = "C:\Program Files\Unity\Hub\Editor\$Versao\Editor\Unity.exe"

function Livre { [math]::Round((Get-PSDrive C).Free / 1GB, 1) }

# --- pré-requisitos ---
if (Test-Path (Join-Path $raiz '_work\PROBLEMA-PC.txt')) { throw "Existe _work\PROBLEMA-PC.txt: resolva antes de compilar." }
if (-not (Test-Path $unity)) { throw "Unity $Versao não encontrado em $unity. Instale pelo Hub: unityhub://6000.3.5f2/3fa8bc678cb0" }
if (-not (Get-Process -Name 'Unity Hub' -ErrorAction SilentlyContinue)) { Write-Warning "O Unity Hub não está aberto: sem ele o editor pode não achar a licença." }
if ((Livre) -lt $DiscoMinimoGB) { throw "Só $(Livre) GB livres; o primeiro build precisa de ~$DiscoMinimoGB GB." }
$blender = Get-ChildItem 'C:\Program Files\Blender Foundation' -Filter blender.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $blender) { Write-Warning "Blender não encontrado: os modelos .blend (notas 'Rectangular') ficarão sem malha." }

New-Item -ItemType Directory -Force $Saida | Out-Null
$exe = Join-Path $Saida 'YARG.exe'

function Rodar-Unity([string]$log) {
    $argumentos = @('-batchmode', '-quit', '-projectPath', $projeto, '-buildTarget', 'Win64',
              '-buildWindows64Player', $exe, '-logFile', $log)
    $inicio = Get-Date
    $p = Start-Process -FilePath $unity -ArgumentList $argumentos -PassThru -WindowStyle Hidden
    while (-not $p.HasExited) {
        if ((Livre) -lt 3) {
            Stop-Process -Id $p.Id -Force
            throw "Disco abaixo de 3 GB durante o build; interrompido."
        }
        Start-Sleep -Seconds 20
        $min = [int]((Get-Date) - $inicio).TotalMinutes
        Write-Host ("  {0} min, disco livre {1} GB" -f $min, (Livre))
    }
    return @{ Codigo = $p.ExitCode; Inicio = $inicio }
}

# Pacotes NuGet (Assets/Packages, fora do git). Quem os restaura é o NuGetForUnity, mas em modo batch ele
# não chega a rodar enquanto houver erro de compilação por falta deles. Restaura antes, nas versões exatas
# do packages.config, com o SDK .NET portátil (os .meta ficam por conta do editor).
if (-not (Test-Path (Join-Path $projeto 'Assets\Packages\ZString.2.5.1'))) {
    Write-Host "Restaurando os pacotes NuGet do jogo..."
    & (Join-Path $raiz '.venv\Scripts\python.exe') (Join-Path $raiz 'tools\unity-compile-check\preparar_copia.py') --nuget-no-fork
    if ($LASTEXITCODE -ne 0) { throw "Falha ao restaurar os pacotes NuGet" }
}

Write-Host "Compilando $projeto com Unity $Versao -> $exe"
$log1 = Join-Path $Saida 'build.log'
$r = Rodar-Unity $log1
$texto = Get-Content $log1 -Raw -ErrorAction SilentlyContinue

# --- resultado ---
$erros = [regex]::Matches($texto, 'error CS\d+[^\r\n]*') | ForEach-Object { $_.Value } | Select-Object -Unique -First 20
$bloqueios = Get-WinEvent -LogName 'Microsoft-Windows-CodeIntegrity/Operational' -ErrorAction SilentlyContinue |
    Where-Object { $_.Id -eq 3077 -and $_.TimeCreated -ge $r.Inicio } |
    ForEach-Object { if ($_.Message -match 'attempted to load (.+?) that') { ($Matches[1] -replace '^.*\\', '') } } |
    Group-Object | Sort-Object Count -Descending

Write-Host ""
if ($r.Codigo -eq 0 -and (Test-Path $exe)) {
    Write-Host "Build OK: $exe" -ForegroundColor Green
} else {
    Write-Host "Build falhou (código $($r.Codigo)). Log: $log1" -ForegroundColor Red
}
if ($erros) { Write-Host "Erros de C#:"; $erros | ForEach-Object { Write-Host "  $_" } }
if ($bloqueios) {
    Write-Host "O Smart App Control bloqueou arquivos durante o build:" -ForegroundColor Yellow
    $bloqueios | ForEach-Object { Write-Host ("  {0}x {1}" -f $_.Count, $_.Name) }
    Write-Host "Ver PROGRESS.md (decisão sobre o Smart App Control)."
}
exit $r.Codigo
