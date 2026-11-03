from __future__ import annotations

import socket

from fakes import FakeDataGateway, FakeLogGateway

from tpfi.observer import SubscriptionManager
from tpfi.protocol import recv_json, send_json
from tpfi.server import ApplicationServer


def invoke(server: ApplicationServer, payload: dict[str, object]) -> dict[str, object]:
    client, service = socket.socketpair()
    try:
        send_json(client, payload)
        server.handle_client(service)
        response = recv_json(client)
        assert isinstance(response, dict)
        return response
    finally:
        client.close()


def make_server() -> tuple[ApplicationServer, FakeDataGateway, FakeLogGateway]:
    data = FakeDataGateway()
    log = FakeLogGateway()
    server = ApplicationServer(
        "127.0.0.1",
        0,
        data_gateway=data,  # type: ignore[arg-type]
        log_gateway=log,  # type: ignore[arg-type]
        subscriptions=SubscriptionManager(),
    )
    return server, data, log


def test_get_and_log() -> None:
    server, _, log = make_server()
    response = invoke(server, {"UUID": "cpu", "ACTION": "get", "ID": "UADER-FCyT-IS2"})
    assert response["status"] == "OK"
    assert log.entries[0]["action"] == "get"


def test_list_and_set() -> None:
    server, data, log = make_server()
    listed = invoke(server, {"UUID": "cpu", "ACTION": "list"})
    changed = invoke(
        server, {"UUID": "cpu", "ACTION": "set", "ID": "X", "DATA": {"cp": "3260"}}
    )
    assert listed["status"] == "OK"
    assert changed["status"] == "OK"
    assert data.records["X"]["cp"] == "3260"
    assert [entry["action"] for entry in log.entries] == ["list", "set"]


def test_invalid_request_returns_error() -> None:
    server, _, _ = make_server()
    response = invoke(server, {"UUID": "cpu", "ACTION": "get"})
    assert response["status"] == "Error"


def test_missing_uuid_returns_error() -> None:
    server, _, _ = make_server()
    response = invoke(server, {"ACTION": "list"})
    assert response["status"] == "Error"


def test_subscribe_receives_ack_and_update() -> None:
    server, _, _ = make_server()
    observer_client, observer_service = socket.socketpair()
    try:
        send_json(observer_client, {"UUID": "observer", "ACTION": "subscribe"})
        server.handle_client(observer_service)
        ack = recv_json(observer_client)
        assert ack["status"] == "OK"
        assert server.subscriptions.count == 1
        invoke(server, {"UUID": "cpu", "ACTION": "set", "ID": "X", "DATA": {"cp": "1"}})
        notification = recv_json(observer_client)
        assert notification["action"] == "set"
    finally:
        observer_client.close()
        server.subscriptions.unsubscribe("observer")
