from __future__ import annotations

import pytest
from fakes import FakeDataGateway

from tpfi.proxy import CorporateDataProxy


def test_get_happy_path() -> None:
    proxy = CorporateDataProxy(FakeDataGateway())
    result = proxy.execute({"ACTION": "get", "ID": "UADER-FCyT-IS2"})
    assert result["localidad"] == "Concepción del Uruguay"


def test_list_happy_path() -> None:
    proxy = CorporateDataProxy(FakeDataGateway())
    assert len(proxy.execute({"ACTION": "list"})) == 1


def test_set_updates_and_creates() -> None:
    gateway = FakeDataGateway()
    proxy = CorporateDataProxy(gateway)
    updated = proxy.execute(
        {"ACTION": "set", "ID": "UADER-FCyT-IS2", "DATA": {"cp": "3260"}}
    )
    created = proxy.execute({"ACTION": "set", "ID": "NUEVO", "telefono": "123"})
    assert updated["cp"] == "3260"
    assert created == {"id": "NUEVO", "telefono": "123"}


@pytest.mark.parametrize(
    "payload", [{}, {"ACTION": "delete"}, {"ACTION": "get"}, {"ACTION": "set"}]
)
def test_invalid_requests(payload: dict[str, str]) -> None:
    proxy = CorporateDataProxy(FakeDataGateway())
    with pytest.raises(ValueError):
        proxy.execute(payload)


def test_get_missing_record() -> None:
    proxy = CorporateDataProxy(FakeDataGateway())
    with pytest.raises(KeyError):
        proxy.execute({"ACTION": "get", "ID": "NO-EXISTE"})
