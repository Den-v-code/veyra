"""Captured downstream inspection of the inert KIE1 preparation sum."""

from __future__ import annotations

import logging
from types import MemberDescriptorType
from typing import Protocol, cast

from . import omegaa_kci1_types as _kci_types
from . import omegaa_keb1_types as _keb_types
from . import omegaa_kie1_binding as _binding
from . import omegaa_kie1_common as _common
from . import omegaa_kie1_types as _types
from . import omegaa_kpt1_types as _kpt_types
from .omegaa_kie1_common import KIEPrepareCodeV1, U64_LIMIT, _integrity_error

logger = logging.getLogger(__name__)
_LOGGER = logger
_INPUT_CLASS = _kci_types.CheckerInputSyntaxV1
_BINDING_CLASS = _keb_types.ExpectedBindingSyntaxV1
_KPT_CLASS = _kpt_types.KernelProofTermV1
_BOUND_CLASS = _types.BoundExpectedInputV1
_ERROR_CLASS = _types.KIEPrepareErrorV1
_BOUND_RESULT_CLASS = _types._KIEBoundResultV1
_ERROR_RESULT_CLASS = _types._KIEInitErrorResultV1
_BOUND_VIEW_CLASS = _types._KIEBoundViewV1
_ERROR_VIEW_CLASS = _types._KIEErrorViewV1
_PREPARE_CODE_CLASS = KIEPrepareCodeV1
_COMMON_MODULE = _common
_U64_LIMIT_FROZEN = U64_LIMIT
_INPUT_DESCRIPTORS = (
    vars(_INPUT_CLASS)["expected_bytes"],
    vars(_INPUT_CLASS)["term_bytes"],
)
_BINDING_DESCRIPTORS = (
    vars(_BINDING_CLASS)["expected_term"],
    vars(_BINDING_CLASS)["expected_wire"],
)
_BOUND_DESCRIPTORS = (
    vars(_BOUND_CLASS)["input"],
    vars(_BOUND_CLASS)["binding"],
)
_ERROR_DESCRIPTORS = (
    vars(_ERROR_CLASS)["code"],
    vars(_ERROR_CLASS)["absolute_kci_offset"],
)
_RESULT_CLASSES = (_BOUND_RESULT_CLASS, _ERROR_RESULT_CLASS)
_RESULT_DESCRIPTORS = (
    (vars(_BOUND_RESULT_CLASS)["bound"],),
    (vars(_ERROR_RESULT_CLASS)["error"],),
)
_VIEW_CLASSES = (_BOUND_VIEW_CLASS, _ERROR_VIEW_CLASS)
_VIEW_DESCRIPTORS = (
    (vars(_BOUND_VIEW_CLASS)["input"], vars(_BOUND_VIEW_CLASS)["binding"]),
    (vars(_ERROR_VIEW_CLASS)["original_error"],),
)
_PROFILE_CLASSES = (
    _INPUT_CLASS,
    _BINDING_CLASS,
    _BOUND_CLASS,
    _ERROR_CLASS,
    *_RESULT_CLASSES,
    *_VIEW_CLASSES,
)
_PROFILE_KEYS = tuple(frozenset(vars(cls)) for cls in _PROFILE_CLASSES)
_PROFILE_INITS = tuple(vars(cls)["__init__"] for cls in _PROFILE_CLASSES)
_PROFILE_INIT_CODES = tuple(function.__code__ for function in _PROFILE_INITS)
_PROFILE_POSTS = tuple(vars(cls)["__post_init__"] for cls in _PROFILE_CLASSES)
_PROFILE_POST_CODES = tuple(function.__code__ for function in _PROFILE_POSTS)
_PROFILE_FINALS = tuple(vars(cls).get("__final__") for cls in _PROFILE_CLASSES)
_PROFILE_SLOTS = tuple(tuple(vars(cls)["__slots__"]) for cls in _PROFILE_CLASSES)
_PROFILE_DESCRIPTORS = (
    _INPUT_DESCRIPTORS,
    _BINDING_DESCRIPTORS,
    _BOUND_DESCRIPTORS,
    _ERROR_DESCRIPTORS,
    *_RESULT_DESCRIPTORS,
    *_VIEW_DESCRIPTORS,
)
_INPUT_DESCRIPTORS_FROZEN = _INPUT_DESCRIPTORS
_BINDING_DESCRIPTORS_FROZEN = _BINDING_DESCRIPTORS
_BOUND_DESCRIPTORS_FROZEN, _ERROR_DESCRIPTORS_FROZEN = _BOUND_DESCRIPTORS, _ERROR_DESCRIPTORS
_RESULT_CLASSES_FROZEN, _RESULT_DESCRIPTORS_FROZEN = _RESULT_CLASSES, _RESULT_DESCRIPTORS
_VIEW_CLASSES_FROZEN, _VIEW_DESCRIPTORS_FROZEN = _VIEW_CLASSES, _VIEW_DESCRIPTORS
_PROFILE_CLASSES_FROZEN, _PROFILE_KEYS_FROZEN = _PROFILE_CLASSES, _PROFILE_KEYS
_PROFILE_INITS_FROZEN, _PROFILE_INIT_CODES_FROZEN = _PROFILE_INITS, _PROFILE_INIT_CODES
_PROFILE_POSTS_FROZEN, _PROFILE_POST_CODES_FROZEN = _PROFILE_POSTS, _PROFILE_POST_CODES
_PROFILE_FINALS_FROZEN, _PROFILE_SLOTS_FROZEN = _PROFILE_FINALS, _PROFILE_SLOTS
_PROFILE_DESCRIPTORS_FROZEN = _PROFILE_DESCRIPTORS
_OBJECT_NEW = object.__new__
_BYTES_EQUAL = bytes.__eq__
_VALIDATE_BINDING = _binding.validate_kie1_binding_integrity_v1
_VALIDATE_BINDING_CODE = _VALIDATE_BINDING.__code__
_INTEGRITY_ERROR = _integrity_error
_INTEGRITY_ERROR_CODE = _INTEGRITY_ERROR.__code__


