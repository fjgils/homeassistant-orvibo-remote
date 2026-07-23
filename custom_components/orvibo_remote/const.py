"""Constants for Orvibo Remote."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "orvibo_remote"
PLATFORMS: Final = ["remote"]

CONF_HOST: Final = "host"
CONF_MODEL_HINT: Final = "model_hint"
CONF_ENABLE_RF: Final = "enable_rf"
CONF_TIMEOUT: Final = "timeout"
CONF_CODE_NAME: Final = "code_name"
CONF_CODE: Final = "code"
CONF_PROTOCOL: Final = "protocol"
CONF_ENTRY_ID: Final = "entry_id"
CONF_LEGACY_STATE: Final = "state"

DEFAULT_NAME: Final = "Orvibo AllOne remote"
DEFAULT_TIMEOUT: Final = 15

MODEL_AUTO: Final = "auto"
MODEL_ALLONE: Final = "allone"
MODEL_ALLONE_PRO: Final = "allone_pro"
SUPPORTED_MODEL_HINTS: Final = [MODEL_AUTO, MODEL_ALLONE, MODEL_ALLONE_PRO]

PROTOCOL_IR: Final = "ir"
PROTOCOL_RF: Final = "rf"

SERVICE_LEARN_IR: Final = "learn_ir"
SERVICE_SEND_IR: Final = "send_ir"
SERVICE_LEARN_RF: Final = "learn_rf"
SERVICE_SEND_RF: Final = "send_rf"
SERVICE_LIST_CODES: Final = "list_codes"
SERVICE_DELETE_CODE: Final = "delete_code"

LEGACY_SERVICE_LEARN: Final = "learn"
LEGACY_SERVICE_EMIT: Final = "emit"

STORAGE_VERSION: Final = 1
STORAGE_KEY: Final = f"{DOMAIN}_codes"
DATA_CLIENTS: Final = f"{DOMAIN}_clients"
DATA_STORES: Final = f"{DOMAIN}_stores"
DATA_COORDINATORS: Final = f"{DOMAIN}_coordinators"
DATA_SERVICES_REGISTERED: Final = f"{DOMAIN}_services_registered"
