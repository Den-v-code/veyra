"""Hook-free KIE1 expected-byte binding and normal preparation sum."""

from __future__ import annotations

import logging
from types import MemberDescriptorType
from typing import Protocol, TypeVar, cast

from . import omegaa_kci1_types as _kci_types
from . import omegaa_keb1_common as _keb_common
from . import omegaa_keb1_types as _keb_types
from . import omegaa_kie1_offsets as _offsets
from . import omegaa_kie1_types as _types
from . import omegaa_kpt1_types as _kpt_types
from .omegaa_kie1_common import (
    KIEPrepareCodeV1,
    _checked_add_u64,
    _integrity_error,
    validate_kie1_common_integrity_v1,
)

logger = logging.getLogger(__name__)
_LOGGER = logger
_INPUT_CLASS = _kci_types.CheckerInputSyntaxV1
_BINDING_CLASS = _keb_types.ExpectedBindingSyntaxV1
_KPT_CLASS = _kpt_types.KernelProofTermV1
_BOUND_CLASS = _types.BoundExpectedInputV1
_ERROR_CLASS = _types.KIEPrepareErrorV1
_BOUND_RESULT_CLASS = _types._KIEBoundResultV1
_ERROR_RESULT_CLASS = _types._KIEInitErrorResultV1
_PREPARE_CODE_CLASS = KIEPrepareCodeV1
_INPUT_SLOTS = tuple(vars(_INPUT_CLASS)["__slots__"])
_INPUT_DESCRIPTORS = tuple(vars(_INPUT_CLASS)[name] for name in _INPUT_SLOTS)
_BINDING_SLOTS = tuple(vars(_BINDING_CLASS)["__slots__"])
_BINDING_DESCRIPTORS = tuple(vars(_BINDING_CLASS)[name] for name in _BINDING_SLOTS)
_OUTPUT_CLASSES = (_BOUND_CLASS, _ERROR_CLASS, _BOUND_RESULT_CLASS, _ERROR_RESULT_CLASS)
_OUTPUT_SLOTS = tuple(tuple(vars(cls)["__slots__"]) for cls in _OUTPUT_CLASSES)
_OUTPUT_DESCRIPTORS = tuple(
    tuple(vars(cls)[name] for name in slots)
    for cls, slots in zip(_OUTPUT_CLASSES, _OUTPUT_SLOTS, strict=True)
)
_ALL_CLASSES = (_INPUT_CLASS, _BINDING_CLASS, *_OUTPUT_CLASSES)
_CLASS_KEYS = tuple(frozenset(vars(cls)) for cls in _ALL_CLASSES)
_CLASS_INITS = tuple(vars(cls)["__init__"] for cls in _ALL_CLASSES)
_CLASS_INIT_CODES = tuple(function.__code__ for function in _CLASS_INITS)
_CLASS_POSTS = tuple(vars(cls)["__post_init__"] for cls in _ALL_CLASSES)
_CLASS_POST_CODES = tuple(function.__code__ for function in _CLASS_POSTS)
_CLASS_FINALS = tuple(vars(cls).get("__final__") for cls in _ALL_CLASSES)
_INPUT_SLOTS_FROZEN, _INPUT_DESCRIPTORS_FROZEN = _INPUT_SLOTS, _INPUT_DESCRIPTORS
_BINDING_SLOTS_FROZEN = _BINDING_SLOTS
_BINDING_DESCRIPTORS_FROZEN = _BINDING_DESCRIPTORS
_OUTPUT_CLASSES_FROZEN, _OUTPUT_SLOTS_FROZEN = _OUTPUT_CLASSES, _OUTPUT_SLOTS
_OUTPUT_DESCRIPTORS_FROZEN = _OUTPUT_DESCRIPTORS
_ALL_CLASSES_FROZEN, _CLASS_KEYS_FROZEN = _ALL_CLASSES, _CLASS_KEYS
_CLASS_INITS_FROZEN, _CLASS_INIT_CODES_FROZEN = _CLASS_INITS, _CLASS_INIT_CODES
_CLASS_POSTS_FROZEN, _CLASS_POST_CODES_FROZEN = _CLASS_POSTS, _CLASS_POST_CODES
_CLASS_FINALS_FROZEN = _CLASS_FINALS
_OBJECT_NEW = object.__new__
_BYTES_CLASS = bytes
_BYTES_EQUAL = bytes.__eq__
_FIRST_DIFF = _offsets.FirstUnsignedDifferenceV1
_FIRST_DIFF_CODE = _FIRST_DIFF.__code__
_KEB_FIRST_DIFF = _keb_common.FirstUnsignedDifferenceV1
_KEB_FIRST_DIFF_CODE = _KEB_FIRST_DIFF.__code__
_VALIDATE_OFFSETS = _offsets.validate_kie1_offsets_integrity_v1
_VALIDATE_OFFSETS_CODE = _VALIDATE_OFFSETS.__code__
_VALIDATE_COMMON = validate_kie1_common_integrity_v1
_VALIDATE_COMMON_CODE = _VALIDATE_COMMON.__code__
_ADD_U64 = _checked_add_u64
_ADD_U64_CODE = _ADD_U64.__code__
_INTEGRITY_ERROR = _integrity_error
_INTEGRITY_ERROR_CODE = _INTEGRITY_ERROR.__code__