class _SlotSetter(Protocol):
    def __set__(self, instance: object, value: object) -> None: ...


def validate_kie1_prepare_integrity_v1() -> None:
    """Refuse result/view/dependency class, slot, hook, allocator, or alias drift."""
    _LOGGER.debug("validate_kie1_prepare_integrity_v1 entry")
    drift = (
        globals().get("logger") is not _LOGGER
        or vars(_kci_types).get("CheckerInputSyntaxV1") is not _INPUT_CLASS
        or vars(_keb_types).get("ExpectedBindingSyntaxV1") is not _BINDING_CLASS
        or vars(_kpt_types).get("KernelProofTermV1") is not _KPT_CLASS
        or vars(_types).get("BoundExpectedInputV1") is not _BOUND_CLASS
        or vars(_types).get("KIEPrepareErrorV1") is not _ERROR_CLASS
        or vars(_types).get("_KIEBoundResultV1") is not _BOUND_RESULT_CLASS
        or vars(_types).get("_KIEInitErrorResultV1") is not _ERROR_RESULT_CLASS
        or vars(_types).get("_KIEBoundViewV1") is not _BOUND_VIEW_CLASS
        or vars(_types).get("_KIEErrorViewV1") is not _ERROR_VIEW_CLASS
        or globals().get("KIEPrepareCodeV1") is not _PREPARE_CODE_CLASS
        or globals().get("U64_LIMIT") is not _U64_LIMIT_FROZEN
        or _U64_LIMIT_FROZEN != 18_446_744_073_709_551_616
        or vars(_COMMON_MODULE).get("U64_LIMIT") is not _U64_LIMIT_FROZEN
        or vars(_types).get("U64_LIMIT") is not _U64_LIMIT_FROZEN
        or vars(_types).get("_U64_LIMIT_FROZEN") is not _U64_LIMIT_FROZEN
        or object.__new__ is not _OBJECT_NEW
        or bytes.__eq__ is not _BYTES_EQUAL
        or vars(_binding).get("validate_kie1_binding_integrity_v1") is not _VALIDATE_BINDING
        or _VALIDATE_BINDING.__code__ is not _VALIDATE_BINDING_CODE
        or globals().get("_integrity_error") is not _INTEGRITY_ERROR
        or _INTEGRITY_ERROR.__code__ is not _INTEGRITY_ERROR_CODE
        or globals().get("_INPUT_DESCRIPTORS") is not _INPUT_DESCRIPTORS_FROZEN
        or globals().get("_BINDING_DESCRIPTORS") is not _BINDING_DESCRIPTORS_FROZEN
        or globals().get("_BOUND_DESCRIPTORS") is not _BOUND_DESCRIPTORS_FROZEN
        or globals().get("_ERROR_DESCRIPTORS") is not _ERROR_DESCRIPTORS_FROZEN
        or globals().get("_RESULT_CLASSES") is not _RESULT_CLASSES_FROZEN
        or globals().get("_RESULT_DESCRIPTORS") is not _RESULT_DESCRIPTORS_FROZEN
        or globals().get("_VIEW_CLASSES") is not _VIEW_CLASSES_FROZEN
        or globals().get("_VIEW_DESCRIPTORS") is not _VIEW_DESCRIPTORS_FROZEN
        or globals().get("_PROFILE_CLASSES") is not _PROFILE_CLASSES_FROZEN
        or globals().get("_PROFILE_KEYS") is not _PROFILE_KEYS_FROZEN
        or globals().get("_PROFILE_INITS") is not _PROFILE_INITS_FROZEN
        or globals().get("_PROFILE_INIT_CODES") is not _PROFILE_INIT_CODES_FROZEN
        or globals().get("_PROFILE_POSTS") is not _PROFILE_POSTS_FROZEN
        or globals().get("_PROFILE_POST_CODES") is not _PROFILE_POST_CODES_FROZEN
        or globals().get("_PROFILE_FINALS") is not _PROFILE_FINALS_FROZEN
        or globals().get("_PROFILE_SLOTS") is not _PROFILE_SLOTS_FROZEN
        or globals().get("_PROFILE_DESCRIPTORS") is not _PROFILE_DESCRIPTORS_FROZEN
        or len(_INPUT_DESCRIPTORS_FROZEN) != 2
        or len(_BINDING_DESCRIPTORS_FROZEN) != 2
        or len(_BOUND_DESCRIPTORS_FROZEN) != 2
        or len(_ERROR_DESCRIPTORS_FROZEN) != 2
        or _RESULT_CLASSES_FROZEN != (_BOUND_RESULT_CLASS, _ERROR_RESULT_CLASS)
        or tuple(len(row) for row in _RESULT_DESCRIPTORS_FROZEN) != (1, 1)
        or _VIEW_CLASSES_FROZEN != (_BOUND_VIEW_CLASS, _ERROR_VIEW_CLASS)
        or tuple(len(row) for row in _VIEW_DESCRIPTORS_FROZEN) != (2, 1)
        or _PROFILE_CLASSES_FROZEN
        != (
            _INPUT_CLASS,
            _BINDING_CLASS,
            _BOUND_CLASS,
            _ERROR_CLASS,
            _BOUND_RESULT_CLASS,
            _ERROR_RESULT_CLASS,
            _BOUND_VIEW_CLASS,
            _ERROR_VIEW_CLASS,
        )
        or _PROFILE_SLOTS_FROZEN
        != (
            ("expected_bytes", "term_bytes"),
            ("expected_term", "expected_wire"),
            ("input", "binding"),
            ("code", "absolute_kci_offset"),
            ("bound",),
            ("error",),
            ("input", "binding"),
            ("original_error",),
        )
        or tuple(len(row) for row in _PROFILE_DESCRIPTORS_FROZEN) != (2, 2, 2, 2, 1, 1, 2, 1)
        or any(
            len(table) != 8
            for table in (
                _PROFILE_KEYS_FROZEN,
                _PROFILE_INITS_FROZEN,
                _PROFILE_INIT_CODES_FROZEN,
                _PROFILE_POSTS_FROZEN,
                _PROFILE_POST_CODES_FROZEN,
                _PROFILE_FINALS_FROZEN,
            )
        )
    )
    if not drift:
        for index, cls in enumerate(_PROFILE_CLASSES_FROZEN):
            namespace = vars(cls)
            if (
                frozenset(namespace) != _PROFILE_KEYS_FROZEN[index]
                or tuple(namespace.get("__slots__", ())) != _PROFILE_SLOTS_FROZEN[index]
                or namespace.get("__init__") is not _PROFILE_INITS_FROZEN[index]
                or _PROFILE_INITS_FROZEN[index].__code__ is not _PROFILE_INIT_CODES_FROZEN[index]
                or namespace.get("__post_init__") is not _PROFILE_POSTS_FROZEN[index]
                or _PROFILE_POSTS_FROZEN[index].__code__ is not _PROFILE_POST_CODES_FROZEN[index]
                or namespace.get("__final__") is not _PROFILE_FINALS_FROZEN[index]
                or _PROFILE_FINALS_FROZEN[index] is not True
                or any(
                    namespace.get(name) is not descriptor or type(descriptor) is not MemberDescriptorType
                    for name, descriptor in zip(
                        _PROFILE_SLOTS_FROZEN[index],
                        _PROFILE_DESCRIPTORS_FROZEN[index],
                        strict=True,
                    )
                )
            ):
                drift = True
                break
    if drift:
        _LOGGER.error("validate_kie1_prepare_integrity_v1 error drift")
        _INTEGRITY_ERROR("kie1-prepare-integrity")
    _VALIDATE_BINDING()
    _LOGGER.debug("validate_kie1_prepare_integrity_v1 exit")


