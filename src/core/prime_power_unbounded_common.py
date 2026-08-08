"""Hostile-safe candidate primitives for the isolated P3-N6 boundary."""

from __future__ import annotations

import hashlib
import inspect
import logging
from types import MemberDescriptorType
from typing import NamedTuple, NoReturn, cast

logger = logging.getLogger(__name__)


class P3N6ValidationError(ValueError):
    """Malformed input at the candidate P3-N6 trust boundary."""


class FrozenLayoutV1(NamedTuple):
    """Import-time exact class/field layout; never mutable dataclass metadata."""

    expected: type
    fields: tuple[tuple[str, object | None], ...]


_MISSING = object()


def freeze_layout(expected: type, names: tuple[str, ...]) -> FrozenLayoutV1:
    """Freeze literal field names and original slot descriptors without callbacks."""
    logger.debug("freeze_layout entry")
    if type(expected) is not type or type(names) is not tuple or not names:
        raise RuntimeError("invalid trusted P3-N6 layout")
    rows: list[tuple[str, object | None]] = []
    for name in names:
        if type(name) is not str or not name:
            raise RuntimeError("invalid trusted P3-N6 field")
        descriptor = inspect.getattr_static(expected, name, _MISSING)
        if descriptor is _MISSING:
            rows.append((name, None))
        elif type(descriptor) is MemberDescriptorType:
            rows.append((name, descriptor))
        else:
            raise RuntimeError("mutable trusted P3-N6 field descriptor")
    result = FrozenLayoutV1(expected, tuple(rows))
    logger.debug("freeze_layout exit fields=%d", len(rows))
    return result


def reject(message: str) -> NoReturn:
    """Log and reject one malformed boundary value."""
    logger.debug("reject entry")
    if type(message) is not str:
        logger.error("P3-N6 validation failed reason=invalid-internal-reason-type")
        raise P3N6ValidationError("invalid-internal-reason-type")
    logger.error("P3-N6 validation failed reason=%s", message)
    raise P3N6ValidationError(message)


def exact_text(value: object, label: str, *, max_bytes: int = 4096) -> str:
    """Require a bounded exact string without coercion."""
    logger.debug("exact_text entry")
    if type(label) is not str or type(max_bytes) is not int or max_bytes < 0:
        reject("exact-text-internal-contract-invalid")
    logger.debug("exact_text state=contract-validated label=%s", label)
    if type(value) is not str:
        reject(f"{label}-exact-text-required")
    text = value
    try:
        encoded = text.encode("utf-8", "strict")
    except UnicodeError:
        reject(f"{label}-utf8-invalid")
    if not encoded or len(encoded) > max_bytes:
        reject(f"{label}-text-length-invalid")
    logger.debug("exact_text exit label=%s bytes=%d", label, len(encoded))
    return text


def exact_digest(value: object, label: str) -> str:
    """Require one lowercase SHA-256 identity."""
    logger.debug("exact_digest entry")
    if type(label) is not str:
        reject("exact-digest-internal-contract-invalid")
    logger.debug("exact_digest state=contract-validated label=%s", label)
    if type(value) is not str:
        reject(f"{label}-digest-invalid")
    candidate = value
    if len(candidate) != 64 or any(
        char not in "0123456789abcdef" for char in candidate
    ):
        reject(f"{label}-digest-invalid")
    logger.debug("exact_digest exit label=%s", label)
    return candidate


def exact_nonnegative_int(value: object, label: str, *, maximum: int) -> int:
    """Require a bounded nonnegative builtin integer, never bool/subclass."""
    logger.debug("exact_nonnegative_int entry")
    if type(label) is not str or type(maximum) is not int or maximum < 0:
        reject("exact-integer-internal-contract-invalid")
    logger.debug("exact_nonnegative_int state=contract-validated label=%s", label)
    if type(value) is not int or value < 0 or value > maximum:
        reject(f"{label}-integer-invalid")
    logger.debug("exact_nonnegative_int exit label=%s value=%d", label, value)
    return value


def exact_bytes(value: object, label: str, *, maximum: int) -> bytes:
    """Require bounded immutable builtin bytes."""
    logger.debug("exact_bytes entry")
    if type(label) is not str or type(maximum) is not int or maximum < 0:
        reject("exact-bytes-internal-contract-invalid")
    logger.debug("exact_bytes state=contract-validated label=%s", label)
    if type(value) is not bytes:
        reject(f"{label}-bytes-invalid")
    payload = value
    if len(payload) > maximum:
        reject(f"{label}-bytes-invalid")
    logger.debug("exact_bytes exit label=%s bytes=%d", label, len(payload))
    return payload


