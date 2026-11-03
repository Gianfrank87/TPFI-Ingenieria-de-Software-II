from __future__ import annotations

from typing import Any

from tpfi.aws_gateway import CorporateDataGateway, CorporateLogGateway


class FakeResource:
    def __init__(self) -> None:
        self.tables: dict[str, FakeTable] = {}

    def Table(self, name: str) -> FakeTable:  # noqa: N802 - API boto3
        return self.tables.setdefault(name, FakeTable(name))


class FakeTable:
    def __init__(self, name: str) -> None:
        self.name = name
        self.items: dict[str, dict[str, Any]] = {}
        self.puts: list[dict[str, Any]] = []

    def get_item(self, Key: dict[str, str]) -> dict[str, Any]:  # noqa: N803
        item = self.items.get(Key["id"])
        return {"Item": dict(item)} if item else {}

    def put_item(self, Item: dict[str, Any]) -> dict[str, Any]:  # noqa: N803
        self.puts.append(dict(Item))
        if "id" in Item:
            self.items[str(Item["id"])] = dict(Item)
        return {}

    def scan(self, **kwargs: Any) -> dict[str, Any]:
        return {"Items": list(self.items.values())}


def test_data_gateway_is_singleton_and_operates() -> None:
    CorporateDataGateway._reset_singleton_for_tests()
    resource = FakeResource()
    first = CorporateDataGateway(resource)  # type: ignore[arg-type]
    second = CorporateDataGateway(resource)  # type: ignore[arg-type]
    assert first is second
    first.set("A", {"cp": "3260"})
    assert first.get("A") == {"id": "A", "cp": "3260"}
    assert first.list_all() == [{"id": "A", "cp": "3260"}]


def test_log_gateway_is_singleton_and_writes() -> None:
    CorporateLogGateway._reset_singleton_for_tests()
    resource = FakeResource()
    first = CorporateLogGateway(resource)  # type: ignore[arg-type]
    second = CorporateLogGateway(resource)  # type: ignore[arg-type]
    assert first is second
    item = first.write(cpu_uuid="cpu", session_id="s", action="get", record_id="A")
    assert item["UUID"] == "cpu"
    assert len(first.table.puts) == 1
