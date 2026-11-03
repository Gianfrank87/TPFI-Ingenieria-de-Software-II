"""Dobles de prueba para aislar AWS."""

from __future__ import annotations

from typing import Any


class FakeDataGateway:
    def __init__(self) -> None:
        self.records: dict[str, dict[str, Any]] = {
            "UADER-FCyT-IS2": {
                "id": "UADER-FCyT-IS2",
                "localidad": "Concepción del Uruguay",
            }
        }

    def get(self, record_id: str) -> dict[str, Any] | None:
        record = self.records.get(record_id)
        return dict(record) if record else None

    def list_all(self) -> list[dict[str, Any]]:
        return [dict(value) for value in self.records.values()]

    def set(self, record_id: str, data: dict[str, Any]) -> dict[str, Any]:
        item = self.records.get(record_id, {"id": record_id})
        item = {**item, **data, "id": record_id}
        self.records[record_id] = item
        return dict(item)


class FakeLogGateway:
    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    def write(self, **kwargs: Any) -> dict[str, Any]:
        self.entries.append(dict(kwargs))
        return dict(kwargs)
