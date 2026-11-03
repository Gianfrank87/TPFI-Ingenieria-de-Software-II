"""Gestión del patrón Observer para clientes suscriptos."""

from __future__ import annotations

import contextlib
import socket
import threading
from typing import Any

from .protocol import send_json


class SubscriptionManager:
    """Subject del patrón Observer que administra observadores por UUID."""

    def __init__(self) -> None:
        """Inicializa el registro de suscriptores y el bloqueo de concurrencia."""
        self._subscribers: dict[str, socket.socket] = {}
        self._lock = threading.Lock()

    def subscribe(self, cpu_uuid: str, sock: socket.socket) -> None:
        """Suscribe un UUID; si ya existía, reemplaza y cierra el socket anterior."""
        previous: socket.socket | None = None
        with self._lock:
            previous = self._subscribers.get(cpu_uuid)
            self._subscribers[cpu_uuid] = sock
        if previous is not None and previous is not sock:
            with contextlib.suppress(OSError):
                previous.close()

    def unsubscribe(self, subscriber: str | socket.socket) -> None:
        """Elimina una subscripción por UUID o por socket."""
        removed: socket.socket | None = None
        with self._lock:
            if isinstance(subscriber, str):
                removed = self._subscribers.pop(subscriber, None)
            else:
                for cpu_uuid, sock in list(self._subscribers.items()):
                    if sock is subscriber:
                        removed = self._subscribers.pop(cpu_uuid)
                        break
        if removed is not None:
            with contextlib.suppress(OSError):
                removed.close()

    def notify(self, payload: dict[str, Any]) -> int:
        """Notifica a todos y elimina automáticamente conexiones caídas."""
        with self._lock:
            subscribers = list(self._subscribers.items())
        delivered = 0
        failed: list[str] = []
        for cpu_uuid, sock in subscribers:
            try:
                send_json(sock, payload)
                delivered += 1
            except OSError:
                failed.append(cpu_uuid)
        for cpu_uuid in failed:
            self.unsubscribe(cpu_uuid)
        return delivered

    @property
    def count(self) -> int:
        """Cantidad actual de observadores."""
        with self._lock:
            return len(self._subscribers)


class ObserverManager(SubscriptionManager):
    """Alias semántico usado por la implementación principal del TPFI."""