def exact_shape(value: object, layout: FrozenLayoutV1, label: str) -> dict[str, object]:
    """Read a frozen literal layout; reject class-descriptor drift before access."""
    logger.debug("exact_shape entry")
    if type(layout) is not FrozenLayoutV1 or type(label) is not str:
        reject("exact-shape-internal-contract-invalid")
    expected, rows = layout
    logger.debug("exact_shape state=contract-validated label=%s", label)
    if type(value) is not expected:
        reject(f"{label}-exact-type-required")
    try:
        result: dict[str, object] = {}
        dictionary_items: tuple[tuple[object, object], ...] = ()
        if any(descriptor is None for _, descriptor in rows):
            namespace = object.__getattribute__(value, "__dict__")
            if type(namespace) is not dict:
                reject(f"{label}-dictionary-invalid")
            dictionary_items = tuple(dict.items(namespace))
            if (
                len(dictionary_items) != len(rows)
                or any(type(key) is not str for key, _ in dictionary_items)
            ):
                reject(f"{label}-field-names-invalid")
            actual_names = tuple(cast(str, key) for key, _ in dictionary_items)
            if any(name not in actual_names for name, _ in rows):
                reject(f"{label}-fields-missing")
        for name, frozen_descriptor in rows:
            current = inspect.getattr_static(expected, name, _MISSING)
            if frozen_descriptor is None:
                if current is not _MISSING:
                    reject(f"{label}-descriptor-drift")
                result[name] = next(
                    item for key, item in dictionary_items if key == name
                )
            else:
                if current is not frozen_descriptor:
                    reject(f"{label}-descriptor-drift")
                result[name] = MemberDescriptorType.__get__(
                    cast(MemberDescriptorType, frozen_descriptor), value, expected
                )
    except (AttributeError, TypeError):
        reject(f"{label}-fields-missing")
    logger.debug("exact_shape exit label=%s fields=%d", label, len(result))
    return result


def exact_text_tuple(
    value: object, label: str, *, maximum_items: int, item_max_bytes: int = 4096
) -> tuple[str, ...]:
    """Require a bounded tuple of exact strings."""
    logger.debug("exact_text_tuple entry")
    if (
        type(label) is not str
        or type(maximum_items) is not int
        or maximum_items < 0
        or type(item_max_bytes) is not int
        or item_max_bytes < 0
    ):
        reject("exact-text-tuple-internal-contract-invalid")
    logger.debug("exact_text_tuple state=contract-validated label=%s", label)
    if type(value) is not tuple or len(value) > maximum_items:
        reject(f"{label}-tuple-invalid")
    items = cast(tuple[object, ...], value)
    result = tuple(
        exact_text(item, f"{label}-{index}", max_bytes=item_max_bytes)
        for index, item in enumerate(items)
    )
    logger.debug("exact_text_tuple exit label=%s items=%d", label, len(result))
    return result


def sha(payload: bytes) -> str:
    """Hash exact captured bytes."""
    logger.debug("sha entry")
    if type(payload) is not bytes:
        reject("sha-exact-bytes-required")
    logger.debug("sha state validated bytes=%d", len(payload))
    result = hashlib.sha256(payload).hexdigest()
    logger.debug("sha exit")
    return result


def frame(domain: str, rows: tuple[tuple[str, bytes], ...]) -> bytes:
    """Encode one ordered length-framed domain-separated transcript."""
    logger.debug("frame entry")
    exact_text(domain, "frame-domain", max_bytes=4096)
    if type(rows) is not tuple or len(rows) > 4096:
        reject("frame-rows-invalid")
    output = bytearray()
    domain_bytes = domain.encode("utf-8")
    output.extend(len(domain_bytes).to_bytes(8, "big"))
    output.extend(domain_bytes)
    for index, row in enumerate(rows):
        if type(row) is not tuple or len(row) != 2:
            reject(f"frame-row-{index}-invalid")
        label, value = row
        exact_text(label, f"frame-label-{index}", max_bytes=4096)
        exact_bytes(value, f"frame-value-{index}", maximum=16 * 1024 * 1024)
        for item in (label.encode("utf-8"), value):
            output.extend(len(item).to_bytes(8, "big"))
            output.extend(item)
    result = bytes(output)
    logger.debug("frame exit rows=%d bytes=%d", len(rows), len(result))
    return result


def digest(domain: str, rows: tuple[tuple[str, bytes], ...]) -> str:
    """Hash one exact ordered transcript."""
    logger.debug("digest entry")
    exact_text(domain, "digest-domain", max_bytes=4096)
    logger.debug("digest state domain-validated")
    result = sha(frame(domain, rows))
    logger.debug("digest exit")
    return result
