"""Servidor TCP SingletonProxyObserverTPFI."""

from __future__ import annotations

import argparse
import contextlib
import logging
import socket
import threading
import uuid
from typing import Any, cast

from .aws_gateway import CorporateDataGateway, CorporateLogGateway
from .observer import SubscriptionManager
from .protocol import ProtocolError, recv_json, send_json
from .proxy import CorporateDataProxy, DataGateway

LOGGER = logging.getLogger(__name__)


class LogGateway:
    """Contrato estructural de la pista auditable."""

    def write(self, **kwargs: Any) -> dict[str, Any]:
        """Escribe una entrada de auditoría."""
        raise NotImplementedError


class ApplicationServer:
    """Servidor concurrente que implementa Proxy + Singleton + Observer."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8080,
        *,
        data_gateway: DataGateway | None = None,
        log_gateway: LogGateway | None = None,
        subscriptions: SubscriptionManager | None = None,
    ) -> None:
        """Inicializa el servidor y sus dependencias."""
        self.host = host
        self.port = port
        self.data_gateway: DataGateway = data_gateway or cast(
            DataGateway, CorporateDataGateway()
        )
        self.log_gateway: LogGateway = log_gateway or cast(
            LogGateway, CorporateLogGateway()
        )
        self.subscriptions = subscriptions or SubscriptionManager()
        self.proxy: CorporateDataProxy = CorporateDataProxy(self.data_gateway)
        self._stop = threading.Event()

    def serve_forever(self) -> None:
        """Escucha conexiones TCP hasta cancelación manual."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.port))
            server.listen()
            server.settimeout(1.0)
            LOGGER.info("Servidor escuchando en %s:%s", self.host, self.port)
            while not self._stop.is_set():
                try:
                    client, address = server.accept()
                except TimeoutError:
                    continue
                LOGGER.debug("Conexión desde %s", address)
                threading.Thread(
                    target=self.handle_client, args=(client,), daemon=True
                ).start()

    def stop(self) -> None:
        """Solicita la finalización del servidor."""
        self._stop.set()

    def handle_client(self, client: socket.socket) -> None:
        """Atiende una solicitud y conserva el socket si es una suscripción."""
        subscribed = False
        try:
            request = recv_json(client)
            if not isinstance(request, dict):
                raise ProtocolError("La solicitud debe ser un objeto JSON")
            cpu_uuid = str(request.get("UUID", "")).strip()
            action = str(request.get("ACTION", "")).strip().lower()
            session_id = str(request.get("SESSION") or uuid.uuid4())
            record_id = str(request.get("ID", "")).strip() or None

            if not cpu_uuid:
                send_json(client, {"status": "Error", "error": "Falta UUID"})
                return

            if action == "subscribe":
                self.subscriptions.subscribe(cpu_uuid, client)
                self.log_gateway.write(
                    cpu_uuid=cpu_uuid,
                    session_id=session_id,
                    action="subscribe",
                    status="OK",
                )
                send_json(client, {"status": "OK", "action": "subscribe"})
                subscribed = True
                return

            try:
                result = self.proxy.execute(request)
            except (ValueError, KeyError) as exc:
                self.log_gateway.write(
                    cpu_uuid=cpu_uuid,
                    session_id=session_id,
                    action=action or "invalid",
                    record_id=record_id,
                    status="Error",
                )
                send_json(client, {"status": "Error", "error": str(exc).strip("'\"")})
                return

            self.log_gateway.write(
                cpu_uuid=cpu_uuid,
                session_id=session_id,
                action=action,
                record_id=record_id,
                status="OK",
            )
            response: dict[str, Any] = {
                "status": "OK",
                "action": action,
                "data": result,
            }
            send_json(client, response)
            if action == "set" and isinstance(result, dict):
                self.subscriptions.notify(
                    {"status": "OK", "action": "set", "data": result}
                )
        except (ConnectionError, OSError, ProtocolError) as exc:
            LOGGER.warning("Cliente finalizado: %s", exc)
        finally:
            if not subscribed:
                with contextlib.suppress(OSError):
                    client.close()


def build_parser() -> argparse.ArgumentParser:
    """Construye los argumentos del servidor."""
    parser = argparse.ArgumentParser(description="SingletonProxyObserverTPFI")
    parser.add_argument("-p", "--port", type=int, default=8080)
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada del servidor."""
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    server = ApplicationServer(port=args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOGGER.info("Servidor detenido por usuario")
    except OSError as exc:
        LOGGER.error("No se pudo iniciar el servidor: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
