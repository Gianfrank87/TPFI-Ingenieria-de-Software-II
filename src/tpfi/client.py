"""Cliente get/set/list del TPFI."""

from __future__ import annotations

import argparse
import json
import logging
import socket
import sys
from pathlib import Path
from typing import Any

from .protocol import recv_json, send_json

LOGGER = logging.getLogger(__name__)


def request_server(payload: dict[str, Any], host: str, port: int) -> Any:
    """Envía una solicitud y devuelve la única respuesta del servidor."""
    with socket.create_connection((host, port), timeout=5) as sock:
        send_json(sock, payload)
        return recv_json(sock)


def build_parser() -> argparse.ArgumentParser:
    """Construye argumentos compatibles con la consigna."""
    parser = argparse.ArgumentParser(description="SingletonClient")
    parser.add_argument("-i", "--input", required=True, type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("-s", "--host", default="localhost")
    parser.add_argument("-p", "--port", type=int, default=8080)
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Carga JSON, invoca al servidor y emite la respuesta."""
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("El JSON de entrada debe ser un objeto")
        result = request_server(payload, args.host, args.port)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"Error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    text = json.dumps(result, ensure_ascii=False, indent=2, default=str)
    print(text)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
