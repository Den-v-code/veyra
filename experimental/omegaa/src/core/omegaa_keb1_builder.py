"""Captured hook-free construction for canonical KEB1 syntax."""

from __future__ import annotations

import logging
from types import MemberDescriptorType
from typing import Protocol, TypeVar, cast

from . import omegaa_keb1_common as _common
from . import omegaa_keb1_types as _syntax
from . import omegaa_kpt1_codec as _kpt_codec_module
from . import omegaa_kpt1_types as _kpt_syntax
from .omegaa_keb1_common import KEB1DecodeCodeV1, KEB1ResourceKindV1, U64_LIMIT, _integrity_error

logger = logging.getLogger(__name__)
_LOGGER = logger
_SYNTAX = _syntax
_COMMON = _common
_DECODE_ENUM = KEB1DecodeCodeV1
_RESOURCE_ENUM = KEB1ResourceKindV1
_U64_LIMIT = U64_LIMIT
_KPT_SYNTAX = _kpt_syntax
_KPT_CODEC_MODULE = _kpt_codec_module
_BINDING_CLASS = _syntax.ExpectedBindingSyntaxV1
_KPT_CLASS = _kpt_syntax.KernelProofTermV1
_BINDING_INIT = vars(_BINDING_CLASS)["__init__"]
_BINDING_POST = vars(_BINDING_CLASS)["__post_init__"]
_BINDING_INIT_CODE = _BINDING_INIT.__code__
_BINDING_POST_CODE = _BINDING_POST.__code__
_BINDING_KEYS = frozenset(vars(_BINDING_CLASS))
_BINDING_SLOTS = tuple(vars(_BINDING_CLASS)["__slots__"])
_BINDING_FINAL = vars(_BINDING_CLASS).get("__final__")
_SYNTAX_LOGGER = _syntax.logger
_TERM_SLOT = vars(_BINDING_CLASS)["expected_term"]
_WIRE_SLOT = vars(_BINDING_CLASS)["expected_wire"]
_KPT_CODEC = _kpt_codec_module.codec_kernel_proof_term_v1
_KPT_CODEC_CODE = _KPT_CODEC.__code__
_KPT_CODEC_NS = vars(_KPT_CODEC_MODULE)
_KPT_FUNCTION_NAMES = ("_check_slot_descriptors", "_mag_size", "_preflight", "_u64", "_frame")
_KPT_FUNCTIONS = tuple(_KPT_CODEC_NS[name] for name in _KPT_FUNCTION_NAMES)
_KPT_FUNCTION_CODES = tuple(function.__code__ for function in _KPT_FUNCTIONS)
_KPT_STATIC_NAMES = (
    "_snapshot_limits", "_resource", "_host_error", "_slot", "_FIELD_KINDS",
    "KernelLevelTagV1", "KernelProofTermV1", "KernelTermTagV1",
    "KernelUniverseLevelV1", "kpt1_level_arity_v1", "kpt1_level_ordinal_v1",
    "kpt1_term_ordinal_v1", "validate_kpt1_enum_integrity_v1", "KPT1_PREFIX",
    "MAX_DEPTH", "MAX_LIST", "MAX_NAT", "MAX_NODES", "MAX_OUTPUT", "logger",
)
_KPT_STATICS = tuple(_KPT_CODEC_NS[name] for name in _KPT_STATIC_NAMES)
_OBJECT_NEW_FROZEN = object.__new__
_OBJECT_NEW = _OBJECT_NEW_FROZEN
_BYTES_CLASS_FROZEN = bytes
_RESULT_CLASSES = (
    _syntax.KEB1DecodeErrorV1, _syntax.KEB1ResourceResultV1,
    _syntax.KEB1DecodedResultV1, _syntax.KEB1DecodeErrorResultV1,
    _syntax.KEB1ResourceParseResultV1,
)
_RESULT_NAMES = (
    "KEB1DecodeErrorV1", "KEB1ResourceResultV1", "KEB1DecodedResultV1",
    "KEB1DecodeErrorResultV1", "KEB1ResourceParseResultV1",
)
_RESULT_KEYS = tuple(frozenset(vars(cls)) for cls in _RESULT_CLASSES)
_RESULT_SLOTS = tuple(tuple(vars(cls)["__slots__"]) for cls in _RESULT_CLASSES)
_RESULT_DESCRIPTORS = tuple(tuple(vars(cls)[name] for name in slots) for cls, slots in zip(_RESULT_CLASSES, _RESULT_SLOTS, strict=True))
_RESULT_INITS = tuple(vars(cls)["__init__"] for cls in _RESULT_CLASSES)
_RESULT_INIT_CODES = tuple(init.__code__ for init in _RESULT_INITS)
_RESULT_POSTS = tuple(vars(cls)["__post_init__"] for cls in _RESULT_CLASSES)
_RESULT_POST_CODES = tuple(post.__code__ for post in _RESULT_POSTS)
_RESULT_FINALS = tuple(vars(cls).get("__final__") for cls in _RESULT_CLASSES)
_INTEGRITY_FROZEN = _integrity_error
_INTEGRITY_CODE = _INTEGRITY_FROZEN.__code__