class _SlotSetter(Protocol):
    def __set__(self, instance: object, value: object) -> None: ...


def validate_kie1_binding_integrity_v1() -> None:
    """Refuse dependency, class, slot, hook, allocator, equality, or helper drift."""
    _LOGGER.debug("validate_kie1_binding_integrity_v1 entry")
    drift = (
        globals().get("logger") is not _LOGGER
        or vars(_kci_types).get("CheckerInputSyntaxV1") is not _INPUT_CLASS
        or vars(_keb_types).get("ExpectedBindingSyntaxV1") is not _BINDING_CLASS
        or vars(_kpt_types).get("KernelProofTermV1") is not _KPT_CLASS
        or vars(_types).get("BoundExpectedInputV1") is not _BOUND_CLASS
        or vars(_types).get("KIEPrepareErrorV1") is not _ERROR_CLASS
        or vars(_types).get("_KIEBoundResultV1") is not _BOUND_RESULT_CLASS
        or vars(_types).get("_KIEInitErrorResultV1") is not _ERROR_RESULT_CLASS
        or globals().get("KIEPrepareCodeV1") is not _PREPARE_CODE_CLASS
        or object.__new__ is not _OBJECT_NEW
        or globals().get("_BYTES_CLASS") is not bytes
        or bytes.__eq__ is not _BYTES_EQUAL
        or vars(_offsets).get("FirstUnsignedDifferenceV1") is not _FIRST_DIFF
        or _FIRST_DIFF.__code__ is not _FIRST_DIFF_CODE
        or vars(_keb_common).get("FirstUnsignedDifferenceV1") is not _KEB_FIRST_DIFF
        or _KEB_FIRST_DIFF.__code__ is not _KEB_FIRST_DIFF_CODE
        or vars(_offsets).get("validate_kie1_offsets_integrity_v1") is not _VALIDATE_OFFSETS
        or _VALIDATE_OFFSETS.__code__ is not _VALIDATE_OFFSETS_CODE
        or globals().get("validate_kie1_common_integrity_v1") is not _VALIDATE_COMMON
        or _VALIDATE_COMMON.__code__ is not _VALIDATE_COMMON_CODE
        or globals().get("_checked_add_u64") is not _ADD_U64
        or _ADD_U64.__code__ is not _ADD_U64_CODE
        or globals().get("_integrity_error") is not _INTEGRITY_ERROR
        or _INTEGRITY_ERROR.__code__ is not _INTEGRITY_ERROR_CODE
        or globals().get("_INPUT_SLOTS") is not _INPUT_SLOTS_FROZEN
        or globals().get("_INPUT_DESCRIPTORS") is not _INPUT_DESCRIPTORS_FROZEN
        or globals().get("_BINDING_SLOTS") is not _BINDING_SLOTS_FROZEN
        or globals().get("_BINDING_DESCRIPTORS") is not _BINDING_DESCRIPTORS_FROZEN
        or globals().get("_OUTPUT_CLASSES") is not _OUTPUT_CLASSES_FROZEN
        or globals().get("_OUTPUT_SLOTS") is not _OUTPUT_SLOTS_FROZEN
        or globals().get("_OUTPUT_DESCRIPTORS") is not _OUTPUT_DESCRIPTORS_FROZEN
        or globals().get("_ALL_CLASSES") is not _ALL_CLASSES_FROZEN
        or globals().get("_CLASS_KEYS") is not _CLASS_KEYS_FROZEN
        or globals().get("_CLASS_INITS") is not _CLASS_INITS_FROZEN
        or globals().get("_CLASS_INIT_CODES") is not _CLASS_INIT_CODES_FROZEN
        or globals().get("_CLASS_POSTS") is not _CLASS_POSTS_FROZEN
        or globals().get("_CLASS_POST_CODES") is not _CLASS_POST_CODES_FROZEN
        or globals().get("_CLASS_FINALS") is not _CLASS_FINALS_FROZEN
        or _INPUT_SLOTS_FROZEN != ("expected_bytes", "term_bytes")
        or len(_INPUT_DESCRIPTORS_FROZEN) != 2
        or _BINDING_SLOTS_FROZEN != ("expected_term", "expected_wire")
        or len(_BINDING_DESCRIPTORS_FROZEN) != 2
        or _OUTPUT_CLASSES_FROZEN
        != (_BOUND_CLASS, _ERROR_CLASS, _BOUND_RESULT_CLASS, _ERROR_RESULT_CLASS)
        or _OUTPUT_SLOTS_FROZEN
        != (("input", "binding"), ("code", "absolute_kci_offset"), ("bound",), ("error",))
        or tuple(len(row) for row in _OUTPUT_DESCRIPTORS_FROZEN) != (2, 2, 1, 1)
        or _ALL_CLASSES_FROZEN != (_INPUT_CLASS, _BINDING_CLASS, *_OUTPUT_CLASSES_FROZEN)
        or any(
            len(table) != 6
            for table in (
                _CLASS_KEYS_FROZEN,
                _CLASS_INITS_FROZEN,
                _CLASS_INIT_CODES_FROZEN,
                _CLASS_POSTS_FROZEN,
                _CLASS_POST_CODES_FROZEN,
                _CLASS_FINALS_FROZEN,
            )
        )
    )
    if not drift:
        for index, cls in enumerate(_ALL_CLASSES_FROZEN):
            namespace = vars(cls)
            expected_slots = (
                _INPUT_SLOTS_FROZEN
                if index == 0
                else _BINDING_SLOTS_FROZEN
                if index == 1
                else _OUTPUT_SLOTS_FROZEN[index - 2]
            )
            expected_descriptors = (
                _INPUT_DESCRIPTORS_FROZEN
                if index == 0
                else _BINDING_DESCRIPTORS_FROZEN
                if index == 1
                else _OUTPUT_DESCRIPTORS_FROZEN[index - 2]
            )
            if (
                frozenset(namespace) != _CLASS_KEYS_FROZEN[index]
                or tuple(namespace.get("__slots__", ())) != expected_slots
                or namespace.get("__init__") is not _CLASS_INITS_FROZEN[index]
                or _CLASS_INITS_FROZEN[index].__code__ is not _CLASS_INIT_CODES_FROZEN[index]
                or namespace.get("__post_init__") is not _CLASS_POSTS_FROZEN[index]
                or _CLASS_POSTS_FROZEN[index].__code__ is not _CLASS_POST_CODES_FROZEN[index]
                or namespace.get("__final__") is not _CLASS_FINALS_FROZEN[index]
                or _CLASS_FINALS_FROZEN[index] is not True
                or any(
                    namespace.get(name) is not descriptor or type(descriptor) is not MemberDescriptorType
                    for name, descriptor in zip(expected_slots, expected_descriptors, strict=True)
                )
            ):
                drift = True
                break
    if drift:
        _LOGGER.error("validate_kie1_binding_integrity_v1 error drift")
        _INTEGRITY_ERROR("kie1-binding-integrity")
    _VALIDATE_COMMON()
    _VALIDATE_OFFSETS()
    _LOGGER.debug("validate_kie1_binding_integrity_v1 exit")


