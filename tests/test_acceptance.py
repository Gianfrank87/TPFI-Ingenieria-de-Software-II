"""Casos de aceptación derivados directamente de la consigna del TPFI."""

from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

import tpfi.client as client
from tpfi.observer_client import build_parser as observer_parser
from tpfi.server import ApplicationServer
from tpfi.server import build_parser as server_parser


class FakeData:
    """Gateway mínimo para pruebas de infraestructura."""

    def get(self, record_id: str):
        return {"id": record_id}

    def list_all(self):
        return []

    def set(self, record_id: str, data: dict):
        return {"id": record_id, **data}


class FakeLog:
    """Log mínimo para pruebas de infraestructura."""

    def write(self, **kwargs):
        return kwargs


def test_malformed_arguments_each_program() -> None:
    """Cada CLI debe rechazar argumentos inválidos."""
    with pytest.raises(SystemExit):
        client.build_parser().parse_args([])
    with pytest.raises(SystemExit):
        observer_parser().parse_args(["-p", "no-es-numero"])
    with pytest.raises(SystemExit):
        server_parser().parse_args(["-p", "no-es-numero"])


def test_singleton_client_handles_server_down(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """SingletonClient informa error y termina controladamente si no hay servidor."""
    source = tmp_path / "input.json"
    source.write_text(json.dumps({"UUID": "cpu", "ACTION": "list"}), encoding="utf-8")

    def fail(*args, **kwargs):
        raise OSError("server down")

    monkeypatch.setattr(client, "request_server", fail)
    assert client.main(["-i", str(source)]) == 1
    assert "server down" in capsys.readouterr().err


def test_second_server_cannot_bind_same_port() -> None:
    """El sistema detecta el intento de levantar dos servidores en el mismo puerto."""
    blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    blocker.bind(("127.0.0.1", 0))
    blocker.listen()
    port = blocker.getsockname()[1]
    server = ApplicationServer(
        "127.0.0.1",
        port,
        data_gateway=FakeData(),  # type: ignore[arg-type]
        log_gateway=FakeLog(),  # type: ignore[arg-type]
    )
    try:
        with pytest.raises(OSError):
            server.serve_forever()
    finally:
        blocker.close()