class _SlotSetter(Protocol):
    def __set__(self, instance: object, value: object) -> None: ...


def validate_keb1_builder_integrity_v1() -> None:
    """Reject class, generated-hook, slot, alias or KPT codec drift."""
    _LOGGER.debug("validate_keb1_builder_integrity_v1 entry")
    namespace = vars(_BINDING_CLASS)
    drift = (
        globals().get("logger") is not _LOGGER
        or globals().get("_syntax") is not _SYNTAX
        or globals().get("_common") is not _COMMON
        or vars(_COMMON).get("KEB1DecodeCodeV1") is not _DECODE_ENUM
        or vars(_COMMON).get("KEB1ResourceKindV1") is not _RESOURCE_ENUM
        or vars(_COMMON).get("U64_LIMIT") != _U64_LIMIT or _U64_LIMIT != 18446744073709551616
        or globals().get("_kpt_syntax") is not _KPT_SYNTAX
        or globals().get("_kpt_codec_module") is not _KPT_CODEC_MODULE
        or vars(_SYNTAX).get("ExpectedBindingSyntaxV1") is not _BINDING_CLASS
        or vars(_KPT_SYNTAX).get("KernelProofTermV1") is not _KPT_CLASS
        or vars(_KPT_CODEC_MODULE).get("codec_kernel_proof_term_v1") is not _KPT_CODEC
        or _KPT_CODEC.__code__ is not _KPT_CODEC_CODE
        or any(_KPT_CODEC_NS.get(name) is not function or function.__code__ is not code for name, function, code in zip(_KPT_FUNCTION_NAMES, _KPT_FUNCTIONS, _KPT_FUNCTION_CODES, strict=True))
        or any(_KPT_CODEC_NS.get(name) is not value for name, value in zip(_KPT_STATIC_NAMES, _KPT_STATICS, strict=True))
        or namespace.get("__init__") is not _BINDING_INIT
        or namespace.get("__post_init__") is not _BINDING_POST
        or _BINDING_INIT.__code__ is not _BINDING_INIT_CODE
        or _BINDING_POST.__code__ is not _BINDING_POST_CODE
        or frozenset(namespace) != _BINDING_KEYS
        or tuple(namespace.get("__slots__", ())) != _BINDING_SLOTS
        or namespace.get("expected_term") is not _TERM_SLOT
        or namespace.get("expected_wire") is not _WIRE_SLOT
        or namespace.get("__final__") is not _BINDING_FINAL or _BINDING_FINAL is not True
        or vars(_SYNTAX).get("logger") is not _SYNTAX_LOGGER
        or globals().get("ExpectedBindingSyntaxV1") not in (None, _BINDING_CLASS)
        or globals().get("_OBJECT_NEW") is not _OBJECT_NEW_FROZEN
        or object.__new__ is not _OBJECT_NEW_FROZEN
        or globals().get("_BYTES_CLASS_FROZEN") is not bytes
        or globals().get("_integrity_error") is not _INTEGRITY_FROZEN
        or _INTEGRITY_FROZEN.__code__ is not _INTEGRITY_CODE
        or any(vars(_SYNTAX).get(name) is not cls for name, cls in zip(_RESULT_NAMES, _RESULT_CLASSES, strict=True))
    )
    if not drift:
        for index, cls in enumerate(_RESULT_CLASSES):
            result_namespace = vars(cls)
            if (
                frozenset(result_namespace) != _RESULT_KEYS[index]
                or tuple(result_namespace.get("__slots__", ())) != _RESULT_SLOTS[index]
                or result_namespace.get("__init__") is not _RESULT_INITS[index]
                or _RESULT_INITS[index].__code__ is not _RESULT_INIT_CODES[index]
                or result_namespace.get("__post_init__") is not _RESULT_POSTS[index]
                or _RESULT_POSTS[index].__code__ is not _RESULT_POST_CODES[index]
                or result_namespace.get("__final__") is not _RESULT_FINALS[index]
                or _RESULT_FINALS[index] is not True
                or any(result_namespace.get(name) is not descriptor or type(descriptor) is not MemberDescriptorType for name, descriptor in zip(_RESULT_SLOTS[index], _RESULT_DESCRIPTORS[index], strict=True))
            ):
                drift = True
                break
    if drift:
        _integrity_error("keb1-builder-integrity")
    _LOGGER.debug("validate_keb1_builder_integrity_v1 exit")