_VALIDATE_BINDING = validate_kie1_binding_integrity_v1
_VALIDATE_BINDING_CODE = _VALIDATE_BINDING.__code__
_T = TypeVar("_T")


def _allocate_v1(cls: type[_T], values: tuple[object, ...]) -> _T:
    """Allocate one captured output class without constructor or post-init hooks."""
    _LOGGER.debug("_allocate_v1 entry")
    _VALIDATE_BINDING()
    if type(values) is not tuple or cls not in _OUTPUT_CLASSES_FROZEN:
        _LOGGER.error("_allocate_v1 error class-shape")
        _INTEGRITY_ERROR("kie1-allocation-host-shape")
    index = _OUTPUT_CLASSES_FROZEN.index(cls)
    if len(values) != len(_OUTPUT_DESCRIPTORS_FROZEN[index]):
        _LOGGER.error("_allocate_v1 error arity")
        _INTEGRITY_ERROR("kie1-allocation-host-shape")
    result = _OBJECT_NEW(cls)
    for descriptor, value in zip(_OUTPUT_DESCRIPTORS_FROZEN[index], values, strict=True):
        cast(_SlotSetter, descriptor).__set__(result, value)
    _LOGGER.debug("_allocate_v1 exit index=%d", index)
    return result


_ALLOCATE = _allocate_v1
_ALLOCATE_CODE = _ALLOCATE.__code__


