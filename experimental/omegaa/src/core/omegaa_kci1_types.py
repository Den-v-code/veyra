"""Exact inert KCI1 input and parse-result DTOs; no checker semantics."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import TypeAlias, final

from .omegaa_kci1_common import KCI1DecodeCodeV1, KCI1ResourceKindV1

logger = logging.getLogger(__name__)


def _reject(reason: str) -> None:
    logger.debug("_reject entry reason=%s", reason)
    logger.error("KCI1 DTO rejected reason=%s", reason)
    raise TypeError(reason)


@final
@dataclass(frozen=True, slots=True)
class CheckerInputSyntaxV1:
    """Two exact opaque byte payloads; representation grants no authority."""

    expected_bytes: bytes
    term_bytes: bytes

    def __post_init__(self) -> None:
        logger.debug("CheckerInputSyntaxV1.__post_init__ entry")
        if type(self.expected_bytes) is not bytes or type(self.term_bytes) is not bytes:
            logger.error("CheckerInputSyntaxV1.__post_init__ error field-type")
            _reject("kci1-input-field-type")
        logger.debug("CheckerInputSyntaxV1.__post_init__ exit")


@final
@dataclass(frozen=True, slots=True)
class KCI1DecodeErrorV1:
    """One canonical wire failure at an absolute KCI1 byte offset."""

    code: KCI1DecodeCodeV1
    absolute_offset: int

    def __post_init__(self) -> None:
        logger.debug("KCI1DecodeErrorV1.__post_init__ entry")
        if (
            type(self.code) is not KCI1DecodeCodeV1
            or type(self.absolute_offset) is not int
            or not 0 <= self.absolute_offset < 2**64
        ):
            logger.error("KCI1DecodeErrorV1.__post_init__ error field-type")
            _reject("kci1-decode-error-field-type")
        logger.debug("KCI1DecodeErrorV1.__post_init__ exit")


@final
@dataclass(frozen=True, slots=True)
class KCI1ResourceResultV1:
    """Bounded syntax-attempt refusal, never a mathematical rejection."""

    kind: KCI1ResourceKindV1
    allowed: int
    required: int
    absolute_offset: int

    def __post_init__(self) -> None:
        logger.debug("KCI1ResourceResultV1.__post_init__ entry")
        values = (self.allowed, self.required, self.absolute_offset)
        if (
            type(self.kind) is not KCI1ResourceKindV1
            or any(type(value) is not int or not 0 <= value < 2**64 for value in values)
            or self.required <= self.allowed
        ):
            logger.error("KCI1ResourceResultV1.__post_init__ error field-type")
            _reject("kci1-resource-result-field-type")
        logger.debug("KCI1ResourceResultV1.__post_init__ exit")


@final
@dataclass(frozen=True, slots=True)
class KCI1DecodedResultV1:
    """Fresh decoded syntax and exact end offset."""

    value: CheckerInputSyntaxV1
    end: int

    def __post_init__(self) -> None:
        logger.debug("KCI1DecodedResultV1.__post_init__ entry")
        if (
            type(self.value) is not CheckerInputSyntaxV1
            or type(self.end) is not int
            or not 0 <= self.end < 2**64
        ):
            logger.error("KCI1DecodedResultV1.__post_init__ error field-type")
            _reject("kci1-decoded-result-field-type")
        logger.debug("KCI1DecodedResultV1.__post_init__ exit")


@final
@dataclass(frozen=True, slots=True)
class KCI1DecodeErrorResultV1:
    """Fresh parse-result wrapper for one canonical decode error."""

    error: KCI1DecodeErrorV1

    def __post_init__(self) -> None:
        logger.debug("KCI1DecodeErrorResultV1.__post_init__ entry")
        if type(self.error) is not KCI1DecodeErrorV1:
            logger.error("KCI1DecodeErrorResultV1.__post_init__ error field-type")
            _reject("kci1-decode-result-field-type")
        logger.debug("KCI1DecodeErrorResultV1.__post_init__ exit")


@final
@dataclass(frozen=True, slots=True)
class KCI1ResourceParseResultV1:
    """Fresh parse-result wrapper for one resource refusal."""

    resource: KCI1ResourceResultV1

    def __post_init__(self) -> None:
        logger.debug("KCI1ResourceParseResultV1.__post_init__ entry")
        if type(self.resource) is not KCI1ResourceResultV1:
            logger.error("KCI1ResourceParseResultV1.__post_init__ error field-type")
            _reject("kci1-resource-parse-result-field-type")
        logger.debug("KCI1ResourceParseResultV1.__post_init__ exit")


KCI1ParseResultV1: TypeAlias = (
    KCI1DecodedResultV1 | KCI1DecodeErrorResultV1 | KCI1ResourceParseResultV1
)