_VALIDATE_BUILDER_FROZEN = validate_keb1_builder_integrity_v1
_VALIDATE_BUILDER_CODE = _VALIDATE_BUILDER_FROZEN.__code__


def _guard_builder_v1() -> None:
    _LOGGER.debug("_guard_builder_v1 entry")
    if globals().get("validate_keb1_builder_integrity_v1") is not _VALIDATE_BUILDER_FROZEN or _VALIDATE_BUILDER_FROZEN.__code__ is not _VALIDATE_BUILDER_CODE:
        _INTEGRITY_FROZEN("keb1-builder-validator-integrity")
    _VALIDATE_BUILDER_FROZEN()
    _LOGGER.debug("_guard_builder_v1 exit")


_GUARD_BUILDER_FROZEN = _guard_builder_v1
_GUARD_BUILDER_CODE = _GUARD_BUILDER_FROZEN.__code__


def _build_prevalidated_binding_v1(
    term: _kpt_syntax.KernelProofTermV1,
    wire: bytes,
    term_alias: object,
    binding_alias: object,
) -> _syntax.ExpectedBindingSyntaxV1:
    """Allocate one prevalidated binding without executing class hooks."""
    _LOGGER.debug("_build_prevalidated_binding_v1 entry")
    _GUARD_BUILDER_FROZEN()
    if term_alias is not _KPT_CLASS or binding_alias is not _BINDING_CLASS:
        _integrity_error("keb1-builder-alias-integrity")
    if type(term) is not _KPT_CLASS or type(wire) is not bytes:
        _integrity_error("keb1-builder-host-shape")
    result = _OBJECT_NEW(_BINDING_CLASS)
    cast(_SlotSetter, _TERM_SLOT).__set__(result, term)
    cast(_SlotSetter, _WIRE_SLOT).__set__(result, wire)
    _LOGGER.debug("_build_prevalidated_binding_v1 exit bytes=%d", len(wire))
    return result


def expected_binding_v1(term: _kpt_syntax.KernelProofTermV1) -> _syntax.ExpectedBindingSyntaxV1:
    """Build a fresh exact KEB1 value from only an exact KPT1 term."""
    _LOGGER.debug("expected_binding_v1 entry")
    _GUARD_BUILDER_FROZEN()
    if type(term) is not _KPT_CLASS:
        _integrity_error("keb1-term-host-shape")
    try:
        wire = _KPT_CODEC(term)
    except Exception as exc:
        _LOGGER.error("expected_binding_v1 error dependency=%s", type(exc).__name__)
        _integrity_error("keb1-kpt-codec-refusal")
    if type(wire) is not bytes:
        _integrity_error("keb1-kpt-codec-result")
    result = _build_prevalidated_binding_v1(term, wire, _KPT_CLASS, _BINDING_CLASS)
    _LOGGER.debug("expected_binding_v1 exit bytes=%d", len(wire))
    return result


_T = TypeVar("_T")


def _allocate_result_v1(cls: type[_T], index: int, values: tuple[object, ...]) -> _T:
    _LOGGER.debug("_allocate_result_v1 entry index=%d", index)
    _GUARD_BUILDER_FROZEN()
    if type(index) is not int or not 0 <= index < len(_RESULT_CLASSES) or cls is not _RESULT_CLASSES[index] or type(values) is not tuple or len(values) != len(_RESULT_SLOTS[index]):
        _integrity_error("keb1-result-allocation-host-shape")
    result = _OBJECT_NEW_FROZEN(cls)
    for descriptor, value in zip(_RESULT_DESCRIPTORS[index], values, strict=True):
        descriptor.__set__(result, value)
    _LOGGER.debug("_allocate_result_v1 exit index=%d", index)
    return result


