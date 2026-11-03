"""Pruebas de argumentos y helpers de clientes."""

from __future__ import annotations

from tpfi.client import build_parser as client_parser
from tpfi.observer_client import build_parser as observer_parser
from tpfi.observer_client import subscription_payload


def test_client_arguments() -> None:
    args = client_parser().parse_args(["-i", "input.json"])
    assert args.port == 8080 and args.host == "localhost"


def test_observer_defaults_and_payload() -> None:
    args = observer_parser().parse_args([])
    assert args.port == 8080 and args.retry == 30
    payload = subscription_payload()
    assert payload["ACTION"] == "subscribe"
    assert payload["UUID"]
    assert payload["SESSION"]


def test_client_main_success_writes_output(tmp_path, monkeypatch, capsys) -> None:
    import json

    import tpfi.client as client

    source = tmp_path / "input.json"
    target = tmp_path / "output.json"
    source.write_text(json.dumps({"UUID": "cpu", "ACTION": "list"}), encoding="utf-8")
    monkeypatch.setattr(
        client, "request_server", lambda payload, host, port: {"status": "OK"}
    )
    assert client.main(["-i", str(source), "-o", str(target)]) == 0
    assert '"status": "OK"' in target.read_text(encoding="utf-8")
    assert '"status": "OK"' in capsys.readouterr().out


def test_client_main_rejects_invalid_json(tmp_path, capsys) -> None:
    import tpfi.client as client

    source = tmp_path / "bad.json"
    source.write_text("{bad", encoding="utf-8")
    assert client.main(["-i", str(source)]) == 1
    assert "Error" in capsys.readouterr().err


def test_request_server_roundtrip(monkeypatch) -> None:
    import socket
    import threading

    import tpfi.client as client
    from tpfi.protocol import recv_json, send_json

    left, right = socket.socketpair()

    class ContextSocket:
        def __enter__(self):
            return left

        def __exit__(self, *args):
            left.close()

    monkeypatch.setattr(
        socket, "create_connection", lambda *args, **kwargs: ContextSocket()
    )

    def service() -> None:
        req = recv_json(right)
        send_json(right, {"echo": req["ACTION"]})
        right.close()

    thread = threading.Thread(target=service)
    thread.start()
    assert client.request_server({"ACTION": "list"}, "localhost", 8080) == {
        "echo": "list"
    }
    thread.join(timeout=2)
