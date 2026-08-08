"""Independent byte difference and checked KCI1 coordinate rebasing for KIE1."""

from __future__ import annotations

import logging
from types import MemberDescriptorType
from typing import Protocol, cast

from . import omegaa_keb1_common as _keb_common
from . import omegaa_kie1_types as _types
from . import omegaa_kpt1_common as _kpt_common
from .omegaa_kie1_common import (
    KIEPayloadOriginV1,
    _checked_add_u64,
    _checked_u64,
    _integrity_error,
    validate_kie1_common_integrity_v1,
)
from .omegaa_kpt1_common import KPT1DecodeCodeV1

logger = logging.getLogger(__name__)
_LOGGER = logger
_ORIGIN_CLASS = KIEPayloadOriginV1
_KPT_CODE_CLASS = KPT1DecodeCodeV1
_KPT_CODES_FROZEN = tuple(_KPT_CODE_CLASS(index) for index in range(11))
_KPT_CODES = _KPT_CODES_FROZEN
_REBASED_CLASS = _types.KIEKPTDecodeAtInputV1
_REBASED_SLOTS_FROZEN = tuple(vars(_REBASED_CLASS)["__slots__"])
_REBASED_SLOTS = _REBASED_SLOTS_FROZEN
_REBASED_DESCRIPTORS_FROZEN = tuple(
    vars(_REBASED_CLASS)[name] for name in _REBASED_SLOTS_FROZEN
)
_REBASED_DESCRIPTORS = _REBASED_DESCRIPTORS_FROZEN
_REBASED_INIT = vars(_REBASED_CLASS)["__init__"]
_REBASED_POST = vars(_REBASED_CLASS)["__post_init__"]
_REBASED_INIT_CODE = _REBASED_INIT.__code__
_REBASED_POST_CODE = _REBASED_POST.__code__
_REBASED_KEYS_FROZEN = frozenset(vars(_REBASED_CLASS))
_REBASED_KEYS = _REBASED_KEYS_FROZEN
_OBJECT_NEW = object.__new__
_KEB_FIRST_DIFF = _keb_common.FirstUnsignedDifferenceV1
_KEB_FIRST_DIFF_CODE = _KEB_FIRST_DIFF.__code__
_VALIDATE_COMMON = validate_kie1_common_integrity_v1
_VALIDATE_COMMON_CODE = _VALIDATE_COMMON.__code__
_CHECK_U64 = _checked_u64
_CHECK_U64_CODE = _CHECK_U64.__code__
_ADD_U64 = _checked_add_u64
_ADD_U64_CODE = _ADD_U64.__code__
_INTEGRITY_ERROR = _integrity_error
_INTEGRITY_ERROR_CODE = _INTEGRITY_ERROR.__code__


class _SlotSetter(Protocol):
    def __set__(self, instance: object, value: object) -> None: ...