_ALLOCATE_RESULT_FROZEN = _allocate_result_v1
_ALLOCATE_RESULT_CODE = _ALLOCATE_RESULT_FROZEN.__code__


def _guard_result_allocator_v1() -> None:
    _LOGGER.debug("_guard_result_allocator_v1 entry")
    if globals().get("_allocate_result_v1") is not _ALLOCATE_RESULT_FROZEN or _ALLOCATE_RESULT_FROZEN.__code__ is not _ALLOCATE_RESULT_CODE:
        _INTEGRITY_FROZEN("keb1-result-allocator-integrity")
    _LOGGER.debug("_guard_result_allocator_v1 exit")


_GUARD_RESULT_FROZEN = _guard_result_allocator_v1
_GUARD_RESULT_CODE = _GUARD_RESULT_FROZEN.__code__


def _build_decode_error_result_v1(code: object, offset: int) -> _syntax.KEB1DecodeErrorResultV1:
    _LOGGER.debug("_build_decode_error_result_v1 entry")
    if globals().get("_guard_result_allocator_v1") is not _GUARD_RESULT_FROZEN or _GUARD_RESULT_FROZEN.__code__ is not _GUARD_RESULT_CODE:
        _INTEGRITY_FROZEN("keb1-result-allocator-guard-integrity")
    _GUARD_RESULT_FROZEN()
    if type(code) is not _DECODE_ENUM or type(offset) is not int or not 0 <= offset < _U64_LIMIT:
        _integrity_error("keb1-decode-result-host-shape")
    error = _ALLOCATE_RESULT_FROZEN(_RESULT_CLASSES[0], 0, (code, offset))
    result = _ALLOCATE_RESULT_FROZEN(_RESULT_CLASSES[3], 3, (error,))
    _LOGGER.debug("_build_decode_error_result_v1 exit")
    return result


def _build_resource_parse_result_v1(kind: object, allowed: int, required: int, offset: int) -> _syntax.KEB1ResourceParseResultV1:
    _LOGGER.debug("_build_resource_parse_result_v1 entry")
    if globals().get("_guard_result_allocator_v1") is not _GUARD_RESULT_FROZEN or _GUARD_RESULT_FROZEN.__code__ is not _GUARD_RESULT_CODE:
        _INTEGRITY_FROZEN("keb1-result-allocator-guard-integrity")
    _GUARD_RESULT_FROZEN()
    if type(kind) is not _RESOURCE_ENUM or any(type(v) is not int or not 0 <= v < _U64_LIMIT for v in (allowed, required, offset)) or required <= allowed:
        _integrity_error("keb1-resource-result-host-shape")
    resource = _ALLOCATE_RESULT_FROZEN(_RESULT_CLASSES[1], 1, (kind, allowed, required, offset))
    result = _ALLOCATE_RESULT_FROZEN(_RESULT_CLASSES[4], 4, (resource,))
    _LOGGER.debug("_build_resource_parse_result_v1 exit")
    return result


def _build_decoded_result_v1(value: _syntax.ExpectedBindingSyntaxV1, end: int) -> _syntax.KEB1DecodedResultV1:
    _LOGGER.debug("_build_decoded_result_v1 entry")
    if globals().get("_guard_result_allocator_v1") is not _GUARD_RESULT_FROZEN or _GUARD_RESULT_FROZEN.__code__ is not _GUARD_RESULT_CODE:
        _INTEGRITY_FROZEN("keb1-result-allocator-guard-integrity")
    _GUARD_RESULT_FROZEN()
    if type(value) is not _BINDING_CLASS or type(end) is not int or not 0 <= end < _U64_LIMIT:
        _integrity_error("keb1-decoded-result-host-shape")
    result = _ALLOCATE_RESULT_FROZEN(_RESULT_CLASSES[2], 2, (value, end))
    _LOGGER.debug("_build_decoded_result_v1 exit")
    return result


ExpectedBindingSyntaxV1 = _BINDING_CLASS
