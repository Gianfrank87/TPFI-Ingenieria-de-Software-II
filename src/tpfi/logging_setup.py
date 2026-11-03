"""Configuración común para las terminales de la defensa."""

from __future__ import annotations

import logging
from typing import Any


def configure_logging(component: str, verbose: bool) -> None:
    """Configura stderr y limita el ruido de dependencias."""
    logging.basicConfig(
        level=logging.WARNING,
        format=f"[{component}] %(message)s",
    )
    logging.getLogger("tpfi").setLevel(logging.DEBUG if verbose else logging.INFO)
    for name in ("boto3", "botocore", "urllib3", "s3transfer"):
        logging.getLogger(name).setLevel(logging.WARNING)


def safe_label(value: object) -> str:
    """Evita inyección de líneas y limita metadatos de solicitudes."""
    return str(value).encode("unicode_escape").decode("ascii")[:160]


def redact(payload: Any) -> Any:
    """Oculta campos sensibles en notificaciones mostradas por el Observer."""
    if isinstance(payload, dict):
        return {
            key: (
                "[REDACTED]"
                if any(
                    word in str(key).lower()
                    for word in (
                        "password",
                        "secret",
                        "token",
                        "credential",
                        "access_key",
                        "authorization",
                        "contraseña",
                        "contrasena",
                    )
                )
                else redact(value)
            )
            for key, value in payload.items()
        }
    if isinstance(payload, list):
        return [redact(value) for value in payload]
    return payload
