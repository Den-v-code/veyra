"""Tagged length-prefixed commitments for the P2-S meta-calculus."""

from __future__ import annotations

from hashlib import sha256
import logging

logger = logging.getLogger(__name__)


def frame(domain: str, fields: tuple[tuple[str, bytes], ...]) -> bytes:
    logger.debug("frame entry domain=%s fields=%d", domain, len(fields))
    out = bytearray(b"VEYRA-P2-S\x00")
    _token(out, b"domain", domain.encode())
    _token(out, b"count", len(fields).to_bytes(8, "big"))
    for tag, value in fields:
        _token(out, tag.encode(), value)
    result = bytes(out)
    logger.debug("frame exit domain=%s bytes=%d", domain, len(result))
    return result


def _token(out: bytearray, tag: bytes, value: bytes) -> None:
    logger.debug("_token entry tag=%d value=%d", len(tag), len(value))
    out.extend(len(tag).to_bytes(4, "big"))
    out.extend(tag)
    out.extend(len(value).to_bytes(8, "big"))
    out.extend(value)
    logger.debug("_token exit")


def digest(domain: str, fields: tuple[tuple[str, bytes], ...]) -> str:
    logger.debug("digest entry domain=%s", domain)
    result = sha256(frame(domain, fields)).hexdigest()
    logger.debug("digest exit domain=%s", domain)
    return result


def text_rows(prefix: str, rows: tuple[str, ...]) -> tuple[tuple[str, bytes], ...]:
    logger.debug("text_rows entry prefix=%s rows=%d", prefix, len(rows))
    result = ((f"{prefix}-count", len(rows).to_bytes(8, "big")),) + tuple(
        (f"{prefix}-{index}", value.encode()) for index, value in enumerate(rows)
    )
    logger.debug("text_rows exit prefix=%s", prefix)
    return result


def nested_rows(prefix: str, rows: tuple[bytes, ...]) -> tuple[tuple[str, bytes], ...]:
    logger.debug("nested_rows entry prefix=%s rows=%d", prefix, len(rows))
    result = ((f"{prefix}-count", len(rows).to_bytes(8, "big")),) + tuple(
        (f"{prefix}-{index}", value) for index, value in enumerate(rows)
    )
    logger.debug("nested_rows exit prefix=%s", prefix)
    return result
