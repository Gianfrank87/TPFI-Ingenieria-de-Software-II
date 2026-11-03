"""Pruebas del Observer y del protocolo de sockets."""

from __future__ import annotations

import socket

from tpfi.observer import ObserverManager
from tpfi.protocol import recv_json


def test_observer_notifies_subscriber() -> None:
    manager = ObserverManager()
    server_side, client_side = socket.socketpair()
    try:
        manager.subscribe("cpu", server_side)
        assert manager.count == 1
        assert manager.notify({"event": "set", "data": {"id": "A"}}) == 1
        assert recv_json(client_side) == {"event": "set", "data": {"id": "A"}}
        manager.unsubscribe(server_side)
        assert manager.count == 0
    finally:
        server_side.close()
        client_side.close()
