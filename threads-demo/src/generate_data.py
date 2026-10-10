"""Gera CEPs fictícios de clientes e grava data/ceps.csv."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "ceps.csv"
DEFAULT_COUNT = 100

FIRST_NAMES = [
    "Ana",
    "Bruno",
    "Carla",
    "Diego",
    "Elena",
    "Felipe",
    "Gabriela",
    "Henrique",
    "Irene",
    "João",
    "Karen",
    "Lucas",
    "Marina",
    "Nicolas",
    "Olivia",
    "Paulo",
    "Queila",
    "Rafael",
    "Sandra",
    "Tiago",
]

LAST_NAMES = [
    "Souza",
    "Lima",
    "Almeida",
    "Costa",
    "Ferreira",
    "Gomes",
    "Ribeiro",
    "Carvalho",
    "Barbosa",
    "Araújo",
    "Rocha",
    "Martins",
    "Dias",
    "Teixeira",
    "Moreira",
    "Cardoso",
    "Correia",
    "Nunes",
    "Freitas",
    "Mendes",
]

# CEPs públicos reais, de várias cidades. A geração cicla esta lista.
CEPS = [
    "01310-100",  # São Paulo - Av. Paulista
    "20040-020",  # Rio de Janeiro - Centro
    "30130-010",  # Belo Horizonte
    "80010-000",  # Curitiba
    "90010-150",  # Porto Alegre
    "40140-110",  # Salvador - Barra
    "60160-230",  # Fortaleza
    "69005-070",  # Manaus
    "74003-010",  # Goiânia
    "58010-050",  # João Pessoa
    "01001-000",  # São Paulo - Sé
    "22041-080",  # Rio de Janeiro - Copacabana
    "30140-071",  # Belo Horizonte
    "80230-130",  # Curitiba
    "90570-080",  # Porto Alegre
    "40140-130",  # Salvador
    "60175-047",  # Fortaleza
    "69020-030",  # Manaus
    "74150-010",  # Goiânia
    "58040-400",  # João Pessoa
    "05422-030",  # São Paulo - Pinheiros
    "22250-040",  # Rio de Janeiro - Botafogo
    "30315-400",  # Belo Horizonte
    "80420-090",  # Curitiba
    "90430-001",  # Porto Alegre
    "41820-020",  # Salvador
    "60115-222",  # Fortaleza
    "69057-000",  # Manaus
    "74223-060",  # Goiânia
    "58045-010",  # João Pessoa
]


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)


def client_name(index: int) -> str:
    first = FIRST_NAMES[index % len(FIRST_NAMES)]
    last = LAST_NAMES[index % len(LAST_NAMES)]
    return f"{first} {last}"


def build_rows(count: int) -> list[dict]:
    if count < 1:
        raise ValueError("a quantidade precisa ser pelo menos 1")

    rows: list[dict] = []
    for index in range(count):
        rows.append(
            {
                "id": index + 1,
                "cliente": client_name(index),
                "cep": CEPS[index % len(CEPS)],
            }
        )
    return rows


def write_rows(rows: list[dict], path: Path = CSV_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "cliente", "cep"])
        writer.writeheader()
        writer.writerows(rows)


def load_rows(limit: int, path: Path = CSV_PATH) -> list[dict]:
    if limit < 1:
        raise ValueError("o limite precisa ser pelo menos 1")
    if not path.exists():
        raise FileNotFoundError(
            f"Não encontrei {path}. Rode: python src/generate_data.py"
        )

    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if len(rows) < limit:
        print(
            f"O CSV tem {len(rows)} linhas e o limite pedido é {limit}. "
            f"Vou usar {len(rows)}. Para gerar mais: "
            f"python src/generate_data.py --count {limit}",
            flush=True,
        )

    selected = []
    for row in rows[:limit]:
        selected.append(
            {
                "id": int(row["id"]),
                "cliente": row["cliente"],
                "cep": row["cep"],
            }
        )
    return selected


def main() -> None:
    configure_output()
    parser = argparse.ArgumentParser(
        description="Gera CEPs de clientes para a demo de threads."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_COUNT,
        help=f"Quantidade de linhas. Padrão: {DEFAULT_COUNT}.",
    )
    args = parser.parse_args()
    rows = build_rows(args.count)
    write_rows(rows)
    print(f"Gravei {len(rows)} linhas em {CSV_PATH}")
    print(f"CEPs distintos na lista base: {len(CEPS)}")


if __name__ == "__main__":
    main()