def _read_inputs_v1(
    input_value: _kci_types.CheckerInputSyntaxV1,
    binding: _keb_types.ExpectedBindingSyntaxV1,
) -> tuple[bytes, bytes]:
    """Validate exact KCI/KEB shapes before captured C-slot reads."""
    _LOGGER.debug("_read_inputs_v1 entry")
    _VALIDATE_BINDING()
    if type(input_value) is not _INPUT_CLASS or type(binding) is not _BINDING_CLASS:
        _LOGGER.error("_read_inputs_v1 error outer-shape")
        _INTEGRITY_ERROR("kie1-input-binding-host-shape")
    expected = _INPUT_DESCRIPTORS_FROZEN[0].__get__(input_value, _INPUT_CLASS)
    term_bytes = _INPUT_DESCRIPTORS_FROZEN[1].__get__(input_value, _INPUT_CLASS)
    expected_term = _BINDING_DESCRIPTORS_FROZEN[0].__get__(binding, _BINDING_CLASS)
    expected_wire = _BINDING_DESCRIPTORS_FROZEN[1].__get__(binding, _BINDING_CLASS)
    if (
        type(expected) is not _BYTES_CLASS
        or type(term_bytes) is not _BYTES_CLASS
        or type(expected_term) is not _KPT_CLASS
        or type(expected_wire) is not _BYTES_CLASS
    ):
        _LOGGER.error("_read_inputs_v1 error field-shape")
        _INTEGRITY_ERROR("kie1-input-binding-field-shape")
    _LOGGER.debug("_read_inputs_v1 exit")
    return expected, expected_wire


_READ_INPUTS = _read_inputs_v1
_READ_INPUTS_CODE = _READ_INPUTS.__code__


def BindExpectedInputV1(
    input_value: _kci_types.CheckerInputSyntaxV1,
    binding: _keb_types.ExpectedBindingSyntaxV1,
) -> _types.KIEPrepareResultV1:
    """Prepare one inert bound pair or one normal expected-wire mismatch."""
    _LOGGER.debug("BindExpectedInputV1 entry")
    if (
        globals().get("validate_kie1_binding_integrity_v1") is not _VALIDATE_BINDING
        or _VALIDATE_BINDING.__code__ is not _VALIDATE_BINDING_CODE
        or globals().get("_allocate_v1") is not _ALLOCATE
        or _ALLOCATE.__code__ is not _ALLOCATE_CODE
        or globals().get("_read_inputs_v1") is not _READ_INPUTS
        or _READ_INPUTS.__code__ is not _READ_INPUTS_CODE
    ):
        _INTEGRITY_ERROR("kie1-bind-helper-integrity")
    expected, wire = _READ_INPUTS(input_value, binding)
    equality = _BYTES_EQUAL(expected, wire)
    if type(equality) is not bool:
        _LOGGER.error("BindExpectedInputV1 error equality-result")
        _INTEGRITY_ERROR("kie1-byte-equality-integrity")
    if equality:
        bound = _ALLOCATE(_BOUND_CLASS, (input_value, binding))
        result: _types.KIEPrepareResultV1 = _ALLOCATE(_BOUND_RESULT_CLASS, (bound,))
        _LOGGER.debug("BindExpectedInputV1 state=bound")
        _LOGGER.debug("BindExpectedInputV1 exit")
        return result
    difference = _FIRST_DIFF(expected, wire)
    dependency_difference = _KEB_FIRST_DIFF(expected, wire)
    if (
        type(difference) is not int
        or type(dependency_difference) is not int
        or difference != dependency_difference
    ):
        _LOGGER.error("BindExpectedInputV1 error difference-disagreement")
        _INTEGRITY_ERROR("kie1-first-difference-integrity")
    offset = _ADD_U64(14, difference, "expected-wire-mismatch")
    error = _ALLOCATE(
        _ERROR_CLASS,
        (_PREPARE_CODE_CLASS.EXPECTED_WIRE_MISMATCH, offset),
    )
    result = _ALLOCATE(_ERROR_RESULT_CLASS, (error,))
    _LOGGER.debug("BindExpectedInputV1 state=expected-wire-mismatch offset=%d", offset)
    _LOGGER.debug("BindExpectedInputV1 exit")
    return result


__all__ = ("BindExpectedInputV1", "validate_kie1_binding_integrity_v1")
