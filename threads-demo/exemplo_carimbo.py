"""Exemplo mínimo do carimbo (SHA-256) mostrando o GIL.

O mesmo trabalho rodado de três jeitos, medindo o tempo:
  - sequencial   (uma linha de trabalho)
  - threads      (várias, mas o GIL trava: ficam perto de 1x)
  - processos    (cada um tem seu GIL: aceleram de verdade)

Rode nos dois Pythons e compare a linha "threads":
  .venv/Scripts/python.exe   exemplo_carimbo.py     # GIL ligado  -> threads ~1x
  .venv-ft/Scripts/python.exe exemplo_carimbo.py    # GIL desligado -> threads aceleram

Mexa em BLOCOS pra ficar mais rápido ou mais lento. 200_000 é ~1s.
"""
import hashlib
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

BLOCOS = 200_000        # menos aqui = mais rápido
TAMANHO = 1024          # < 2048: o hashlib NÃO solta o GIL (de propósito)
WORKERS = 4


def carimba(fatia):
    """Carimba (SHA-256) cada bloco da fatia [start, end)."""
    start, end = fatia
    total = 0
    for i in range(start, end):
        payload = i.to_bytes(8, "big") * (TAMANHO // 8)  # 1024 bytes inventados do índice
        total += hashlib.sha256(payload).digest()[0]
    return total


def fatias(n, parts):
    """Divide n blocos em parts fatias (start, end)."""
    size = (n + parts - 1) // parts
    return [(i, min(n, i + size)) for i in range(0, n, size)]


def mede(fn):
    t = time.perf_counter()
    total = fn()
    return total, time.perf_counter() - t


if __name__ == "__main__":
    chunks = fatias(BLOCOS, WORKERS)

    # 1) sequencial — uma linha de trabalho
    _, t_seq = mede(lambda: sum(carimba(c) for c in chunks))

    # 2) threads — várias, mas o GIL mantém num núcleo só
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        _, t_thr = mede(lambda: sum(ex.map(carimba, chunks)))

    # 3) processos — cada um tem seu próprio GIL, ocupam vários núcleos
    with ProcessPoolExecutor(max_workers=WORKERS) as ex:
        _, t_proc = mede(lambda: sum(ex.map(carimba, chunks)))

    gil = getattr(sys, "_is_gil_enabled", lambda: None)()
    print(f"GIL:        {gil}")
    print(f"sequencial:  {t_seq:.2f}s")
    print(f"threads:     {t_thr:.2f}s  ({t_seq / t_thr:.2f}x)")
    print(f"processos:   {t_proc:.2f}s  ({t_seq / t_proc:.2f}x)")
    print()
    print("Com GIL: threads ~= 1x (GIL trava). Processos aceleram.")
    print("Sem GIL: threads aceleram junto com os processos.")
