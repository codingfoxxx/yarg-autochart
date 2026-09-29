# Cria (ou recria) a cópia só-de-scripts do fork usada por compilar.py. Ver README.md.
#
# Uso:  tools\unity-compile-check\criar_copia.ps1 [-Versao 6000.6.3f1]
# Leva ~5 min. O editor do Unity roda uma vez em modo batch só para gravar o grafo de build;
# com o Smart App Control ligado ele termina com "Scripts have compiler errors", o que é esperado.
param([string]$Versao = '6000.6.3f1')
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$fork = Join-Path $raiz 'YARG'
$copia = Join-Path $raiz '_work\unity-compilecheck'
$unity = "C:\Program Files\Unity\Hub\Editor\$Versao\Editor\Unity.exe"
$py = Join-Path $raiz '.venv\Scripts\python.exe'
if (-not (Test-Path $unity)) { throw "Unity $Versao não encontrado em $unity" }

New-Item -ItemType Directory -Force "$copia\Assets", "$copia\Packages", "$copia\YARG.Core" | Out-Null
foreach ($d in 'Script', 'Plugins', 'Editor', 'VLCUnity') {
    robocopy "$fork\Assets\$d" "$copia\Assets\$d" /MIR /NFL /NDL /NJH /NJS /NP | Out-Null
    Copy-Item "$fork\Assets\$d.meta" "$copia\Assets\" -Force
}
foreach ($f in 'packages.config', 'packages.config.meta', 'NuGet.config', 'NuGet.config.meta',
               'YargInput.inputactions', 'YargInput.inputactions.meta', 'Packages.meta') {
    Copy-Item "$fork\Assets\$f" "$copia\Assets\" -Force
}
robocopy "$fork\ProjectSettings" "$copia\ProjectSettings" /MIR /NFL /NDL /NJH /NJS /NP | Out-Null
Copy-Item "$fork\Packages\manifest.json", "$fork\Packages\packages-lock.json" "$copia\Packages\" -Force
robocopy "$fork\YARG.Core\YARG.Core" "$copia\YARG.Core\YARG.Core" /MIR /XD bin obj /NFL /NDL /NJH /NJS /NP | Out-Null

Write-Host "Restaurando os pacotes NuGet do jogo..."
& $py (Join-Path $PSScriptRoot 'preparar_copia.py') --nuget
if ($LASTEXITCODE -ne 0) { throw "Falha ao restaurar o NuGet" }

Write-Host "Abrindo a cópia no Unity $Versao em modo batch (grava o grafo de build)..."
$log = Join-Path $raiz '_work\unity-compilecheck.log'
$p = Start-Process -FilePath $unity -PassThru -WindowStyle Hidden -ArgumentList @(
    '-batchmode', '-nographics', '-quit', '-projectPath', $copia, '-logFile', $log)
$p.WaitForExit()
if (-not (Get-ChildItem "$copia\Library\Bee" -Filter *.dag.json -ErrorAction SilentlyContinue)) {
    throw "O Unity não gravou o grafo de build; ver $log"
}

& $py (Join-Path $PSScriptRoot 'preparar_copia.py')
Write-Host "Pronto. Agora: $py tools\unity-compile-check\compilar.py --sincronizar-de YARG"
