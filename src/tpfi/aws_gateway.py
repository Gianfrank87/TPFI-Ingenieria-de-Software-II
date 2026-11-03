"""Acceso Singleton a las tablas DynamoDB requeridas por la consigna."""

from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from typing import Any, ClassVar, cast
from uuid import uuid4

import boto3
from boto3.resources.base import ServiceResource

from .config import CORPORATE_DATA_TABLE, CORPORATE_LOG_TABLE


class _SingletonTableGateway:
    """Base Singleton thread-safe para encapsular un recurso DynamoDB."""

    _instances: ClassVar[dict[type, _SingletonTableGateway]] = {}
    _lock: ClassVar[Lock] = Lock()
    table_name: ClassVar[str]

    def __new__(cls, *args: Any, **kwargs: Any) -> _SingletonTableGateway:
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]

    def __init__(self, resource: ServiceResource | None = None) -> None:
        if getattr(self, "_initialized", False):
            return
        self._resource = resource or boto3.resource("dynamodb")
        dynamodb_resource = cast(Any, self._resource)
        self.table = dynamodb_resource.Table(self.table_name)
        self._initialized = True

    @classmethod
    def _reset_singleton_for_tests(cls) -> None:
        """Reinicia la instancia únicamente para aislamiento de pruebas."""
        instance = cls._instances.pop(cls, None)
        if instance is not None and hasattr(instance, "_initialized"):
            delattr(instance, "_initialized")


class CorporateDataGateway(_SingletonTableGateway):
    """Singleton de acceso a la tabla CorporateData."""

    table_name = CORPORATE_DATA_TABLE

    def get(self, record_id: str) -> dict[str, Any] | None:
        """Obtiene un registro por su clave ``id``."""
        response = self.table.get_item(Key={"id": record_id})
        item = response.get("Item")
        return dict(item) if item is not None else None

    def list_all(self) -> list[dict[str, Any]]:
        """Lista todos los registros, incluyendo páginas sucesivas de DynamoDB."""
        items: list[dict[str, Any]] = []
        response = self.table.scan()
        items.extend(response.get("Items", []))
        while "LastEvaluatedKey" in response:
            response = self.table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))
        return items

    def set(self, record_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Crea o actualiza parcialmente un registro y devuelve su estado final."""
        clean = {key: value for key, value in data.items() if key != "id"}
        current = self.get(record_id) or {"id": record_id}
        current.update(clean)
        self.table.put_item(Item=current)
        return current


class CorporateLogGateway(_SingletonTableGateway):
    """Singleton de acceso a la tabla CorporateLog."""

    table_name = CORPORATE_LOG_TABLE

    def write(
        self,
        *,
        cpu_uuid: str,
        session_id: str,
        action: str,
        record_id: str | None = None,
        status: str = "OK",
    ) -> dict[str, Any]:
        """Escribe una pista auditable de una operación."""
        item: dict[str, Any] = {
            "id": str(uuid4()),
            "UUID": cpu_uuid,
            "session": session_id,
            "action": action,
            "timestamp": datetime.now(UTC).isoformat(),
            "status": status,
        }
        if record_id is not None:
            item["record_id"] = record_id
        self.table.put_item(Item=item)
        return item
