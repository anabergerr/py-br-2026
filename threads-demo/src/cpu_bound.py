"""Trabalho pesado em Python puro: sequencial vs threads vs processos.

O exemplo é um checksum: calcular SHA-256 de muitos blocos pequenos. Em
software real isso aparece em "verificar integridade de arquivos", "procurar
duplicatas", "assinar lotes de dados". Aqui o payload é determinístico só pra
o cálculo bater nos três modos (sequencial, threads e processos).

Por que esse exemplo prende o GIL (e vira demo didática do GIL):

- O payload tem 1024 bytes. O `hashlib` do CPython só libera o GIL para
  entradas >= 2048 bytes (HASHLIB_GIL_MINSIZE). Abaixo disso, o GIL fica
  preso durante a chamada.
- O laço `for` fica em bytecode Python, que também segura o GIL.

Com GIL ativo, threads praticamente não aceleram. Processos aceleram porque
cada um tem o próprio interpretador (e o próprio GIL). No Python free-threaded
(3.13+ sem GIL), o mesmo comando com threads tende a se aproximar do ganho
dos processos.
"""

from __future__ import annotations

import hashlib
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor


# Padrão: ~2–3s no sequencial em notebook típico; processos devem ganhar.
# Palestra rápida: --upto 400000. Se processos empatam: --upto 1200000.
DEFAULT_UPTO = 800_000
DEFAULT_WORKERS = max(2, min(8, os.cpu_count() or 4))

# 1024 bytes < HASHLIB_GIL_MINSIZE (2048). Mantém o GIL preso dentro de hashlib.
# ponytail: valor fixo propositalmente. Mexer aqui muda o ponto didático.
BLOCK_SIZE = 1024


def gil_status() -> tuple[bool | None, str]:
    """(gil_ligado, rótulo legível). None = API indisponível nesta versão."""
    checker = getattr(sys, "_is_gil_enabled", None)
    if checker is None:
        return None, "desconhecido (Python < 3.13)"
    enabled = bool(checker())
    if enabled:
        return True, "ligado (CPython padrão)"
    return False, "desligado (free-threaded / sem GIL)"


