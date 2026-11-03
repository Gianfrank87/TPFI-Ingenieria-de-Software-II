"""Configuración común de pytest."""

from __future__ import annotations

import sys
from pathlib import Path

import boto3
import botocore.endpoint
import botocore.session
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(autouse=True)
def block_real_aws(monkeypatch: pytest.MonkeyPatch) -> None:
    """Impide leer credenciales o realizar llamadas AWS durante las pruebas."""

    def blocked(*args: object, **kwargs: object) -> None:
        raise AssertionError("AWS real está bloqueado: usar gateways falsos")

    monkeypatch.setattr(boto3, "resource", blocked)
    monkeypatch.setattr(boto3, "client", blocked)
    monkeypatch.setattr(botocore.session.Session, "get_credentials", blocked)
    monkeypatch.setattr(botocore.endpoint.Endpoint, "make_request", blocked)
