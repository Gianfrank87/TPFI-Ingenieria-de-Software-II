"""Servidor TCP SingletonProxyObserverTPFI."""

from __future__ import annotations

import argparse
import contextlib
import logging
import socket
import threading
import uuid
from typing import Any, cast

from botocore.exceptions import BotoCoreError, ClientError

from .aws_gateway import CorporateDataGateway, CorporateLogGateway
from .logging_setup import configure_logging, safe_label
from .observer import SubscriptionManager
from .protocol import ProtocolError, recv_json, send_json
from .proxy import CorporateDataProxy, DataGateway

LOGGER = logging.getLogger("tpfi.server")


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
            LOGGER.info("Servidor escuchando en %s:%s", *server.getsockname())
            while not self._stop.is_set():
                try:
                    client, address = server.accept()
                except TimeoutError:
                    continue
                LOGGER.info("Cliente conectado: %s:%s", *address)
                threading.Thread(
                    target=self.handle_client, args=(client,), daemon=True
                ).start()
        LOGGER.info("Servidor detenido")

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
            LOGGER.info(
                "%s recibido: UUID=%s ID=%s",
                safe_label(action.upper()),
                safe_label(cpu_uuid),
                safe_label(record_id),
            )

            if not cpu_uuid:
                LOGGER.info("Validación fallida: falta UUID")
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
                LOGGER.info(
                    "CorporateLog: SUBSCRIBE registrado UUID=%s", safe_label(cpu_uuid)
                )
                send_json(client, {"status": "OK", "action": "subscribe"})
                subscribed = True
                LOGGER.info(
                    "Suscripción validada y confirmada: UUID=%s", safe_label(cpu_uuid)
                )
                LOGGER.info(
                    "Observer registrado; observadores registrados: %s",
                    self.subscriptions.count,
                )
                return

            try:
                result = self.proxy.execute(request)
            except (ValueError, KeyError) as exc:
                LOGGER.info("Solicitud rechazada: %s", type(exc).__name__)
                self.log_gateway.write(
                    cpu_uuid=cpu_uuid,
                    session_id=session_id,
                    action=action or "invalid",
                    record_id=record_id,
                    status="Error",
                )
                LOGGER.info(
                    "CorporateLog: error registrado UUID=%s", safe_label(cpu_uuid)
                )
                send_json(client, {"status": "Error", "error": str(exc).strip("'\"")})
                return

            LOGGER.info(
                "%s validado y ejecutado correctamente", safe_label(action.upper())
            )
            if action == "set":
                LOGGER.info(
                    "Registro modificado mediante SET: %s", safe_label(record_id)
                )
            self.log_gateway.write(
                cpu_uuid=cpu_uuid,
                session_id=session_id,
                action=action,
                record_id=record_id,
                status="OK",
            )
            LOGGER.info(
                "CorporateLog: %s registrado UUID=%s",
                safe_label(action.upper()),
                safe_label(cpu_uuid),
            )
            response: dict[str, Any] = {
                "status": "OK",
                "action": action,
                "data": result,
            }
            send_json(client, response)
            if action == "set" and isinstance(result, dict):
                delivered = self.subscriptions.notify(
                    {"status": "OK", "action": "set", "data": result}
                )
                LOGGER.info(
                    "Notificaciones entregadas por TCP: %s; "
                    "observadores registrados: %s",
                    delivered,
                    self.subscriptions.count,
                )
        except (ConnectionError, OSError, ProtocolError) as exc:
            LOGGER.warning("Error de comunicación/solicitud: %s", type(exc).__name__)
        except (BotoCoreError, ClientError) as exc:
            LOGGER.error(
                "Error de acceso a datos o CorporateLog: %s", type(exc).__name__
            )
        finally:
            if not subscribed:
                self.subscriptions.unsubscribe(client)
                with contextlib.suppress(OSError):
                    client.close()
                LOGGER.info("Conexión de cliente cerrada")


def build_parser() -> argparse.ArgumentParser:
    """Construye los argumentos del servidor."""
    parser = argparse.ArgumentParser(description="SingletonProxyObserverTPFI")
    parser.add_argument("-p", "--port", type=int, default=8080)
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada del servidor."""
    args = build_parser().parse_args(argv)
    configure_logging("SERVER", args.verbose)
    server = ApplicationServer(port=args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOGGER.info("Servidor detenido por usuario")
    except OSError as exc:
        LOGGER.error("No se pudo iniciar el servidor: %s", type(exc).__name__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