def hash_blocks(start: int, end: int) -> int:
    """SHA-256 em cada bloco de [start, end). Retorna soma do 1º byte.

    Cada bloco tem 1024 bytes (índice repetido). Mantido abaixo do limiar
    que faz o hashlib liberar o GIL, de propósito.
    """
    total = 0
    for i in range(start, end):
        # 8 bytes * 128 = 1024 bytes, determinístico por índice.
        payload = i.to_bytes(8, "big", signed=False) * (BLOCK_SIZE // 8)
        total += hashlib.sha256(payload).digest()[0]
    return total


def make_chunks(upto: int, parts: int) -> list[tuple[int, int]]:
    if upto < 1:
        raise ValueError("upto precisa ser pelo menos 1")
    if parts < 1:
        raise ValueError("workers precisa ser pelo menos 1")

    size = (upto + parts - 1) // parts
    chunks: list[tuple[int, int]] = []
    for index in range(parts):
        start = index * size
        end = min(upto, start + size)
        if start < end:
            chunks.append((start, end))
    return chunks


def run_sequential(chunks: list[tuple[int, int]]) -> tuple[int, float]:
    started = time.perf_counter()
    total = sum(hash_blocks(start, end) for start, end in chunks)
    return total, time.perf_counter() - started


def run_threaded(chunks: list[tuple[int, int]], workers: int) -> tuple[int, float]:
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        total = sum(executor.map(_hash_blocks_star, chunks))
    return total, time.perf_counter() - started


def run_processes(chunks: list[tuple[int, int]], workers: int) -> tuple[int, float]:
    started = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as executor:
        total = sum(executor.map(_hash_blocks_star, chunks))
    return total, time.perf_counter() - started


def _hash_blocks_star(chunk: tuple[int, int]) -> int:
    # Precisa ser top-level para o ProcessPoolExecutor picklar no Windows.
    start, end = chunk
    return hash_blocks(start, end)


def run_cpu_compare(upto: int = DEFAULT_UPTO, workers: int = DEFAULT_WORKERS) -> None:
    gil_on, gil_label = gil_status()
    chunks = make_chunks(upto, workers)

    print(f"Python: {sys.version.split()[0]}  ({sys.executable})")
    print(f"GIL: {gil_label}")
    print(f"CPU lógicos: {os.cpu_count()}")
    print(
        f"Trabalho: SHA-256 de {upto} blocos de {BLOCK_SIZE} bytes, "
        f"em {len(chunks)} fatias"
    )
    print(f"Workers: {workers}")
    print()

    print("=== Sequencial ===")
    seq_total, seq_time = run_sequential(chunks)
    print(f"Checksum: {seq_total}")
    print(f"Tempo: {seq_time:.2f} segundos")
    print()

    print(f"=== Threads (workers={workers}) ===")
    thr_total, thr_time = run_threaded(chunks, workers)
    print(f"Checksum: {thr_total}")
    print(f"Tempo: {thr_time:.2f} segundos")
    print()

    print(f"=== Processos (workers={workers}) ===")
    proc_total, proc_time = run_processes(chunks, workers)
    print(f"Checksum: {proc_total}")
    print(f"Tempo: {proc_time:.2f} segundos")
    print()

    if {seq_total, thr_total, proc_total} != {seq_total}:
        print("Aviso: totais diferentes — algo deu errado no cálculo.")
        return

    print("--- Comparação ---")
    print(f"Sequencial: {seq_time:.2f}s  (baseline)")
    _print_speedup("Threads", seq_time, thr_time)
    _print_speedup("Processos", seq_time, proc_time)
    print()
    _print_reading(gil_on, seq_time, thr_time, proc_time)


def _print_speedup(label: str, baseline: float, elapsed: float) -> None:
    if elapsed <= 0:
        print(f"{label}: tempo inválido")
        return
    speedup = baseline / elapsed
    print(f"{label}: {elapsed:.2f}s  (speedup {speedup:.2f}x vs sequencial)")


def _print_reading(
    gil_on: bool | None,
    seq_time: float,
    thr_time: float,
    proc_time: float,
) -> None:
    thr_speedup = seq_time / thr_time if thr_time > 0 else 0.0
    proc_speedup = seq_time / proc_time if proc_time > 0 else 0.0

    if gil_on is True:
        print("Leitura (GIL ligado):")
        print("- Threads ≈ sequencial: o GIL impede paralelismo real em Python puro.")
        print("- Processos mais rápidos: cada processo tem seu próprio GIL.")
        if thr_speedup >= 1.3:
            print("- Neste run as threads ajudaram um pouco (agendamento/OS); o padrão típico é pouco ganho.")
        if proc_speedup < 1.2:
            print("- Poucos núcleos ou lote pequeno: processos podem não brilhar neste hardware.")
        print("- Para ver threads acelerando CPU de verdade, rode o mesmo comando no Python free-threaded.")
        return

    if gil_on is False:
        print("Leitura (GIL desligado / free-threaded):")
        print("- Threads podem usar vários núcleos em Python puro.")
        print("- Compare com o mesmo comando no Python normal: lá threads quase não aceleram.")
        if thr_speedup >= 1.3:
            print("- Neste run as threads aceleraram — contraste típico com o CPython com GIL.")
        else:
            print("- Se threads não aceleraram, aumente --upto ou confira se há núcleos livres.")
        return

    print("Leitura:")
    print("- Compare threads (mesmo processo) com processos (vários interpretadores).")


# Self-check: três modos têm que dar o mesmo total.
# ponytail: roda em processo direto, sem framework de teste.
if __name__ == "__main__" and len(sys.argv) == 1:
    chunks = make_chunks(2_000, 4)
    seq, _ = run_sequential(chunks)
    thr, _ = run_threaded(chunks, 4)
    proc, _ = run_processes(chunks, 4)
    assert seq == thr == proc, f"inconsistente: seq={seq} thr={thr} proc={proc}"
    print(f"ok · checksum consistente nos três modos ({seq})")