def validate_kie1_offsets_integrity_v1() -> None:
    """Refuse helper, enum, DTO, slot, hook, allocator, or KEB FirstDiff drift."""
    _LOGGER.debug("validate_kie1_offsets_integrity_v1 entry")
    namespace = vars(_REBASED_CLASS)
    drift = (
        globals().get("logger") is not _LOGGER
        or globals().get("KIEPayloadOriginV1") is not _ORIGIN_CLASS
        or globals().get("KPT1DecodeCodeV1") is not _KPT_CODE_CLASS
        or vars(_kpt_common).get("KPT1DecodeCodeV1") is not _KPT_CODE_CLASS
        or globals().get("_KPT_CODES") is not _KPT_CODES_FROZEN
        or len(_KPT_CODES_FROZEN) != 11
        or any(
            type(code) is not _KPT_CODE_CLASS
            or code is not _KPT_CODE_CLASS(index)
            or type(object.__getattribute__(code, "_value_")) is not int
            or object.__getattribute__(code, "_value_") != index
            for index, code in enumerate(_KPT_CODES_FROZEN)
        )
        or vars(_types).get("KIEKPTDecodeAtInputV1") is not _REBASED_CLASS
        or globals().get("_REBASED_SLOTS") is not _REBASED_SLOTS_FROZEN
        or globals().get("_REBASED_DESCRIPTORS") is not _REBASED_DESCRIPTORS_FROZEN
        or globals().get("_REBASED_KEYS") is not _REBASED_KEYS_FROZEN
        or _REBASED_SLOTS_FROZEN != ("code", "absolute_kci_offset")
        or len(_REBASED_DESCRIPTORS_FROZEN) != 2
        or tuple(namespace.get("__slots__", ())) != _REBASED_SLOTS_FROZEN
        or frozenset(namespace) != _REBASED_KEYS_FROZEN
        or namespace.get("__init__") is not _REBASED_INIT
        or namespace.get("__post_init__") is not _REBASED_POST
        or _REBASED_INIT.__code__ is not _REBASED_INIT_CODE
        or _REBASED_POST.__code__ is not _REBASED_POST_CODE
        or any(
            namespace.get(name) is not descriptor or type(descriptor) is not MemberDescriptorType
            for name, descriptor in zip(
                _REBASED_SLOTS_FROZEN,
                _REBASED_DESCRIPTORS_FROZEN,
                strict=True,
            )
        )
        or object.__new__ is not _OBJECT_NEW
        or vars(_keb_common).get("FirstUnsignedDifferenceV1") is not _KEB_FIRST_DIFF
        or _KEB_FIRST_DIFF.__code__ is not _KEB_FIRST_DIFF_CODE
        or globals().get("validate_kie1_common_integrity_v1") is not _VALIDATE_COMMON
        or _VALIDATE_COMMON.__code__ is not _VALIDATE_COMMON_CODE
        or globals().get("_checked_u64") is not _CHECK_U64
        or _CHECK_U64.__code__ is not _CHECK_U64_CODE
        or globals().get("_checked_add_u64") is not _ADD_U64
        or _ADD_U64.__code__ is not _ADD_U64_CODE
        or globals().get("_integrity_error") is not _INTEGRITY_ERROR
        or _INTEGRITY_ERROR.__code__ is not _INTEGRITY_ERROR_CODE
    )
    if drift:
        _LOGGER.error("validate_kie1_offsets_integrity_v1 error drift")
        _INTEGRITY_ERROR("kie1-offsets-integrity")
    _VALIDATE_COMMON()
    _LOGGER.debug("validate_kie1_offsets_integrity_v1 exit")


_VALIDATE_OFFSETS = validate_kie1_offsets_integrity_v1
_VALIDATE_OFFSETS_CODE = _VALIDATE_OFFSETS.__code__


def FirstUnsignedDifferenceV1(left: bytes, right: bytes) -> int | None:
    """Return least unequal unsigned-byte index, length split, or None iff equal."""
    _LOGGER.debug(
        "FirstUnsignedDifferenceV1 entry left=%d right=%d",
        len(left) if type(left) is bytes else -1,
        len(right) if type(right) is bytes else -1,
    )
    _VALIDATE_OFFSETS()
    if type(left) is not bytes or type(right) is not bytes:
        _LOGGER.error("FirstUnsignedDifferenceV1 error host-shape")
        _INTEGRITY_ERROR("kie1-first-difference-host-shape")
    stop = min(len(left), len(right))
    for index in range(stop):
        if left[index] != right[index]:
            _LOGGER.debug("FirstUnsignedDifferenceV1 exit index=%d", index)
            return index
    if len(left) != len(right):
        _LOGGER.debug("FirstUnsignedDifferenceV1 exit prefix_index=%d", stop)
        return stop
    _LOGGER.debug("FirstUnsignedDifferenceV1 exit equal=true")
    return None


_FIRST_DIFF = FirstUnsignedDifferenceV1
_FIRST_DIFF_CODE = _FIRST_DIFF.__code__


def _base_v1(origin: KIEPayloadOriginV1, expected_bytes: bytes) -> int:
    """Return Base(EXPECTED,E)=14 or Base(TERM,E)=22+|E|."""
    _LOGGER.debug("_base_v1 entry")
    _VALIDATE_OFFSETS()
    if type(origin) is not _ORIGIN_CLASS or type(expected_bytes) is not bytes:
        _LOGGER.error("_base_v1 error host-shape")
        _INTEGRITY_ERROR("kie1-origin-host-shape")
    expected_length = _CHECK_U64(len(expected_bytes), "expected-length")
    if origin is _ORIGIN_CLASS.EXPECTED:
        result = 14
    elif origin is _ORIGIN_CLASS.TERM:
        result = _ADD_U64(22, expected_length, "term-base")
    else:
        _INTEGRITY_ERROR("kie1-origin-ordinal")
    _LOGGER.debug("_base_v1 exit base=%d", result)
    return result


