"""Mede o mesmo lote com 1, 2, 5, 10 e 20 workers.

O resultado é o tempo observado nesta execução. Não há número fixo no código.
"""

from __future__ import annotations

from threaded import process_threaded

WORKER_COUNTS = (1, 2, 5, 10, 20)


def run_benchmark(
    rows: list[dict],
    worker_counts: tuple[int, ...] = WORKER_COUNTS,
) -> list[dict]:
    calls = len(rows) * len(worker_counts)
    print(
        f"Benchmark: {len(rows)} CEPs x {len(worker_counts)} níveis "
        f"= cerca de {calls} chamadas ao ViaCEP."
    )
    print("Erros temporários podem gerar tentativas extras.")
    print(
        "Workers = 1 ainda passa pelo ThreadPoolExecutor. "
        "O laço sem pool é o comando sequencial."
    )

    results_table: list[dict] = []
    for workers in worker_counts:
        print()
        print(f"=== Workers: {workers} ===")
        results, elapsed = process_threaded(rows, max_workers=workers)
        errors = sum(1 for item in results if item["erro"])
        results_table.append({"workers": workers, "elapsed": elapsed, "errors": errors})

    print()
    print(format_table(results_table))
    _print_reading(results_table)
    return results_table


def format_table(rows: list[dict]) -> str:
    lines = [
        "| Workers | Tempo   | Erros |",
        "| ------- | ------- | ----- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['workers']:<7} | {row['elapsed']:>6.2f}s | {row['errors']:<5} |"
        )
    return "\n".join(lines)


def _print_reading(rows: list[dict]) -> None:
    if len(rows) < 2:
        return
    fastest = min(rows, key=lambda row: row["elapsed"])
    slowest = max(rows, key=lambda row: row["elapsed"])
    print()
    print(
        f"Mais rápido nesta execução: {fastest['workers']} workers "
        f"({fastest['elapsed']:.2f}s)."
    )
    print(
        f"Mais lento nesta execução: {slowest['workers']} workers "
        f"({slowest['elapsed']:.2f}s)."
    )
    print("Se o tempo piorar com mais workers, olhe a coluna de erros e o rate limit.")
