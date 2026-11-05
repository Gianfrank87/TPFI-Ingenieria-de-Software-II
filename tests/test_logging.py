"""Regresiones de observabilidad sin acceso a AWS."""

import json
import logging
import socket
import subprocess
import sys
import threading

import pytest
from botocore.exceptions import ClientError
from test_server import invoke, make_server

from tpfi import client, observer_client
from tpfi.logging_setup import configure_logging, redact, safe_label
from tpfi.protocol import recv_json, send_json


@pytest.mark.parametrize(
    "action,record_id", [("get", "UADER-FCyT-IS2"), ("list", None), ("set", "own")]
)
def test_operations_logged_after_audit(caplog, action, record_id):
    caplog.set_level(logging.INFO, logger="tpfi")
    server, _, log = make_server()
    payload = {"UUID": "cpu-demo", "ACTION": action, "DATA": {"cp": "1"}}
    if record_id:
        payload["ID"] = record_id
    assert invoke(server, payload)["status"] == "OK"
    assert len(log.entries) == 1
    assert f"{action.upper()} recibido: UUID=cpu-demo" in caplog.text
    assert "validado y ejecutado correctamente" in caplog.text
    assert f"CorporateLog: {action.upper()} registrado" in caplog.text
    assert "Conexión de cliente cerrada" in caplog.text
    if action == "set":
        assert "Registro modificado mediante SET: own" in caplog.text
        assert "Notificaciones entregadas por TCP: 0" in caplog.text


def test_subscription_and_notification_logs(caplog):
    caplog.set_level(logging.INFO, logger="tpfi")
    server, _, _ = make_server()
    peer, service = socket.socketpair()
    try:
        send_json(peer, {"UUID": "watcher", "ACTION": "subscribe"})
        server.handle_client(service)
        assert recv_json(peer)["action"] == "subscribe"
        assert "Suscripción validada y confirmada" in caplog.text
        assert "observadores registrados: 1" in caplog.text
        invoke(server, {"UUID": "cpu", "ACTION": "set", "ID": "own", "DATA": {}})
        assert recv_json(peer)["data"]["id"] == "own"
        assert "Notificaciones entregadas por TCP: 1" in caplog.text
    finally:
        peer.close()
        server.subscriptions.unsubscribe("watcher")


@pytest.mark.parametrize(
    "payload", [{"ACTION": "list"}, {"UUID": "cpu", "ACTION": "get"}]
)
def test_validation_failures_not_announced_as_success(caplog, payload):
    caplog.set_level(logging.INFO, logger="tpfi")
    server, _, _ = make_server()
    assert invoke(server, payload)["status"] == "Error"
    assert "correctamente" not in caplog.text
    assert "fallida" in caplog.text or "rechazada" in caplog.text


def test_audit_failure_does_not_claim_success_or_leave_subscription(
    caplog, monkeypatch
):
    caplog.set_level(logging.INFO, logger="tpfi")
    server, _, log = make_server()

    def fail(**kwargs):
        raise ClientError(
            {"Error": {"Code": "Denied", "Message": "hidden-secret"}}, "PutItem"
        )

    monkeypatch.setattr(log, "write", fail)
    peer, service = socket.socketpair()
    try:
        send_json(peer, {"UUID": "watcher", "ACTION": "subscribe"})
        server.handle_client(service)
        assert server.subscriptions.count == 0
        assert "Error de acceso" in caplog.text
        assert "hidden-secret" not in caplog.text
        assert "CorporateLog: SUBSCRIBE registrado" not in caplog.text
        assert "confirmada" not in caplog.text
    finally:
        peer.close()


def test_listener_connection_and_stop_logs(caplog):
    caplog.set_level(logging.INFO, logger="tpfi")
    server, _, _ = make_server()
    # Reserve a free TCP port, then start the actual accept loop.
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        server.port = probe.getsockname()[1]
    ready = threading.Event()
    original = server.handle_client

    def handle(sock):
        original(sock)
        server.stop()
        ready.set()

    server.handle_client = handle
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        # A bounded wait on the log avoids arbitrary startup sleeps.
        import time

        deadline = time.monotonic() + 3
        while "Servidor escuchando" not in caplog.text:
            assert time.monotonic() < deadline
            threading.Event().wait(0.01)
        assert (
            client.request_server(
                {"UUID": "cpu", "ACTION": "list"}, "127.0.0.1", server.port
            )["status"]
            == "OK"
        )
        assert ready.wait(3)
    finally:
        server.stop()
        thread.join(3)
    assert not thread.is_alive()
    assert "Cliente conectado: 127.0.0.1:" in caplog.text
    assert "Servidor detenido" in caplog.text