_BASE = _base_v1
_BASE_CODE = _BASE.__code__


def _allocate_rebased_v1(code: KPT1DecodeCodeV1, absolute_offset: int) -> _types.KIEKPTDecodeAtInputV1:
    """Allocate a fresh exact rebased DTO without executing class hooks."""
    _LOGGER.debug("_allocate_rebased_v1 entry")
    _VALIDATE_OFFSETS()
    if type(code) is not _KPT_CODE_CLASS or not any(
        code is member for member in _KPT_CODES_FROZEN
    ):
        _LOGGER.error("_allocate_rebased_v1 error code-type")
        _INTEGRITY_ERROR("kie1-kpt-code-host-shape")
    checked_offset = _CHECK_U64(absolute_offset, "rebased-offset")
    result = _OBJECT_NEW(_REBASED_CLASS)
    cast(_SlotSetter, _REBASED_DESCRIPTORS_FROZEN[0]).__set__(result, code)
    cast(_SlotSetter, _REBASED_DESCRIPTORS_FROZEN[1]).__set__(result, checked_offset)
    _LOGGER.debug("_allocate_rebased_v1 exit")
    return result


_ALLOCATE_REBASED = _allocate_rebased_v1
_ALLOCATE_REBASED_CODE = _ALLOCATE_REBASED.__code__


def RebaseKPTV1(
    origin: KIEPayloadOriginV1,
    decode: tuple[KPT1DecodeCodeV1, int],
    expected_bytes: bytes,
) -> _types.KIEKPTDecodeAtInputV1:
    """Preserve an exact KPT1 code while rebasing its relative offset into KCI1."""
    _LOGGER.debug("RebaseKPTV1 entry")
    if (
        globals().get("_base_v1") is not _BASE
        or _BASE.__code__ is not _BASE_CODE
        or globals().get("_allocate_rebased_v1") is not _ALLOCATE_REBASED
        or _ALLOCATE_REBASED.__code__ is not _ALLOCATE_REBASED_CODE
    ):
        _INTEGRITY_ERROR("kie1-rebase-helper-integrity")
    _VALIDATE_OFFSETS()
    if type(decode) is not tuple or len(decode) != 2:
        _LOGGER.error("RebaseKPTV1 error decode-shape")
        _INTEGRITY_ERROR("kie1-kpt-decode-host-shape")
    code, relative_offset = decode
    if type(code) is not _KPT_CODE_CLASS:
        _LOGGER.error("RebaseKPTV1 error code-type")
        _INTEGRITY_ERROR("kie1-kpt-decode-host-shape")
    base = _BASE(origin, expected_bytes)
    absolute_offset = _ADD_U64(base, _CHECK_U64(relative_offset, "relative-kpt-offset"), "kpt-origin")
    result = _ALLOCATE_REBASED(code, absolute_offset)
    _LOGGER.debug("RebaseKPTV1 exit")
    return result


def RebaseSuppliedSemanticOriginV1(
    origin: KIEPayloadOriginV1,
    relative_tag_offset: int,
    expected_bytes: bytes,
) -> int:
    """Rebase a checker-supplied canonical node-tag offset without navigation."""
    _LOGGER.debug("RebaseSuppliedSemanticOriginV1 entry")
    if globals().get("_base_v1") is not _BASE or _BASE.__code__ is not _BASE_CODE:
        _INTEGRITY_ERROR("kie1-semantic-origin-helper-integrity")
    base = _BASE(origin, expected_bytes)
    result = _ADD_U64(
        base,
        _CHECK_U64(relative_tag_offset, "relative-tag-offset"),
        "semantic-origin",
    )
    _LOGGER.debug("RebaseSuppliedSemanticOriginV1 exit offset=%d", result)
    return result


__all__ = (
    "FirstUnsignedDifferenceV1",
    "RebaseKPTV1",
    "RebaseSuppliedSemanticOriginV1",
    "validate_kie1_offsets_integrity_v1",
)
