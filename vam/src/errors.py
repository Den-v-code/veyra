"""Stable VAM v1.1 error taxonomy helpers.

This module intentionally does not raise or wrap interpreter/bytecode errors.
It only classifies the exception/message strings already emitted by the
reference Python path into JSON-serializable rows for reports and tests.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

ERROR_PROFILE = "vam-error-taxonomy-v1.1"
CATEGORIES = ("frame", "decode", "execution", "boundary")
TAXONOMY: dict[str, list[str]] = {
    "frame": ["short_frame", "magic", "version", "length", "crc32", "unknown"],
    "decode": ["payload", "payload_shape", "instruction_row", "argument_item", "unknown"],
    "execution": ["destination_register", "unsupported_instruction", "unknown"],
    "boundary": ["argument_type", "obstruction", "native_boundary", "unknown"],
}

JsonDict = dict[str, Any]

_MESSAGE_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("short VAM0 frame", "frame", "short_frame"),
    ("bad VAM0 magic", "frame", "magic"),
    ("unsupported VAM0 version", "frame", "version"),
    ("VAM0 payload length mismatch", "frame", "length"),
    ("VAM0 checksum mismatch", "frame", "crc32"),
    ("bad VAM0 payload", "decode", "payload"),
    ("VAM0 payload must be a list", "decode", "payload_shape"),
    ("bad instruction row", "decode", "instruction_row"),
    ("bad argument item", "decode", "argument_item"),
    ("unsupported argument type", "boundary", "argument_type"),
    ("first operand must be destination register", "execution", "destination_register"),
    ("unsupported or malformed instruction", "execution", "unsupported_instruction"),
)

_EXCEPTION_DEFAULTS: dict[str, tuple[str, str]] = {
    "VamBytecodeError": ("decode", "unknown"),
    "VamExecutionError": ("execution", "unknown"),
}


def classify_message(message: str) -> tuple[str, str]:
    """Classify an existing VAM error message as ``(category, kind)``."""
    logger.debug("classify_message entry chars=%d", len(message))
    for marker, category, kind in _MESSAGE_PATTERNS:
        if marker in message:
            logger.debug("classify_message exit category=%s kind=%s", category, kind)
            return category, kind
    logger.debug("classify_message exit category=boundary kind=unknown")
    return "boundary", "unknown"


def error_row(error: BaseException | str, *, source: str = "python") -> JsonDict:
    """Map an existing exception or message to a stable JSON row."""
    message = str(error)
    logger.debug("error_row entry source=%s error_type=%s", source, type(error).__name__)
    category, kind = classify_message(message)
    if kind == "unknown" and isinstance(error, BaseException):
        category, kind = _EXCEPTION_DEFAULTS.get(type(error).__name__, (category, kind))
    row = _row(category, kind, message, source=source)
    logger.debug("error_row exit code=%s", row["code"])
    return row


def boundary_error_row(kind: str, message: str, *, source: str = "boundary") -> JsonDict:
    """Build a stable row for host/native/API boundary errors."""
    logger.debug("boundary_error_row entry source=%s kind=%s", source, kind)
    normalized = _normalize_kind(kind)
    row = _row("boundary", normalized, message, source=source)
    logger.debug("boundary_error_row exit code=%s", row["code"])
    return row


def obstruction_error_row(claim: str, *, source: str = "obstruction") -> JsonDict:
    """Represent a VAM obstruction claim as a boundary-category error row."""
    logger.debug("obstruction_error_row entry source=%s claim=%s", source, claim)
    row = _row("boundary", "obstruction", claim, source=source)
    logger.debug("obstruction_error_row exit code=%s", row["code"])
    return row


def _row(category: str, kind: str, message: str, *, source: str) -> JsonDict:
    if category not in CATEGORIES:
        raise ValueError(f"unknown VAM error category: {category}")
    stable_kind = _normalize_kind(kind)
    return {
        "profile": ERROR_PROFILE,
        "category": category,
        "kind": stable_kind,
        "code": f"{category}.{stable_kind}",
        "source": str(source),
        "message": str(message),
    }


def _normalize_kind(value: str) -> str:
    token = value.strip().lower().replace("-", "_").replace(" ", "_")
    token = "".join(char for char in token if char.isalnum() or char == "_").strip("_")
    return token or "unknown"
