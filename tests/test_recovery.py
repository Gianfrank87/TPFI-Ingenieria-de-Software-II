"""Pruebas de recuperación del Observer y errores al iniciar el servidor."""

from __future__ import annotations

import socket

import pytest
from fakes import FakeDataGateway, FakeLogGateway

from tpfi import observer_client
from tpfi.server import ApplicationServer


def test_observer_retries_after_server_disconnect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Una desconexión no termina el Observer: intenta suscribirse nuevamente."""
    connections = []
    pauses = []

    class FakeConnection:
        def __enter__(self):
            connections.append(self)
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def settimeout(self, value: object) -> None:
            assert value is None

    def connect(host_port: tuple[str, int], timeout: int) -> FakeConnection:
        assert host_port == ("localhost", 8080)
        assert timeout == 5
        return FakeConnection()

    def receive(sock: FakeConnection) -> dict[str, str]:
        if len(connections) == 1:
            raise ConnectionError("servidor desconectado")
        raise KeyboardInterrupt

    monkeypatch.setattr(observer_client.socket, "create_connection", connect)
    monkeypatch.setattr(observer_client, "send_json", lambda sock, data: None)
    monkeypatch.setattr(observer_client, "recv_json", receive)
    monkeypatch.setattr(observer_client.time, "sleep", pauses.append)

    with pytest.raises(KeyboardInterrupt):
        observer_client.run("localhost", 8080, None, retry=3)
    assert len(connections) == 2
    assert pauses == [3]


def test_second_server_on_same_port_fails_without_harming_first() -> None:
    """El SO impide iniciar dos listeners en una misma dirección y puerto."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as first:
        first.bind(("127.0.0.1", 0))
        first.listen()
        port = first.getsockname()[1]
        second = ApplicationServer(
            host="127.0.0.1",
            port=port,
            data_gateway=FakeDataGateway(),  # type: ignore[arg-type]
            log_gateway=FakeLogGateway(),  # type: ignore[arg-type]
        )
        with pytest.raises(OSError):
            second.serve_forever()
        assert first.fileno() >= 0
