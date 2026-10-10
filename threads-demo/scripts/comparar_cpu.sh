#!/usr/bin/env bash
# Roda a demo de CPU nos dois Pythons (.venv com GIL, .venv-ft sem GIL)
# e mostra o contraste das threads num comando só.
#
# Uso (a partir de threads-demo, no Git Bash):
#   bash scripts/comparar_cpu.sh              # --upto 400000 (rápido, padrão palestra)
#   bash scripts/comparar_cpu.sh 200000       # ainda mais rápido
#   bash scripts/comparar_cpu.sh 800000 4     # upto=800000 workers=4 (mais lento, contraste mais nítido)

cd "$(dirname "$0")/.."

UPTO="${1:-400000}"
WORKERS="${2:-4}"

echo "============================================================"
echo "  CPU demo · upto=$UPTO workers=$WORKERS"
echo "============================================================"

echo
echo ">>> COM GIL  (.venv)  — threads devem ficar perto de 1x"
echo "------------------------------------------------------------"
.venv/Scripts/python.exe src/main.py cpu --upto "$UPTO" --workers "$WORKERS"

echo
echo ">>> SEM GIL  (.venv-ft) — threads devem acelerar de verdade"
echo "------------------------------------------------------------"
.venv-ft/Scripts/python.exe src/main.py cpu --upto "$UPTO" --workers "$WORKERS"

echo
echo "============================================================"
echo "  Compare a linha 'Threads' de cada bloco."
echo "  Com GIL: ~1x. Sem GIL: >2x. Esse é o contraste da palestra."
echo "============================================================"
