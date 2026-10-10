# Python free-threaded (sem GIL) neste projeto

Documento do que foi instalado nesta máquina e como repetir o processo.

## O que foi instalado

| Item | Valor |
| --- | --- |
| Build | Python **3.13.15** experimental free-threading |
| Origem | Zip oficial: `python-3.13.15t-amd64.zip` |
| Pasta | `%LOCALAPPDATA%\Programs\Python\Python313t` |
| Executável | `...\Python313t\python3.13t.exe` |
| Venv do projeto | `threads-demo\.venv-ft` |
| Conferência | `sys._is_gil_enabled()` → `False` |

URL usada:

```text
https://www.python.org/ftp/python/3.13.15/python-3.13.15t-amd64.zip
```

## Por que zip e não o instalador gráfico

O instalador `.exe` do python.org também instala o free-threaded (checkbox
*Download free-threaded binaries*), mas exige UI. O zip oficial `*t-amd64.zip`
dá o mesmo build e dá para automatizar no PowerShell.

## Passos (reprodutível)

No PowerShell, a partir de qualquer pasta:

```powershell
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$version = '3.13.15'
$url = "https://www.python.org/ftp/python/$version/python-${version}t-amd64.zip"
$zipPath = "$env:TEMP\python-${version}t-amd64.zip"
$destRoot = "$env:LOCALAPPDATA\Programs\Python\Python313t"

curl.exe -L --fail -o $zipPath $url

if (Test-Path $destRoot) { Remove-Item -Recurse -Force $destRoot }
New-Item -ItemType Directory -Path $destRoot | Out-Null
Expand-Archive -Path $zipPath -DestinationPath $destRoot -Force

$pyt = Join-Path $destRoot 'python3.13t.exe'
& $pyt -c "import sys; print(sys.version); print(sys._is_gil_enabled())"
# Esperado: free-threading build + False
```

Ou rode o script do repositório:

```powershell
cd threads-demo
powershell -ExecutionPolicy Bypass -File scripts\install_free_threaded.ps1
```

## Venv do projeto

O Python free-threaded **não** deve misturar site-packages com o `.venv` normal.

```powershell
cd threads-demo
& "$env:LOCALAPPDATA\Programs\Python\Python313t\python3.13t.exe" -m venv .venv-ft
.\.venv-ft\Scripts\Activate.ps1
python -c "import sys; print(sys._is_gil_enabled())"   # False
```

Esta demo não precisa de `pip install` (só stdlib).

## Como comparar na palestra

```powershell
cd threads-demo

# COM GIL (venv normal)
.\.venv\Scripts\python.exe src\main.py cpu --upto 800000 --workers 4

# SEM GIL (venv free-threaded)
.\.venv-ft\Scripts\python.exe src\main.py cpu --upto 800000 --workers 4
```

### Resultado medido nesta máquina (exemplo)

| Build | Sequencial | Threads | Processos |
| --- | ---: | ---: | ---: |
| GIL ligado (`.venv`) | 2.44s | 2.60s (**0.94x**) | 1.32s (**1.85x**) |
| GIL desligado (`.venv-ft`) | 3.17s | 1.11s (**2.87x**) | 1.62s (**1.95x**) |

Mensagem didática:

- **Com GIL:** threads ≈ sequencial; processos aceleram.
- **Sem GIL:** threads aceleram de verdade (aqui ~2.9x).

Números mudam a cada run (carga da máquina). O padrão relativo é o que importa.

## Alternativa: instalador oficial (UI)

1. Baixe o instalador em https://www.python.org/downloads/windows/
2. Customize installation → marque **Download free-threaded binaries**
3. Depois: `py -0p` deve listar algo como `3.13t`
4. Use `py -3.13t` ou o `python3.13t.exe` instalado

## Observações

- Free-threaded ainda é **experimental**. Pacotes com extensão C podem falhar;
  esta demo só usa biblioteca padrão.
- O zip instalado em `%LOCALAPPDATA%` **não** registra automaticamente o launcher
  `py -3.13t`. Use o caminho completo ou o `.venv-ft`.
- Sequencial no free-threaded pode sair um pouco mais lento que no CPython com
  GIL (overhead do build). O contraste importante é **threads com vs sem GIL**.