_VALIDATE_PREPARE = validate_kie1_prepare_integrity_v1
_VALIDATE_PREPARE_CODE = _VALIDATE_PREPARE.__code__


def _allocate_view_v1(cls: type[object], values: tuple[object, ...]) -> _types.KIEPrepareViewV1:
    """Allocate a fresh private view without constructor or post-init hooks."""
    _LOGGER.debug("_allocate_view_v1 entry")
    _VALIDATE_PREPARE()
    if type(values) is not tuple or cls not in _VIEW_CLASSES_FROZEN:
        _LOGGER.error("_allocate_view_v1 error class-shape")
        _INTEGRITY_ERROR("kie1-view-allocation-host-shape")
    index = _VIEW_CLASSES_FROZEN.index(cls)
    if len(values) != len(_VIEW_DESCRIPTORS_FROZEN[index]):
        _LOGGER.error("_allocate_view_v1 error arity")
        _INTEGRITY_ERROR("kie1-view-allocation-host-shape")
    result = _OBJECT_NEW(cls)
    for descriptor, value in zip(_VIEW_DESCRIPTORS_FROZEN[index], values, strict=True):
        cast(_SlotSetter, descriptor).__set__(result, value)
    _LOGGER.debug("_allocate_view_v1 exit index=%d", index)
    return cast(_types.KIEPrepareViewV1, result)


