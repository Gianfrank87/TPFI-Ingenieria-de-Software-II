from __future__ import annotations

import socket

import pytest

from tpfi.protocol import recv_json, send_json


def test_protocol_roundtrip() -> None:
    left, right = socket.socketpair()
    try:
        send_json(left, {"hola": "mundo"})
        assert recv_json(right) == {"hola": "mundo"}
    finally:
        left.close()
        right.close()


def test_recv_closed_connection() -> None:
    left, right = socket.socketpair()
    left.close()
    try:
        with pytest.raises(ConnectionError):
            recv_json(right)
    finally:
        right.close()
