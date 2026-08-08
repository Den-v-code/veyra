"""Captured hook-free builders for fresh exact KCI1 DTOs."""

from __future__ import annotations

import logging
from types import MemberDescriptorType
from typing import TypeVar

from . import omegaa_kci1_common as _common
from . import omegaa_kci1_types as _syntax

logger = logging.getLogger(__name__)
_LOGGER = logger
_COMMON_MODULE = _common
_SYNTAX_MODULE = _syntax
_OBJECT_NEW = object.__new__
_OBJECT_NEW_FROZEN = object.__new__
_BYTES_CLASS = bytes
_BYTES_CLASS_FROZEN = bytes
_INPUT_CLASS = _syntax.CheckerInputSyntaxV1
_DECODE_ERROR_CLASS = _syntax.KCI1DecodeErrorV1
_RESOURCE_CLASS = _syntax.KCI1ResourceResultV1
_DECODED_CLASS = _syntax.KCI1DecodedResultV1
_DECODE_RESULT_CLASS = _syntax.KCI1DecodeErrorResultV1
_RESOURCE_RESULT_CLASS = _syntax.KCI1ResourceParseResultV1
_DECODE_ENUM = _common.KCI1DecodeCodeV1
_RESOURCE_ENUM = _common.KCI1ResourceKindV1
_VALIDATE_COMMON = _common.validate_kci1_common_integrity_v1
_VALIDATE_COMMON_CODE = _VALIDATE_COMMON.__code__
_INTEGRITY_ERROR = _common._integrity_error
_INTEGRITY_ERROR_CODE = _INTEGRITY_ERROR.__code__
_CHECKED_U64 = _common._checked_u64
_CHECKED_U64_CODE = _CHECKED_U64.__code__
_SYNTAX_LOGGER = _syntax.logger

_CLASSES = (
    _INPUT_CLASS,
    _DECODE_ERROR_CLASS,
    _RESOURCE_CLASS,
    _DECODED_CLASS,
    _DECODE_RESULT_CLASS,
    _RESOURCE_RESULT_CLASS,
)
_CLASS_NAMES = (
    "CheckerInputSyntaxV1",
    "KCI1DecodeErrorV1",
    "KCI1ResourceResultV1",
    "KCI1DecodedResultV1",
    "KCI1DecodeErrorResultV1",
    "KCI1ResourceParseResultV1",
)
_CLASS_KEYS = tuple(frozenset(vars(cls)) for cls in _CLASSES)
_CLASS_SLOTS = tuple(tuple(vars(cls)["__slots__"]) for cls in _CLASSES)
_CLASS_SLOT_DESCRIPTORS = tuple(
    tuple(vars(cls)[name] for name in slots)
    for cls, slots in zip(_CLASSES, _CLASS_SLOTS, strict=True)
)
_CLASS_INITS = tuple(vars(cls)["__init__"] for cls in _CLASSES)
_CLASS_INIT_CODES = tuple(init.__code__ for init in _CLASS_INITS)
_CLASS_POSTS = tuple(vars(cls)["__post_init__"] for cls in _CLASSES)
_CLASS_POST_CODES = tuple(post.__code__ for post in _CLASS_POSTS)
_CLASS_FINALS = tuple(vars(cls).get("__final__") for cls in _CLASSES)


