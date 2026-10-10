"""Cliente ViaCEP: uma linha da planilha, uma chamada HTTPS.

A chamada é síncrona de propósito: quem chama fica bloqueado até a rede
voltar. Esse tempo de espera é o que as threads vão sobrepor.
"""

from __future__ import annotations

import json
import re
import threading
import time
import urllib.error
import urllib.request

BASE_URL = "https://viacep.com.br/ws/{cep}/json/"
MAX_ATTEMPTS = 3
TIMEOUT_SECONDS = 15

# Só o print. A chamada HTTP não entra neste lock.
log_lock = threading.Lock()


def log(message: str) -> None:
    with log_lock:
        print(message, flush=True)


def public_error(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"[:300]


def lookup_cep(cep: str) -> dict:
    """Consulta um CEP e devolve logradouro, bairro, cidade e UF."""
    digits = re.sub(r"\D", "", cep)
    if len(digits) != 8:
        raise ValueError(f"CEP inválido: {cep!r}")

    url = BASE_URL.format(cep=digits)
    last_error: Exception | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            request = urllib.request.Request(
                url,
                headers={"Accept": "application/json", "User-Agent": "threads-demo/1.0"},
            )
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read().decode("utf-8"))

            if payload.get("erro") in (True, "true"):
                raise ValueError(f"CEP não encontrado: {digits}")

            return {
                "cep": payload.get("cep") or digits,
                "logradouro": (payload.get("logradouro") or "").strip(),
                "bairro": (payload.get("bairro") or "").strip(),
                "localidade": (payload.get("localidade") or "").strip(),
                "uf": (payload.get("uf") or "").strip(),
            }
        except Exception as exc:
            last_error = exc
            if attempt == MAX_ATTEMPTS or not _is_retryable(exc):
                raise
            wait_seconds = 2 ** (attempt - 1)
            log(
                f"[ViaCEP] tentativa {attempt}/{MAX_ATTEMPTS} falhou "
                f"({public_error(exc)}). Nova tentativa em {wait_seconds}s."
            )
            time.sleep(wait_seconds)

    assert last_error is not None
    raise last_error


def format_address(data: dict) -> str:
    street = data.get("logradouro") or "(sem logradouro)"
    neighborhood = data.get("bairro") or "(sem bairro)"
    city = data.get("localidade") or "?"
    state = data.get("uf") or "?"
    return f"{street}, {neighborhood} — {city}/{state}"


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, (ValueError, json.JSONDecodeError)):
        return False
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in {429, 500, 502, 503, 504}
    return isinstance(exc, (urllib.error.URLError, TimeoutError, ConnectionError))
