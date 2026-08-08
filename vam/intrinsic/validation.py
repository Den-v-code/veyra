"""Shared local semantic checks used during fail-closed VAMI decoding."""

from __future__ import annotations

import logging

from vam.src.intrinsic_ir import IntrinsicIRError, validate_intrinsic_ir

logger = logging.getLogger(__name__)
_MESSAGES = {
    "invalid-mismatch": "mismatch responses are equal",
    "invalid-mismatch-kind": "mismatch response kinds differ",
    "invalid-obstruction": "invalid obstruction path grammar",
}


def decoded_semantic_error(value: object) -> str | None:
    """Return the stable wire error for one locally complete decoded node."""
    logger.debug("decoded_semantic_error entry type=%s", type(value).__name__)
    try:
        validate_intrinsic_ir(value)
    except IntrinsicIRError as error:
        result = _MESSAGES.get(str(error), str(error))
        logger.debug("decoded_semantic_error exit error=%s", result)
        return result
    logger.debug("decoded_semantic_error exit error=none")
    return None
