"""Roteiro da demo.

uma          consulta 1 CEP
sequencial   uma por vez
threads      ThreadPoolExecutor
comparar     sequencial, threads e speedup medido
benchmark    1, 2, 5, 10 e 20 workers
cpu          checksum pesado (SHA-256): sequencial vs threads vs processos (GIL)
"""

from __future__ import annotations

import argparse
import sys
import time

from benchmark import run_benchmark
from cpu_bound import DEFAULT_UPTO, DEFAULT_WORKERS as DEFAULT_CPU_WORKERS, run_cpu_compare
from generate_data import load_rows
from sequential import process_sequential
from threaded import process_threaded
from viacep_client import format_address, lookup_cep, public_error

# Padrão pequeno para ensaio rápido.
# Na palestra maior: --limit 100 ou --limit 200.
DEFAULT_LIMIT = 20
DEFAULT_WORKERS = 10


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Demo de threads (ViaCEP) e do GIL (CPU vs processos)."
    )
    subcommands = parser.add_subparsers(dest="comando", required=True)

    subcommands.add_parser("uma", help="Consulta o primeiro CEP. Uma chamada.")

    sequential = subcommands.add_parser("sequencial", help="Processa o lote, uma por vez.")
    _add_limit(sequential)

    threaded = subcommands.add_parser("threads", help="Processa o lote com threads.")
    _add_limit(threaded)
    _add_workers(threaded)

    benchmark = subcommands.add_parser(
        "benchmark",
        help="Mede o lote com 1, 2, 5, 10 e 20 workers.",
    )
    _add_limit(benchmark)

    compare = subcommands.add_parser(
        "comparar",
        help="Roda o sequencial e as threads e calcula o speedup.",
    )
    _add_limit(compare)
    _add_workers(compare)

    cpu = subcommands.add_parser(
        "cpu",
        help="Cálculo pesado: sequencial vs threads vs processos (efeito do GIL).",
    )
    cpu.add_argument(
        "--upto",
        type=int,
        default=DEFAULT_UPTO,
        help=f"Quantidade total de blocos a hashear. Padrão: {DEFAULT_UPTO}.",
    )
    cpu.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_CPU_WORKERS,
        help=f"Workers de threads/processos. Padrão: {DEFAULT_CPU_WORKERS}.",
    )
    return parser


def _add_limit(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Linhas usadas neste comando. Padrão: {DEFAULT_LIMIT}.",
    )


def _add_workers(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Threads do pool. Padrão: {DEFAULT_WORKERS}.",
    )


def main() -> None:
    configure_output()
    args = build_parser().parse_args()
    try:
        if args.comando == "uma":
            run_one()
            return
        if args.comando == "cpu":
            run_cpu_compare(upto=args.upto, workers=args.workers)
            return
        rows = load_rows(args.limit)
        print("API: ViaCEP (https://viacep.com.br)")
        if args.comando == "sequencial":
            _warn(len(rows))
            process_sequential(rows)
        elif args.comando == "threads":
            _warn(len(rows))
            process_threaded(rows, max_workers=args.workers)
        elif args.comando == "benchmark":
            run_benchmark(rows)
        elif args.comando == "comparar":
            run_compare(rows, workers=args.workers)
    except Exception as exc:
        print(f"Erro: {public_error(exc)}", file=sys.stderr)
        raise SystemExit(1) from None


def run_one() -> None:
    row = load_rows(1)[0]
    print("API: ViaCEP (https://viacep.com.br)")
    print("Este comando faz 1 chamada ao ViaCEP.")
    print(f"Linha {row['id']} — {row['cliente']}")
    print(f"CEP: {row['cep']}")
    print()
    started = time.perf_counter()
    result = lookup_cep(row["cep"])
    elapsed = time.perf_counter() - started
    print(f"Endereço: {format_address(result)}")
    print(f"Tempo: {elapsed:.2f} segundos")


def run_compare(rows: list[dict], workers: int) -> None:
    calls = len(rows) * 2
    _warn(calls)
    print("O segundo teste pode ficar mais lento se o primeiro saturar a API.")
    print()
    print("=== Sequencial ===")
    _, sequential_time = process_sequential(rows)
    print()
    print(f"=== Threads (workers={workers}) ===")
    _, threaded_time = process_threaded(rows, max_workers=workers)
    print()
    print(f"Tempo sequencial: {sequential_time:.2f} segundos")
    print(f"Tempo com Threads: {threaded_time:.2f} segundos")
    if threaded_time <= 0:
        print("Não foi possível calcular o speedup.")
        return
    speedup = sequential_time / threaded_time
    print("Fórmula: speedup = tempo_sequencial / tempo_threaded")
    if speedup >= 1:
        print(f"Speedup: {speedup:.2f} vezes mais rápido")
    else:
        print(
            f"Speedup: {speedup:.2f} "
            "(menor que 1: neste lote as threads não ficaram mais rápidas)"
        )


def _warn(calls: int) -> None:
    print(f"Cerca de {calls} chamada(s) ao ViaCEP.")


if __name__ == "__main__":
    main()