_ALLOCATE_VIEW = _allocate_view_v1
_ALLOCATE_VIEW_CODE = _ALLOCATE_VIEW.__code__


def _validate_bound_v1(bound: object) -> tuple[_kci_types.CheckerInputSyntaxV1, _keb_types.ExpectedBindingSyntaxV1]:
    """Revalidate every exact KCI/KEB slot and expected-wire equality."""
    _LOGGER.debug("_validate_bound_v1 entry")
    _VALIDATE_PREPARE()
    if type(bound) is not _BOUND_CLASS:
        _LOGGER.error("_validate_bound_v1 error bound-type")
        _INTEGRITY_ERROR("kie1-inspect-bound-host-shape")
    input_value = _BOUND_DESCRIPTORS_FROZEN[0].__get__(bound, _BOUND_CLASS)
    binding = _BOUND_DESCRIPTORS_FROZEN[1].__get__(bound, _BOUND_CLASS)
    if type(input_value) is not _INPUT_CLASS or type(binding) is not _BINDING_CLASS:
        _LOGGER.error("_validate_bound_v1 error pair-shape")
        _INTEGRITY_ERROR("kie1-inspect-bound-host-shape")
    expected = _INPUT_DESCRIPTORS_FROZEN[0].__get__(input_value, _INPUT_CLASS)
    term_bytes = _INPUT_DESCRIPTORS_FROZEN[1].__get__(input_value, _INPUT_CLASS)
    expected_term = _BINDING_DESCRIPTORS_FROZEN[0].__get__(binding, _BINDING_CLASS)
    expected_wire = _BINDING_DESCRIPTORS_FROZEN[1].__get__(binding, _BINDING_CLASS)
    if (
        type(expected) is not bytes
        or type(term_bytes) is not bytes
        or type(expected_term) is not _KPT_CLASS
        or type(expected_wire) is not bytes
    ):
        _LOGGER.error("_validate_bound_v1 error field-shape")
        _INTEGRITY_ERROR("kie1-inspect-bound-host-shape")
    equality = _BYTES_EQUAL(expected, expected_wire)
    if equality is not True:
        _LOGGER.error("_validate_bound_v1 error mismatch")
        _INTEGRITY_ERROR("kie1-inspect-bound-mismatch")
    _LOGGER.debug("_validate_bound_v1 exit")
    return input_value, binding