def test_observer_reconnect_ack_and_event_logs(monkeypatch, caplog, capsys):
    caplog.set_level(logging.INFO, logger="tpfi")
    events = iter(
        [
            {"status": "OK", "action": "subscribe"},
            {"action": "set", "data": {"id": "own", "password": "hidden-secret"}},
            ConnectionError(),
            {"status": "OK", "action": "subscribe"},
            KeyboardInterrupt(),
        ]
    )
    from unittest.mock import MagicMock

    sock = MagicMock()
    sock.__enter__.return_value = sock
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: sock)
    monkeypatch.setattr(observer_client, "send_json", lambda *a: None)

    def receive(sock):
        event = next(events)
        if isinstance(event, BaseException):
            raise event
        return event

    monkeypatch.setattr(observer_client, "recv_json", receive)
    monkeypatch.setattr(observer_client.time, "sleep", lambda seconds: None)
    with pytest.raises(KeyboardInterrupt):
        observer_client.run("localhost", 8080, None, 1)
    for text in (
        "Conectando",
        "Conexión TCP establecida",
        "SUBSCRIBE enviada",
        "Suscripción confirmada",
        "SET recibido: ID=own",
        "Servidor desconectado",
        "Reconexión TCP establecida",
    ):
        assert text in caplog.text
    assert "hidden-secret" not in capsys.readouterr().out
    assert caplog.text.count("Suscripción confirmada") == 2


def test_rejected_subscription_is_not_confirmed(monkeypatch, caplog):
    from unittest.mock import MagicMock

    caplog.set_level(logging.INFO, logger="tpfi")
    sock = MagicMock()
    sock.__enter__.return_value = sock
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: sock)
    monkeypatch.setattr(observer_client, "send_json", lambda *a: None)
    monkeypatch.setattr(observer_client, "recv_json", lambda *a: {"status": "Error"})

    def stop(seconds):
        raise KeyboardInterrupt

    monkeypatch.setattr(observer_client.time, "sleep", stop)
    with pytest.raises(KeyboardInterrupt):
        observer_client.run("localhost", 8080, None)
    assert "Suscripción confirmada" not in caplog.text
    assert "Reintento" in caplog.text


def test_cli_logging_stderr_and_clean_json_stdout(tmp_path):
    source = tmp_path / "input.json"
    source.write_text('{"UUID":"demo","ACTION":"list"}', encoding="utf-8")
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()

        def respond():
            sock, _ = listener.accept()
            with sock:
                recv_json(sock)
                send_json(sock, {"status": "OK", "data": []})

        thread = threading.Thread(target=respond, daemon=True)
        thread.start()
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tpfi.client",
                "-i",
                str(source),
                "-s",
                "127.0.0.1",
                "-p",
                str(listener.getsockname()[1]),
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        thread.join(3)
    assert result.returncode == 0
    assert json.loads(result.stdout) == {"status": "OK", "data": []}
    for text in (
        "[CLIENT] Conectando",
        "Conexión TCP establecida",
        "list enviado",
        "Respuesta recibida",
        "Conexión cerrada",
    ):
        assert text in result.stderr


def test_connection_error_logs(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger="tpfi")

    def fail(*a, **k):
        raise ConnectionRefusedError("hidden-secret")

    monkeypatch.setattr(socket, "create_connection", fail)
    with pytest.raises(ConnectionRefusedError):
        client.request_server({}, "localhost", 8080)
    assert "Error de comunicación" in caplog.text
    assert "hidden-secret" not in caplog.text
    assert "Conexión cerrada" not in caplog.text


@pytest.mark.parametrize("verbose", [True, False])
def test_logging_levels_and_dependency_noise(verbose):
    names = ("tpfi", "boto3", "botocore", "urllib3", "s3transfer")
    levels = {name: logging.getLogger(name).level for name in names}
    try:
        configure_logging("SERVER", verbose)
        assert logging.getLogger("tpfi").level == (
            logging.DEBUG if verbose else logging.INFO
        )
        assert all(
            logging.getLogger(name).level == logging.WARNING for name in names[1:]
        )
    finally:
        for name, level in levels.items():
            logging.getLogger(name).setLevel(level)


def test_safe_metadata_and_nested_redaction():
    assert "\n" not in safe_label("cpu\nforged")
    assert len(safe_label("x" * 1000)) == 160
    assert redact({"data": [{"token": "hidden", "id": "own"}]}) == {
        "data": [{"token": "[REDACTED]", "id": "own"}]
    }
