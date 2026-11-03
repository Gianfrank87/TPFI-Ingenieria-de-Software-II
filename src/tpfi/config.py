"""Configuración central del proyecto."""

from __future__ import annotations

import os

DEFAULT_HOST = os.getenv("TPFI_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("TPFI_PORT", "8080"))
DEFAULT_RETRY_SECONDS = int(os.getenv("TPFI_RETRY_SECONDS", "30"))
CORPORATE_DATA_TABLE = os.getenv("TPFI_DATA_TABLE", "CorporateData")
CORPORATE_LOG_TABLE = os.getenv("TPFI_LOG_TABLE", "CorporateLog")
