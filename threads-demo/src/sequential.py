"""Uma linha por vez.

A próxima chamada só começa quando a anterior termina.
O tempo total fica perto da soma das esperas da API.
"""

from __future__ import annotations

import time

from viacep_client import format_address, lookup_cep, public_error


def process_sequential(rows: list[dict]) -> tuple[list[dict], float]:
    results: list[dict] = []
    started = time.perf_counter()

    for row in rows:
        row_id = row["id"]
        print(f"[Sequential] Iniciando CEP {row_id} ({row['cep']})", flush=True)
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
            print(
                f"[Sequential] Erro no CEP {row_id}: {result['erro']}",
                flush=True,
            )

        print(
            f"[Sequential] Finalizando CEP {row_id} -> "
            f"{result['endereco'] or 'erro'}",
            flush=True,
        )
        results.append(result)

    elapsed = time.perf_counter() - started
    _print_summary(len(rows), len(results), results, elapsed)
    return results, elapsed


def _print_summary(total: int, processed: int, results: list[dict], elapsed: float) -> None:
    errors = sum(1 for item in results if item["erro"])
    print()
    print(f"Quantidade de CEPs: {total}")
    print(f"Quantidade processada: {processed}")
    print(f"Com sucesso: {processed - errors}")
    print(f"Com erro: {errors}")
    print(f"Tempo total: {elapsed:.2f} segundos")