def validate_kci1_builder_integrity_v1() -> None:
    """Refuse module, class, slot, hook, enum, logger, or allocator drift."""
    _LOGGER.debug("validate_kci1_builder_integrity_v1 entry")
    syntax = vars(_SYNTAX_MODULE)
    common = vars(_COMMON_MODULE)
    drift = (
        globals().get("logger") is not _LOGGER
        or globals().get("_syntax") is not _SYNTAX_MODULE
        or globals().get("_common") is not _COMMON_MODULE
        or globals().get("_OBJECT_NEW") is not _OBJECT_NEW_FROZEN
        or _OBJECT_NEW_FROZEN is not object.__new__
        or globals().get("_BYTES_CLASS") is not _BYTES_CLASS_FROZEN
        or _BYTES_CLASS_FROZEN is not bytes
        or syntax.get("logger") is not _SYNTAX_LOGGER
        or common.get("KCI1DecodeCodeV1") is not _DECODE_ENUM
        or common.get("KCI1ResourceKindV1") is not _RESOURCE_ENUM
        or common.get("validate_kci1_common_integrity_v1") is not _VALIDATE_COMMON
        or _VALIDATE_COMMON.__code__ is not _VALIDATE_COMMON_CODE
        or common.get("_integrity_error") is not _INTEGRITY_ERROR
        or _INTEGRITY_ERROR.__code__ is not _INTEGRITY_ERROR_CODE
        or common.get("_checked_u64") is not _CHECKED_U64
        or _CHECKED_U64.__code__ is not _CHECKED_U64_CODE
        or globals().get("build_checker_input_syntax_v1") is not _BUILD_PUBLIC
        or _BUILD_PUBLIC.__code__ is not _BUILD_PUBLIC_CODE
        or any(syntax.get(name) is not cls for name, cls in zip(_CLASS_NAMES, _CLASSES, strict=True))
    )
    if not drift:
        for index, cls in enumerate(_CLASSES):
            namespace = vars(cls)
            slots = _CLASS_SLOTS[index]
            descriptors = _CLASS_SLOT_DESCRIPTORS[index]
            if (
                frozenset(namespace) != _CLASS_KEYS[index]
                or tuple(namespace.get("__slots__", ())) != slots
                or namespace.get("__init__") is not _CLASS_INITS[index]
                or _CLASS_INITS[index].__code__ is not _CLASS_INIT_CODES[index]
                or namespace.get("__post_init__") is not _CLASS_POSTS[index]
                or _CLASS_POSTS[index].__code__ is not _CLASS_POST_CODES[index]
                or namespace.get("__final__") is not _CLASS_FINALS[index]
                or _CLASS_FINALS[index] is not True
                or any(
                    namespace.get(name) is not descriptor
                    or type(descriptor) is not MemberDescriptorType
                    for name, descriptor in zip(slots, descriptors, strict=True)
                )
            ):
                drift = True
                break
    if drift:
        _LOGGER.error("validate_kci1_builder_integrity_v1 error drift")
        _INTEGRITY_ERROR("kci1-builder-integrity")
    _VALIDATE_COMMON()
    _LOGGER.debug("validate_kci1_builder_integrity_v1 exit")


_VALIDATE_LOCAL = validate_kci1_builder_integrity_v1
_VALIDATE_LOCAL_CODE = _VALIDATE_LOCAL.__code__
_T = TypeVar("_T")


def _allocate_v1(cls: type[_T], class_index: int, values: tuple[object, ...]) -> _T:
    _LOGGER.debug("_allocate_v1 entry class_index=%d", class_index)
    if (
        globals().get("_OBJECT_NEW") is not _OBJECT_NEW_FROZEN
        or _OBJECT_NEW_FROZEN is not object.__new__
        or globals().get("_BYTES_CLASS") is not _BYTES_CLASS_FROZEN
        or _BYTES_CLASS_FROZEN is not bytes
        or globals().get("_allocate_v1") is not _ALLOCATE
        or _ALLOCATE.__code__ is not _ALLOCATE_CODE
        or type(class_index) is not int
        or not 0 <= class_index < len(_CLASSES)
        or cls is not _CLASSES[class_index]
        or type(values) is not tuple
        or len(values) != len(_CLASS_SLOTS[class_index])
    ):
        _LOGGER.error("_allocate_v1 error host-shape")
        _INTEGRITY_ERROR("kci1-allocation-host-shape")
    _LOGGER.debug("_allocate_v1 external_call=object.__new__")
    result = _OBJECT_NEW_FROZEN(cls)
    for descriptor, value in zip(_CLASS_SLOT_DESCRIPTORS[class_index], values, strict=True):
        _LOGGER.debug("_allocate_v1 external_call=member_descriptor.__set__")
        descriptor.__set__(result, value)
    _LOGGER.debug("_allocate_v1 exit class_index=%d", class_index)
    return result


