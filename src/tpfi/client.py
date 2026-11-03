"""Cliente get/set/list del TPFI."""

from __future__ import annotations

import argparse
import json
import logging
import socket
import sys
from pathlib import Path
from typing import Any

from .logging_setup import configure_logging, safe_label
from .protocol import recv_json, send_json

LOGGER = logging.getLogger("tpfi.client")


def request_server(payload: dict[str, Any], host: str, port: int) -> Any:
    """Envía una solicitud y devuelve la única respuesta del servidor."""
    LOGGER.info("Conectando a %s:%s", safe_label(host), port)
    connected = False
    try:
        with socket.create_connection((host, port), timeout=5) as sock:
            connected = True
            LOGGER.info("Conexión TCP establecida")
            try:
                send_json(sock, payload)
                LOGGER.info(
                    "%s enviado: ID=%s",
                    safe_label(payload.get("ACTION", "")),
                    safe_label(payload.get("ID")),
                )
                response = recv_json(sock)
                LOGGER.info("Respuesta recibida; JSON disponible en stdout")
                return response
            finally:
                LOGGER.debug("Finalizando intercambio TCP")
    except (OSError, ConnectionError, ValueError):
        LOGGER.error("Error de comunicación con el servidor")
        raise
    finally:
        if connected:
            LOGGER.info("Conexión cerrada")


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
    configure_logging("CLIENT", args.verbose)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("El JSON de entrada debe ser un objeto")
        result = request_server(payload, args.host, args.port)
    except (OSError, ConnectionError, ValueError) as exc:
        print(json.dumps({"Error": type(exc).__name__}), file=sys.stderr)
        return 1
    text = json.dumps(result, ensure_ascii=False, indent=2, default=str)
    print(text)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
