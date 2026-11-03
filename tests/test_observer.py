from __future__ import annotations

import json

from tpfi.observer import SubscriptionManager


class FakeSocket:
    def __init__(self, fail: bool = False) -> None:
        self.data = bytearray()
        self.closed = False
        self.fail = fail

    def sendall(self, data: bytes) -> None:
        if self.fail:
            raise OSError("caído")
        self.data.extend(data)

    def close(self) -> None:
        self.closed = True


def test_subscribe_notify_unsubscribe() -> None:
    manager = SubscriptionManager()
    sock = FakeSocket()
    manager.subscribe("cpu-1", sock)  # type: ignore[arg-type]
    assert manager.count == 1
    assert manager.notify({"status": "OK"}) == 1
    assert json.loads(bytes(sock.data).decode().strip())["status"] == "OK"
    manager.unsubscribe("cpu-1")
    assert manager.count == 0
    assert sock.closed


def test_failed_subscriber_is_removed() -> None:
    manager = SubscriptionManager()
    sock = FakeSocket(fail=True)
    manager.subscribe("cpu-1", sock)  # type: ignore[arg-type]
    assert manager.notify({"x": 1}) == 0
    assert manager.count == 0


def test_resubscribe_replaces_old_socket() -> None:
    manager = SubscriptionManager()
    first, second = FakeSocket(), FakeSocket()
    manager.subscribe("cpu", first)  # type: ignore[arg-type]
    manager.subscribe("cpu", second)  # type: ignore[arg-type]
    assert first.closed
    assert manager.count == 1


def test_unsubscribe_unknown_is_idempotent() -> None:
    manager = SubscriptionManager()
    manager.unsubscribe("missing")
    assert manager.count == 0