_ALLOCATE = _allocate_v1
_ALLOCATE_CODE = _ALLOCATE.__code__


def _guard_builder_v1() -> None:
    _LOGGER.debug("_guard_builder_v1 entry")
    if (
        globals().get("validate_kci1_builder_integrity_v1") is not _VALIDATE_LOCAL
        or _VALIDATE_LOCAL.__code__ is not _VALIDATE_LOCAL_CODE
        or globals().get("_allocate_v1") is not _ALLOCATE
        or _ALLOCATE.__code__ is not _ALLOCATE_CODE
    ):
        _LOGGER.error("_guard_builder_v1 error helper-drift")
        _INTEGRITY_ERROR("kci1-builder-helper-integrity")
    _VALIDATE_LOCAL()
    _LOGGER.debug("_guard_builder_v1 exit")


_GUARD = _guard_builder_v1
_GUARD_CODE = _GUARD.__code__


def build_checker_input_syntax_v1(
    expected_bytes: bytes,
    term_bytes: bytes,
) -> _syntax.CheckerInputSyntaxV1:
    """Create one fresh exact two-slot syntax DTO without Python hooks."""
    _LOGGER.debug("build_checker_input_syntax_v1 entry")
    if (
        globals().get("build_checker_input_syntax_v1") is not _BUILD_PUBLIC
        or _BUILD_PUBLIC.__code__ is not _BUILD_PUBLIC_CODE
        or globals().get("_guard_builder_v1") is not _GUARD
        or _GUARD.__code__ is not _GUARD_CODE
    ):
        _LOGGER.error("build_checker_input_syntax_v1 error guard-drift")
        _INTEGRITY_ERROR("kci1-builder-guard-integrity")
    _GUARD()
    if (
        type(expected_bytes) is not _BYTES_CLASS_FROZEN
        or type(term_bytes) is not _BYTES_CLASS_FROZEN
    ):
        _LOGGER.error("build_checker_input_syntax_v1 error payload-type")
        _INTEGRITY_ERROR("kci1-input-payload-type")
    result = _ALLOCATE(_INPUT_CLASS, 0, (expected_bytes, term_bytes))
    _LOGGER.debug("build_checker_input_syntax_v1 exit")
    return result


_BUILD_PUBLIC = build_checker_input_syntax_v1
_BUILD_PUBLIC_CODE = _BUILD_PUBLIC.__code__


def _build_decode_error_v1(
    code: _common.KCI1DecodeCodeV1,
    absolute_offset: int,
) -> _syntax.KCI1DecodeErrorV1:
    _LOGGER.debug("_build_decode_error_v1 entry")
    if (
        globals().get("_guard_builder_v1") is not _GUARD
        or _GUARD.__code__ is not _GUARD_CODE
    ):
        _LOGGER.error("_build_decode_error_v1 error guard-drift")
        _INTEGRITY_ERROR("kci1-builder-guard-integrity")
    _GUARD()
    if type(code) is not _DECODE_ENUM:
        _LOGGER.error("_build_decode_error_v1 error code-type")
        _INTEGRITY_ERROR("kci1-decode-code-type")
    offset = _CHECKED_U64(absolute_offset, "decode-offset")
    result = _ALLOCATE(_DECODE_ERROR_CLASS, 1, (code, offset))
    _LOGGER.debug("_build_decode_error_v1 exit")
    return result