_VALIDATE_BOUND = _validate_bound_v1
_VALIDATE_BOUND_CODE = _VALIDATE_BOUND.__code__


def _validate_error_v1(error: object) -> _types.KIEPrepareErrorV1:
    """Revalidate the exact normal error shape while preserving its identity."""
    _LOGGER.debug("_validate_error_v1 entry")
    _VALIDATE_PREPARE()
    if type(error) is not _ERROR_CLASS:
        _LOGGER.error("_validate_error_v1 error error-type")
        _INTEGRITY_ERROR("kie1-inspect-error-host-shape")
    code = _ERROR_DESCRIPTORS_FROZEN[0].__get__(error, _ERROR_CLASS)
    offset = _ERROR_DESCRIPTORS_FROZEN[1].__get__(error, _ERROR_CLASS)
    if (
        type(code) is not _PREPARE_CODE_CLASS
        or code is not _PREPARE_CODE_CLASS.EXPECTED_WIRE_MISMATCH
        or type(offset) is not int
        or not 0 <= offset < _U64_LIMIT_FROZEN
    ):
        _LOGGER.error("_validate_error_v1 error field-shape")
        _INTEGRITY_ERROR("kie1-inspect-error-host-shape")
    _LOGGER.debug("_validate_error_v1 exit")
    return error


_VALIDATE_ERROR = _validate_error_v1
_VALIDATE_ERROR_CODE = _VALIDATE_ERROR.__code__


def InspectKIEPrepareResultV1(result: _types.KIEPrepareResultV1) -> _types.KIEPrepareViewV1:
    """Return a fresh inert BOUND or ERROR view after exact slot revalidation."""
    _LOGGER.debug("InspectKIEPrepareResultV1 entry")
    if (
        globals().get("validate_kie1_prepare_integrity_v1") is not _VALIDATE_PREPARE
        or _VALIDATE_PREPARE.__code__ is not _VALIDATE_PREPARE_CODE
        or globals().get("_allocate_view_v1") is not _ALLOCATE_VIEW
        or _ALLOCATE_VIEW.__code__ is not _ALLOCATE_VIEW_CODE
        or globals().get("_validate_bound_v1") is not _VALIDATE_BOUND
        or _VALIDATE_BOUND.__code__ is not _VALIDATE_BOUND_CODE
        or globals().get("_validate_error_v1") is not _VALIDATE_ERROR
        or _VALIDATE_ERROR.__code__ is not _VALIDATE_ERROR_CODE
    ):
        _INTEGRITY_ERROR("kie1-inspect-helper-integrity")
    _VALIDATE_PREPARE()
    if type(result) is _BOUND_RESULT_CLASS:
        bound = _RESULT_DESCRIPTORS_FROZEN[0][0].__get__(result, _BOUND_RESULT_CLASS)
        input_value, binding = _VALIDATE_BOUND(bound)
        view = _ALLOCATE_VIEW(_BOUND_VIEW_CLASS, (input_value, binding))
        _LOGGER.debug("InspectKIEPrepareResultV1 state=bound")
        _LOGGER.debug("InspectKIEPrepareResultV1 exit")
        return view
    if type(result) is _ERROR_RESULT_CLASS:
        error = _RESULT_DESCRIPTORS_FROZEN[1][0].__get__(result, _ERROR_RESULT_CLASS)
        exact_error = _VALIDATE_ERROR(error)
        view = _ALLOCATE_VIEW(_ERROR_VIEW_CLASS, (exact_error,))
        _LOGGER.debug("InspectKIEPrepareResultV1 state=error")
        _LOGGER.debug("InspectKIEPrepareResultV1 exit")
        return view
    _LOGGER.error("InspectKIEPrepareResultV1 error result-type")
    _INTEGRITY_ERROR("kie1-inspect-result-host-shape")


__all__ = ("InspectKIEPrepareResultV1", "validate_kie1_prepare_integrity_v1")
