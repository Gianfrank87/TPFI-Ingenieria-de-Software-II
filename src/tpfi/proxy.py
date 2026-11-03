"""Patrón Proxy para el acceso a datos corporativos."""

from __future__ import annotations

from typing import Any, Protocol


class DataGateway(Protocol):
    """Contrato mínimo que debe ofrecer el Singleton de CorporateData."""

    def get(self, record_id: str) -> dict[str, Any] | None:
        """Recupera un registro por id."""
        ...

    def list_all(self) -> list[dict[str, Any]]:
        """Lista todos los registros."""
        ...

    def set(self, record_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Crea o actualiza parcialmente un registro."""
        ...


class CorporateDataProxy:
    """Valida get/set/list antes de delegar al Singleton de acceso físico."""

    def __init__(self, gateway: DataGateway) -> None:
        """Inicializa el proxy con el gateway de acceso a datos."""
        self._gateway = gateway

    def execute(self, request: dict[str, Any]) -> dict[str, Any] | list[dict[str, Any]]:
        """Ejecuta una acción válida o eleva un error de validación."""
        action = str(request.get("ACTION", "")).strip().lower()
        if action not in {"get", "set", "list"}:
            raise ValueError("ACTION debe ser get, set o list")

        if action == "list":
            return self._gateway.list_all()

        record_id = str(request.get("ID", "")).strip()
        if not record_id:
            raise ValueError(f"La acción {action} requiere ID")

        if action == "get":
            item = self._gateway.get(record_id)
            if item is None:
                raise KeyError("Registro inexistente")
            return item

        values = request.get("DATA")
        if values is None:
            values = {
                key: value
                for key, value in request.items()
                if key not in {"UUID", "SESSION", "ACTION", "ID"}
            }
        if not isinstance(values, dict):
            raise ValueError("DATA debe ser un objeto JSON")
        return self._gateway.set(record_id, values)
