"""Canonical, resource-bounded codec for ``veyra.observer-core.v2``."""

from __future__ import annotations

from hashlib import sha256
import json
import logging
from typing import NoReturn

from .observer_core_semantics import ObserverCoreError, infer_observer_kind
from .observer_core_types import Apply, Input, ObserverExpr, Pair, PrimitiveId

logger = logging.getLogger(__name__)
SCHEMA_ID = "veyra.observer-core.v2"
MAX_OBSERVER_BYTES = 65_536


class ObserverCodecError(ValueError):
    """A deterministic canonical-codec rejection."""


def _reject(reason: str) -> NoReturn:
    logger.error("observer codec rejected reason=%s", reason)
    raise ObserverCodecError(reason)


def _raw_observer(observer: ObserverExpr) -> dict[str, object]:
    logger.debug("_raw_observer entry type=%s", type(observer).__name__)
    infer_observer_kind(observer)
    stack: list[tuple[bool, object]] = [(False, observer)]
    values: list[dict[str, object]] = []
    while stack:
        exiting, node = stack.pop()
        if not exiting:
            stack.append((True, node))
            if type(node) is Apply:
                stack.append((False, node.child))
            elif type(node) is Pair:
                stack.append((False, node.right))
                stack.append((False, node.left))
            continue
        if type(node) is Input:
            values.append({"tag": "input"})
        elif type(node) is Apply:
            values.append({"child": values.pop(), "primitive": node.primitive.value, "tag": "apply"})
        else:
            right, left = values.pop(), values.pop()
            values.append({"left": left, "right": right, "tag": "pair"})
    if len(values) != 1:
        _reject("invalid-observer-shape")
    result = values[0]
    logger.debug("_raw_observer exit tag=%s", result["tag"])
    return result


def canonical_observer_bytes(observer: ObserverExpr) -> bytes:
    """Encode one validated AST as its unique canonical JSON byte string."""
    logger.debug("canonical_observer_bytes entry type=%s", type(observer).__name__)
    try:
        raw = {"observer": _raw_observer(observer), "schema": SCHEMA_ID}
        result = json.dumps(raw, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("ascii")
    except (ObserverCodecError, ObserverCoreError):
        raise
    except (RecursionError, TypeError, ValueError) as exc:
        logger.error("canonical_observer_bytes encoding failed type=%s", type(exc).__name__)
        _reject("encoding-failure")
    if len(result) > MAX_OBSERVER_BYTES:
        _reject("observer-byte-limit")
    logger.debug("canonical_observer_bytes exit bytes=%d", len(result))
    return result


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    logger.debug("_unique_object entry pairs=%d", len(pairs))
    result: dict[str, object] = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            _reject("duplicate-or-invalid-key")
        result[key] = value
    logger.debug("_unique_object exit keys=%d", len(result))
    return result


def _decode_raw(raw: object) -> ObserverExpr:
    logger.debug("_decode_raw entry type=%s", type(raw).__name__)
    stack: list[tuple[bool, object, int]] = [(False, raw, 0)]
    values: list[ObserverExpr] = []
    while stack:
        exiting, node, depth = stack.pop()
        if not exiting:
            if type(node) is not dict or type(node.get("tag")) is not str:
                _reject("invalid-node")
            tag = node["tag"]
            if tag == "input":
                if set(node) != {"tag"}:
                    _reject("invalid-input-keys")
            elif tag == "apply":
                if set(node) != {"tag", "primitive", "child"}:
                    _reject("invalid-apply-keys")
                if type(node["primitive"]) is not str or node["primitive"] not in {item.value for item in PrimitiveId}:
                    _reject("invalid-primitive")
            elif tag == "pair":
                if set(node) != {"tag", "left", "right"}:
                    _reject("invalid-pair-keys")
            else:
                _reject("unknown-tag")
            stack.append((True, node, depth))
            if tag == "apply":
                stack.append((False, node["child"], depth + 1))
            elif tag == "pair":
                stack.append((False, node["right"], depth + 1))
                stack.append((False, node["left"], depth + 1))
            continue
        tag = node["tag"]
        if tag == "input":
            values.append(Input())
        elif tag == "apply":
            values.append(Apply(PrimitiveId(node["primitive"]), values.pop()))
        else:
            right, left = values.pop(), values.pop()
            values.append(Pair(left, right))
    if len(values) != 1:
        _reject("invalid-observer-shape")
    result = values[0]
    infer_observer_kind(result)
    logger.debug("_decode_raw exit type=%s", type(result).__name__)
    return result


def decode_observer(data: bytes) -> ObserverExpr:
    """Decode only exact canonical bytes for the versioned observer schema."""
    logger.debug("decode_observer entry type=%s", type(data).__name__)
    if type(data) is not bytes:
        _reject("observer-bytes-required")
    if not data or len(data) > MAX_OBSERVER_BYTES:
        _reject("observer-byte-limit")
    try:
        text = data.decode("utf-8", errors="strict")
        raw = json.loads(text, object_pairs_hook=_unique_object)
    except ObserverCodecError:
        raise
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        logger.error("decode_observer parse failed type=%s", type(exc).__name__)
        _reject("invalid-json")
    if type(raw) is not dict or set(raw) != {"schema", "observer"} or type(raw.get("schema")) is not str:
        _reject("invalid-envelope")
    if raw["schema"] != SCHEMA_ID:
        _reject("unsupported-schema")
    result = _decode_raw(raw["observer"])
    if canonical_observer_bytes(result) != data:
        _reject("noncanonical-json")
    logger.debug("decode_observer exit type=%s", type(result).__name__)
    return result


def observer_digest(observer: ObserverExpr) -> str:
    """Return the SHA-256 identity of the canonical versioned AST."""
    logger.debug("observer_digest entry type=%s", type(observer).__name__)
    result = sha256(canonical_observer_bytes(observer)).hexdigest()
    logger.debug("observer_digest exit digest=%s", result[:12])
    return result
