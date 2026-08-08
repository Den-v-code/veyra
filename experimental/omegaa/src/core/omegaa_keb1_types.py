"""Exact inert syntax for a KEB1 expected KPT binding."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import TypeAlias, final

from .omegaa_keb1_common import KEB1DecodeCodeV1, KEB1ResourceKindV1, U64_LIMIT
from .omegaa_kpt1_types import KernelProofTermV1

logger = logging.getLogger(__name__)
_LOGGER = logger
_KPT_CLASS = KernelProofTermV1


class KEB1ValidationError(ValueError):
    """Host value is not the exact two-cell KEB1 syntax."""


@final
@dataclass(frozen=True, slots=True)
class ExpectedBindingSyntaxV1:
    """A KPT term paired with its canonical KPT wire; it carries no executable capability."""

    expected_term: KernelProofTermV1
    expected_wire: bytes

    def __post_init__(self) -> None:
        _LOGGER.debug("ExpectedBindingSyntaxV1.__post_init__ entry")
        if type(self.expected_term) is not _KPT_CLASS or type(self.expected_wire) is not bytes:
            _LOGGER.error("ExpectedBindingSyntaxV1.__post_init__ error host-shape")
            raise KEB1ValidationError("binding-host-shape")
        _LOGGER.debug("ExpectedBindingSyntaxV1.__post_init__ exit bytes=%d", len(self.expected_wire))


def _reject(reason: str) -> None:
    _LOGGER.debug("_reject entry reason=%s", reason)
    _LOGGER.error("KEB1 DTO rejected reason=%s", reason)
    raise TypeError(reason)


@final
@dataclass(frozen=True, slots=True)
class KEB1DecodeErrorV1:
    code: KEB1DecodeCodeV1
    absolute_offset: int

    def __post_init__(self) -> None:
        _LOGGER.debug("KEB1DecodeErrorV1.__post_init__ entry")
        if type(self.code) is not KEB1DecodeCodeV1 or type(self.absolute_offset) is not int or not 0 <= self.absolute_offset < U64_LIMIT:
            _reject("keb1-decode-error-field-type")
        _LOGGER.debug("KEB1DecodeErrorV1.__post_init__ exit")


@final
@dataclass(frozen=True, slots=True)
class KEB1ResourceResultV1:
    kind: KEB1ResourceKindV1
    allowed: int
    required: int
    absolute_offset: int

    def __post_init__(self) -> None:
        _LOGGER.debug("KEB1ResourceResultV1.__post_init__ entry")
        values = (self.allowed, self.required, self.absolute_offset)
        if type(self.kind) is not KEB1ResourceKindV1 or any(type(v) is not int or not 0 <= v < U64_LIMIT for v in values) or self.required <= self.allowed:
            _reject("keb1-resource-result-field-type")
        _LOGGER.debug("KEB1ResourceResultV1.__post_init__ exit")


@final
@dataclass(frozen=True, slots=True)
class KEB1DecodedResultV1:
    value: ExpectedBindingSyntaxV1
    end: int

    def __post_init__(self) -> None:
        _LOGGER.debug("KEB1DecodedResultV1.__post_init__ entry")
        if type(self.value) is not ExpectedBindingSyntaxV1 or type(self.end) is not int or not 0 <= self.end < U64_LIMIT:
            _reject("keb1-decoded-result-field-type")
        _LOGGER.debug("KEB1DecodedResultV1.__post_init__ exit")


@final
@dataclass(frozen=True, slots=True)
class KEB1DecodeErrorResultV1:
    error: KEB1DecodeErrorV1

    def __post_init__(self) -> None:
        _LOGGER.debug("KEB1DecodeErrorResultV1.__post_init__ entry")
        if type(self.error) is not KEB1DecodeErrorV1:
            _reject("keb1-decode-result-field-type")
        _LOGGER.debug("KEB1DecodeErrorResultV1.__post_init__ exit")


@final
@dataclass(frozen=True, slots=True)
class KEB1ResourceParseResultV1:
    resource: KEB1ResourceResultV1

    def __post_init__(self) -> None:
        _LOGGER.debug("KEB1ResourceParseResultV1.__post_init__ entry")
        if type(self.resource) is not KEB1ResourceResultV1:
            _reject("keb1-resource-parse-result-field-type")
        _LOGGER.debug("KEB1ResourceParseResultV1.__post_init__ exit")


KEB1ParseResultV1: TypeAlias = KEB1DecodedResultV1 | KEB1DecodeErrorResultV1 | KEB1ResourceParseResultV1
