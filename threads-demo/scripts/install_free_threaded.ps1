# Instala o Python free-threaded (sem GIL) e cria .venv-ft neste repo.
# Uso:
#   powershell -ExecutionPolicy Bypass -File scripts\install_free_threaded.ps1

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$version = '3.13.15'
$url = "https://www.python.org/ftp/python/$version/python-${version}t-amd64.zip"
$zipPath = "$env:TEMP\python-${version}t-amd64.zip"
$destRoot = "$env:LOCALAPPDATA\Programs\Python\Python313t"
$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $projectRoot '.venv-ft'

Write-Host "Baixando $url"
curl.exe -L --fail -o $zipPath $url
Write-Host "Arquivo: $((Get-Item $zipPath).Length) bytes"

if (Test-Path $destRoot) {
    Write-Host "Removendo instalação anterior em $destRoot"
    Remove-Item -Recurse -Force $destRoot
}
New-Item -ItemType Directory -Path $destRoot | Out-Null
Expand-Archive -Path $zipPath -DestinationPath $destRoot -Force

$pyt = Join-Path $destRoot 'python3.13t.exe'
if (-not (Test-Path $pyt)) {
    throw "Não achei python3.13t.exe em $destRoot"
}

Write-Host "Conferindo GIL..."
& $pyt -c "import sys; print(sys.version); assert sys._is_gil_enabled() is False, 'GIL ainda ligado'; print('GIL desligado: OK')"

if (Test-Path $venvPath) {
    Write-Host "Removendo venv antigo $venvPath"
    Remove-Item -Recurse -Force $venvPath
}

Write-Host "Criando venv em $venvPath"
& $pyt -m venv $venvPath

$venvPython = Join-Path $venvPath 'Scripts\python.exe'
& $venvPython -c "import sys; print(sys.executable); print('gil_enabled', sys._is_gil_enabled())"

Write-Host ""
Write-Host "Pronto. Para a demo:"
Write-Host "  .\.venv\Scripts\python.exe src\main.py cpu --upto 800000 --workers 4"
Write-Host "  .\.venv-ft\Scripts\python.exe src\main.py cpu --upto 800000 --workers 4"
Write-Host "Detalhes: docs\FREE_THREADED.md"
