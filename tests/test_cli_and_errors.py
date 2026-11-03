"""Pruebas de caminos de CLI y errores para completar aceptación."""

from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

from tpfi import observer_client
from tpfi.protocol import ProtocolError, recv_json
from tpfi.server import ApplicationServer, LogGateway, build_parser, main


def test_protocol_invalid_json() -> None:
    left, right = socket.socketpair()
    try:
        left.sendall(b"{bad}\n")
        with pytest.raises(ProtocolError):
            recv_json(right)
    finally:
        left.close()
        right.close()


def test_observer_emit_stdout_and_file(tmp_path: Path, capsys) -> None:
    output = tmp_path / "events.jsonl"
    observer_client.emit({"status": "OK"}, output)
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "OK"
    assert "OK" in capsys.readouterr().out


def test_observer_run_retries_when_server_is_down(monkeypatch) -> None:
    def fail_connect(*args, **kwargs):
        raise OSError("down")

    def stop_sleep(seconds: int) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(socket, "create_connection", fail_connect)
    monkeypatch.setattr(observer_client.time, "sleep", stop_sleep)
    with pytest.raises(KeyboardInterrupt):
        observer_client.run("localhost", 8080, None, retry=1)


def test_observer_main_handles_keyboard_interrupt(monkeypatch, capsys) -> None:
    def stop(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(observer_client, "run", stop)
    assert observer_client.main([]) == 0
    assert "finalizado" in capsys.readouterr().err


def test_server_parser_defaults() -> None:
    args = build_parser().parse_args([])
    assert args.port == 8080 and not args.verbose


def test_server_stop_sets_event() -> None:
    class Data:
        def get(self, record_id: str):
            return None

        def list_all(self):
            return []

        def set(self, record_id: str, data: dict):
            return data

    class Log:
        def write(self, **kwargs):
            return kwargs

    server = ApplicationServer("127.0.0.1", 0, data_gateway=Data(), log_gateway=Log())  # type: ignore[arg-type]
    server.stop()
    assert server._stop.is_set()


def test_log_gateway_abstract_behavior() -> None:
    with pytest.raises(NotImplementedError):
        LogGateway().write(action="x")


def test_server_main_handles_oserror(monkeypatch) -> None:
    class FakeServer:
        def __init__(self, port: int):
            self.port = port

        def serve_forever(self) -> None:
            raise OSError("port busy")

    monkeypatch.setattr("tpfi.server.ApplicationServer", FakeServer)
    assert main(["-p", "9999"]) == 1


def test_server_main_handles_keyboard_interrupt(monkeypatch) -> None:
    class FakeServer:
        def __init__(self, port: int):
            self.port = port

        def serve_forever(self) -> None:
            raise KeyboardInterrupt

    monkeypatch.setattr("tpfi.server.ApplicationServer", FakeServer)
    assert main([]) == 0
