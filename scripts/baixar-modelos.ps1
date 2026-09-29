# Baixa os pesos dos modelos das fontes oficiais e confere o SHA-256 (os mesmos hashes fixados em
# autochart/src/autochart/models.py e registrados no SECURITY_LOG.md). Arquivo com hash diferente é apagado.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$models = @(
    @{ Dest = 'models\beat_this\final0.ckpt'
       Url = 'https://cloud.cp.jku.at/public.php/dav/files/7ik4RrBKTS273gp/final0.ckpt'
       Sha = '8c328b45f59d8dd3dff219253ff6a8d6482be57d0133a29140e2febbf8eb8331' },
    @{ Dest = 'models\demucs\htdemucs_6s-5c90dfd2.safetensors'
       Url = 'https://huggingface.co/adefossez/HTDemucs-6s/resolve/3c5ee475be622df764938de97e4281a7b07ffa58/5c90dfd2.safetensors'
       Sha = 'd2a1745f0744721f6b8ca5bf469b67c651ea5ed1b52998cab033b2158609d411' }
)
foreach ($m in $models) {
    $dest = Join-Path $root $m.Dest
    if ((Test-Path -LiteralPath $dest) -and ((Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash.ToLower() -eq $m.Sha)) {
        Write-Host "ok (já existe): $($m.Dest)"
        continue
    }
    New-Item -ItemType Directory -Force (Split-Path -Parent $dest) | Out-Null
    Write-Host "baixando $($m.Dest) ..."
    curl.exe -sSL --fail -o $dest $m.Url
    $h = (Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash.ToLower()
    if ($h -ne $m.Sha) {
        Remove-Item -LiteralPath $dest -Force
        throw "hash diferente do esperado para $($m.Dest) ($h); arquivo apagado"
    }
    Write-Host "ok: $($m.Dest)"
}
