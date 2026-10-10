"""Várias linhas ao mesmo tempo com ThreadPoolExecutor.

Cada thread chama lookup_cep e bloqueia no HTTPS do ViaCEP.
Enquanto essa thread espera a rede, o CPython libera o GIL e outra
thread pode enviar a próxima consulta. O ganho existe porque o
trabalho é I/O-bound. Mais workers não garante menos tempo: a API
pode limitar concorrência ou ficar mais lenta.
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

from viacep_client import format_address, log, lookup_cep, public_error


def _lookup(row: dict) -> dict:
    """Trabalho de uma thread: uma linha, uma chamada, um resultado."""
    row_id = row["id"]
    thread_name = threading.current_thread().name
    log(f"[Thread {thread_name}] Iniciando CEP {row_id} ({row['cep']})")
    try:
        looked_up = lookup_cep(row["cep"])
        result = {
            "id": row_id,
            "endereco": format_address(looked_up),
            "erro": None,
        }
    except Exception as exc:
        result = {
            "id": row_id,
            "endereco": None,
            "erro": public_error(exc),
        }
        log(f"[Thread {thread_name}] Erro no CEP {row_id}: {result['erro']}")

    log(
        f"[Thread {thread_name}] Finalizando CEP {row_id} -> "
        f"{result['endereco'] or 'erro'}"
    )
    return result


def process_threaded(
    rows: list[dict],
    max_workers: int = 10,
) -> tuple[list[dict], float]:
    if max_workers < 1:
        raise ValueError("max_workers precisa ser pelo menos 1")

    print(
        f"[Thread] Lote de {len(rows)} CEPs com {max_workers} workers.",
        flush=True,
    )

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="worker") as executor:
        # map devolve na ordem do CSV. Os logs não seguem essa ordem:
        # eles aparecem conforme cada thread entra e sai da espera da API.
        results = list(executor.map(_lookup, rows))
    elapsed = time.perf_counter() - started

    _print_summary(len(rows), max_workers, results, elapsed)
    return results, elapsed


def _print_summary(
    total: int,
    max_workers: int,
    results: list[dict],
    elapsed: float,
) -> None:
    errors = sum(1 for item in results if item["erro"])
    print()
    print(f"Quantidade de CEPs: {total}")
    print(f"Quantidade de workers: {max_workers}")
    print(f"Quantidade processada: {len(results)}")
    print(f"Com sucesso: {len(results) - errors}")
    print(f"Com erro: {errors}")
    print(f"Tempo total: {elapsed:.2f} segundos")
