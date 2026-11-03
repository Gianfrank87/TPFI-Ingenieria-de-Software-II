"""Utilidades del protocolo JSON sobre sockets TCP."""

from __future__ import annotations

import json
import socket
from typing import Any


class ProtocolError(ValueError):
    """Indica un mensaje inválido para el protocolo del TPFI."""


def send_json(sock: socket.socket, payload: Any) -> None:
    """Envía un objeto JSON terminado en salto de línea."""
    raw = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8") + b"\n"
    sock.sendall(raw)


def recv_json(sock: socket.socket) -> Any:
    """Recibe un único objeto JSON terminado en salto de línea."""
    data = bytearray()
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            if not data:
                raise ConnectionError("Conexión cerrada antes de recibir una respuesta")
            break
        data.extend(chunk)
        if b"\n" in chunk:
            break
    line = bytes(data).split(b"\n", 1)[0]
    try:
        return json.loads(line.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("Mensaje JSON inválido") from exc
