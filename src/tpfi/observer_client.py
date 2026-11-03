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

from .logging_setup import configure_logging, redact, safe_label
from .protocol import ProtocolError, recv_json, send_json

LOGGER = logging.getLogger("tpfi.observer_client")


def subscription_payload() -> dict[str, str]:
    """Construye el mensaje de subscripción requerido por la consigna."""
    return {
        "UUID": str(uuid.getnode()),
        "SESSION": str(uuid.uuid4()),
        "ACTION": "subscribe",
    }


def emit(payload: Any, output: Path | None) -> None:
    """Muestra cada evento y opcionalmente lo anexa a un archivo."""
    text = json.dumps(redact(payload), ensure_ascii=False, default=str)
    print(text, flush=True)
    if output:
        with output.open("a", encoding="utf-8") as stream:
            stream.write(text + "\n")


def run(host: str, port: int, output: Path | None, retry: int = 30) -> None:
    """Mantiene una subscripción; ante caída reintenta cada ``retry`` segundos."""
    connected_before = False
    while True:
        connected = False
        try:
            LOGGER.info("Conectando a %s:%s", safe_label(host), port)
            with socket.create_connection((host, port), timeout=5) as sock:
                connected = True
                LOGGER.info(
                    "%s TCP establecida",
                    "Reconexión" if connected_before else "Conexión",
                )
                connected_before = True
                sock.settimeout(None)
                send_json(sock, subscription_payload())
                LOGGER.info("Solicitud SUBSCRIBE enviada")
                ack = recv_json(sock)
                if (
                    not isinstance(ack, dict)
                    or ack.get("status") != "OK"
                    or ack.get("action") != "subscribe"
                ):
                    raise ProtocolError("Suscripción rechazada o inválida")
                emit(ack, output)
                LOGGER.info("Suscripción confirmada; esperando modificaciones...")
                while True:
                    event = recv_json(sock)
                    if isinstance(event, dict) and event.get("action") == "set":
                        data = event.get("data")
                        record_id = data.get("id") if isinstance(data, dict) else None
                        LOGGER.info(
                            "SET recibido: ID=%s; JSON en stdout", safe_label(record_id)
                        )
                    emit(event, output)
        except (OSError, ConnectionError, ProtocolError) as exc:
            LOGGER.info(
                "%s (%s). Reintento en %ss",
                "Servidor desconectado" if connected else "Servidor no disponible",
                type(exc).__name__,
                retry,
            )
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
    configure_logging("OBSERVER", args.verbose)
    try:
        run(args.host, args.port, args.output, args.retry)
    except KeyboardInterrupt:
        print("Observer finalizado por usuario", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