def _build_resource_result_v1(
    kind: _common.KCI1ResourceKindV1,
    allowed: int,
    required: int,
    absolute_offset: int,
) -> _syntax.KCI1ResourceResultV1:
    _LOGGER.debug("_build_resource_result_v1 entry")
    if (
        globals().get("_guard_builder_v1") is not _GUARD
        or _GUARD.__code__ is not _GUARD_CODE
    ):
        _LOGGER.error("_build_resource_result_v1 error guard-drift")
        _INTEGRITY_ERROR("kci1-builder-guard-integrity")
    _GUARD()
    if type(kind) is not _RESOURCE_ENUM:
        _LOGGER.error("_build_resource_result_v1 error kind-type")
        _INTEGRITY_ERROR("kci1-resource-kind-type")
    checked = tuple(
        _CHECKED_U64(value, label)
        for value, label in (
            (allowed, "resource-allowed"),
            (required, "resource-required"),
            (absolute_offset, "resource-offset"),
        )
    )
    if checked[1] <= checked[0]:
        _LOGGER.error("_build_resource_result_v1 error nonexcess")
        _INTEGRITY_ERROR("kci1-resource-nonexcess")
    result = _ALLOCATE(_RESOURCE_CLASS, 2, (kind, *checked))
    _LOGGER.debug("_build_resource_result_v1 exit")
    return result


def _build_decoded_result_v1(
    value: _syntax.CheckerInputSyntaxV1,
    end: int,
) -> _syntax.KCI1DecodedResultV1:
    _LOGGER.debug("_build_decoded_result_v1 entry")
    if (
        globals().get("_guard_builder_v1") is not _GUARD
        or _GUARD.__code__ is not _GUARD_CODE
    ):
        _LOGGER.error("_build_decoded_result_v1 error guard-drift")
        _INTEGRITY_ERROR("kci1-builder-guard-integrity")
    _GUARD()
    if type(value) is not _INPUT_CLASS:
        _LOGGER.error("_build_decoded_result_v1 error value-type")
        _INTEGRITY_ERROR("kci1-decoded-value-type")
    result = _ALLOCATE(_DECODED_CLASS, 3, (value, _CHECKED_U64(end, "decoded-end")))
    _LOGGER.debug("_build_decoded_result_v1 exit")
    return result


def _build_decode_error_result_v1(
    error: _syntax.KCI1DecodeErrorV1,
) -> _syntax.KCI1DecodeErrorResultV1:
    _LOGGER.debug("_build_decode_error_result_v1 entry")
    if (
        globals().get("_guard_builder_v1") is not _GUARD
        or _GUARD.__code__ is not _GUARD_CODE
    ):
        _LOGGER.error("_build_decode_error_result_v1 error guard-drift")
        _INTEGRITY_ERROR("kci1-builder-guard-integrity")
    _GUARD()
    if type(error) is not _DECODE_ERROR_CLASS:
        _LOGGER.error("_build_decode_error_result_v1 error value-type")
        _INTEGRITY_ERROR("kci1-decode-result-value-type")
    result = _ALLOCATE(_DECODE_RESULT_CLASS, 4, (error,))
    _LOGGER.debug("_build_decode_error_result_v1 exit")
    return result


def _build_resource_parse_result_v1(
    resource: _syntax.KCI1ResourceResultV1,
) -> _syntax.KCI1ResourceParseResultV1:
    _LOGGER.debug("_build_resource_parse_result_v1 entry")
    if (
        globals().get("_guard_builder_v1") is not _GUARD
        or _GUARD.__code__ is not _GUARD_CODE
    ):
        _LOGGER.error("_build_resource_parse_result_v1 error guard-drift")
        _INTEGRITY_ERROR("kci1-builder-guard-integrity")
    _GUARD()
    if type(resource) is not _RESOURCE_CLASS:
        _LOGGER.error("_build_resource_parse_result_v1 error value-type")
        _INTEGRITY_ERROR("kci1-resource-result-value-type")
    result = _ALLOCATE(_RESOURCE_RESULT_CLASS, 5, (resource,))
    _LOGGER.debug("_build_resource_parse_result_v1 exit")
    return result
