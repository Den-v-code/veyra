"""Exact inert KIE1 binding, preparation, view, and rebased-origin DTOs."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import TypeAlias, final

from . import omegaa_kie1_common as _common
from .omegaa_kci1_types import CheckerInputSyntaxV1
from .omegaa_keb1_types import ExpectedBindingSyntaxV1
from .omegaa_kie1_common import KIEPayloadOriginV1, KIEPrepareCodeV1, U64_LIMIT
from .omegaa_kpt1_common import KPT1DecodeCodeV1
from .omegaa_kpt1_types import KernelProofTermV1

logger = logging.getLogger(__name__)
_LOGGER = logger
_INPUT_CLASS = CheckerInputSyntaxV1
_BINDING_CLASS = ExpectedBindingSyntaxV1
_KPT_CLASS = KernelProofTermV1
_PREPARE_CODE_CLASS = KIEPrepareCodeV1
_KPT_CODE_CLASS = KPT1DecodeCodeV1
_KPT_CODES_FROZEN = tuple(_KPT_CODE_CLASS(index) for index in range(11))
_U64_LIMIT_FROZEN = U64_LIMIT
_INPUT_EXPECTED_SLOT = vars(_INPUT_CLASS)["expected_bytes"]
_BINDING_TERM_SLOT = vars(_BINDING_CLASS)["expected_term"]
_BINDING_WIRE_SLOT = vars(_BINDING_CLASS)["expected_wire"]


def _reject(reason: str) -> None:
    """Reject direct hostile DTO construction; this is not a normal mismatch."""
    _LOGGER.debug("_reject entry reason=%s", reason)
    _LOGGER.error("KIE1 DTO rejected reason=%s", reason)
    raise TypeError(reason)


@final
@dataclass(frozen=True, slots=True)
class BoundExpectedInputV1:
    """One inert input/binding pair whose expected bytes currently agree."""

    input: CheckerInputSyntaxV1
    binding: ExpectedBindingSyntaxV1

    def __post_init__(self) -> None:
        _LOGGER.debug("BoundExpectedInputV1.__post_init__ entry")
        if type(self.input) is not _INPUT_CLASS or type(self.binding) is not _BINDING_CLASS:
            _LOGGER.error("BoundExpectedInputV1.__post_init__ error host-shape")
            _reject("kie1-bound-host-shape")
        expected = _INPUT_EXPECTED_SLOT.__get__(self.input, _INPUT_CLASS)
        term = _BINDING_TERM_SLOT.__get__(self.binding, _BINDING_CLASS)
        wire = _BINDING_WIRE_SLOT.__get__(self.binding, _BINDING_CLASS)
        if type(expected) is not bytes or type(term) is not _KPT_CLASS or type(wire) is not bytes or expected != wire:
            _LOGGER.error("BoundExpectedInputV1.__post_init__ error invariant")
            _reject("kie1-bound-invariant")
        _LOGGER.debug("BoundExpectedInputV1.__post_init__ exit")


@final
@dataclass(frozen=True, slots=True)
class KIEPrepareErrorV1:
    """Normal expected-wire mismatch at an absolute KCI1 byte offset."""

    code: KIEPrepareCodeV1
    absolute_kci_offset: int

    def __post_init__(self) -> None:
        _LOGGER.debug("KIEPrepareErrorV1.__post_init__ entry")
        if (
            globals().get("U64_LIMIT") is not _U64_LIMIT_FROZEN
            or vars(_common).get("U64_LIMIT") is not _U64_LIMIT_FROZEN
            or _U64_LIMIT_FROZEN != 18_446_744_073_709_551_616
            or type(self.code) is not _PREPARE_CODE_CLASS
            or self.code is not _PREPARE_CODE_CLASS.EXPECTED_WIRE_MISMATCH
            or type(self.absolute_kci_offset) is not int
            or not 0 <= self.absolute_kci_offset < _U64_LIMIT_FROZEN
        ):
            _LOGGER.error("KIEPrepareErrorV1.__post_init__ error host-shape")
            _reject("kie1-prepare-error-host-shape")
        _LOGGER.debug("KIEPrepareErrorV1.__post_init__ exit")


@final
@dataclass(frozen=True, slots=True)
class _KIEBoundResultV1:
    """Private normal-sum arm; nominal shape grants no provenance."""

    bound: BoundExpectedInputV1

    def __post_init__(self) -> None:
        _LOGGER.debug("_KIEBoundResultV1.__post_init__ entry")
        if type(self.bound) is not BoundExpectedInputV1:
            _LOGGER.error("_KIEBoundResultV1.__post_init__ error host-shape")
            _reject("kie1-bound-result-host-shape")
        _LOGGER.debug("_KIEBoundResultV1.__post_init__ exit")


@final
@dataclass(frozen=True, slots=True)
class _KIEInitErrorResultV1:
    """Private normal-sum mismatch arm."""

    error: KIEPrepareErrorV1

    def __post_init__(self) -> None:
        _LOGGER.debug("_KIEInitErrorResultV1.__post_init__ entry")
        if type(self.error) is not KIEPrepareErrorV1:
            _LOGGER.error("_KIEInitErrorResultV1.__post_init__ error host-shape")
            _reject("kie1-error-result-host-shape")
        _LOGGER.debug("_KIEInitErrorResultV1.__post_init__ exit")


KIEPrepareResultV1: TypeAlias = _KIEBoundResultV1 | _KIEInitErrorResultV1


@final
@dataclass(frozen=True, slots=True)
class _KIEBoundViewV1:
    """Fresh inert downstream view; exact class is not an authority token."""

    input: CheckerInputSyntaxV1
    binding: ExpectedBindingSyntaxV1

    def __post_init__(self) -> None:
        _LOGGER.debug("_KIEBoundViewV1.__post_init__ entry")
        if type(self.input) is not _INPUT_CLASS or type(self.binding) is not _BINDING_CLASS:
            _LOGGER.error("_KIEBoundViewV1.__post_init__ error host-shape")
            _reject("kie1-bound-view-host-shape")
        _LOGGER.debug("_KIEBoundViewV1.__post_init__ exit")


@final
@dataclass(frozen=True, slots=True)
class _KIEErrorViewV1:
    """Fresh inert view retaining the original normal error identity."""

    original_error: KIEPrepareErrorV1

    def __post_init__(self) -> None:
        _LOGGER.debug("_KIEErrorViewV1.__post_init__ entry")
        if type(self.original_error) is not KIEPrepareErrorV1:
            _LOGGER.error("_KIEErrorViewV1.__post_init__ error host-shape")
            _reject("kie1-error-view-host-shape")
        _LOGGER.debug("_KIEErrorViewV1.__post_init__ exit")


KIEPrepareViewV1: TypeAlias = _KIEBoundViewV1 | _KIEErrorViewV1


@final
@dataclass(frozen=True, slots=True)
class KIEKPTDecodeAtInputV1:
    """An unchanged KPT1 decode code rebased to an absolute KCI1 offset."""

    code: KPT1DecodeCodeV1
    absolute_kci_offset: int

    def __post_init__(self) -> None:
        _LOGGER.debug("KIEKPTDecodeAtInputV1.__post_init__ entry")
        if (
            globals().get("U64_LIMIT") is not _U64_LIMIT_FROZEN
            or vars(_common).get("U64_LIMIT") is not _U64_LIMIT_FROZEN
            or _U64_LIMIT_FROZEN != 18_446_744_073_709_551_616
            or type(self.code) is not _KPT_CODE_CLASS
            or len(_KPT_CODES_FROZEN) != 11
            or any(
                type(code) is not _KPT_CODE_CLASS
                or code is not _KPT_CODE_CLASS(index)
                or object.__getattribute__(code, "_value_") != index
                for index, code in enumerate(_KPT_CODES_FROZEN)
            )
            or not any(self.code is code for code in _KPT_CODES_FROZEN)
            or type(self.absolute_kci_offset) is not int
            or not 0 <= self.absolute_kci_offset < _U64_LIMIT_FROZEN
        ):
            _LOGGER.error("KIEKPTDecodeAtInputV1.__post_init__ error host-shape")
            _reject("kie1-kpt-origin-host-shape")
        _LOGGER.debug("KIEKPTDecodeAtInputV1.__post_init__ exit")


__all__ = (
    "BoundExpectedInputV1",
    "KIEKPTDecodeAtInputV1",
    "KIEPayloadOriginV1",
    "KIEPrepareCodeV1",
    "KIEPrepareErrorV1",
    "KIEPrepareResultV1",
    "KIEPrepareViewV1",
)
