"""Cliente Observer con reconexión periódica."""

from __future__ import annotations

import argparse
import json
import logging
import socket
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from .protocol import recv_json, send_json

LOGGER = logging.getLogger(__name__)


def subscription_payload() -> dict[str, str]:
    """Construye el mensaje de subscripción requerido por la consigna."""
    return {
        "UUID": str(uuid.getnode()),
        "SESSION": str(uuid.uuid4()),
        "ACTION": "subscribe",
    }


def emit(payload: Any, output: Path | None) -> None:
    """Muestra cada evento y opcionalmente lo anexa a un archivo."""
    text = json.dumps(payload, ensure_ascii=False, default=str)
    print(text, flush=True)
    if output:
        with output.open("a", encoding="utf-8") as stream:
            stream.write(text + "\n")


def run(host: str, port: int, output: Path | None, retry: int = 30) -> None:
    """Mantiene una subscripción; ante caída reintenta cada ``retry`` segundos."""
    while True:
        try:
            with socket.create_connection((host, port), timeout=5) as sock:
                sock.settimeout(None)
                send_json(sock, subscription_payload())
                while True:
                    emit(recv_json(sock), output)
        except (OSError, ConnectionError) as exc:
            LOGGER.warning("Servidor no disponible (%s). Reintento en %ss", exc, retry)
            time.sleep(retry)


def build_parser() -> argparse.ArgumentParser:
    """Construye argumentos del ObserverClient."""
    parser = argparse.ArgumentParser(description="ObserverClient")
    parser.add_argument("-s", "--host", default="localhost")
    parser.add_argument("-p", "--port", type=int, default=8080)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--retry", type=int, default=30)
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada del ObserverClient."""
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)
    try:
        run(args.host, args.port, args.output, args.retry)
    except KeyboardInterrupt:
        print("Observer finalizado por usuario", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
