"""Shared frozen tables, slots, limits, and result helpers for KCS1."""

from __future__ import annotations

from dataclasses import fields
import logging
from types import MemberDescriptorType, MappingProxyType
from typing import Protocol, cast

from . import omegaa_kcs1_types as t
from .omegaa_kcs1_builder import _build_result_v1, validate_kcs1_builder_integrity_v1

logger = logging.getLogger(__name__)
KCN1_PREFIX = b"KCN1"
KCS1_PREFIX = b"KCS1"
KRR1_PREFIX = b"KRR1"
KRL1_PREFIX = b"KRL1"
KRF1_PREFIX = b"KRF1"
KAR1_PREFIX = b"KAR1"
KCS1_MAX_SAFE_DEPTH = 132

_DOMAIN_NAMES = ("KCN1", "KCS1", "KRR1", "KRL1", "KRF1", "KAR1")
_PREFIXES = (KCN1_PREFIX, KCS1_PREFIX, KRR1_PREFIX, KRL1_PREFIX, KRF1_PREFIX, KAR1_PREFIX)
_DECODE_ENUMS = (
    t.KCN1DecodeCodeV1,
    t.KCS1DecodeCodeV1,
    t.KRR1DecodeCodeV1,
    t.KRL1DecodeCodeV1,
    t.KRF1DecodeCodeV1,
    t.KAR1DecodeCodeV1,
)
_DECODE_ERROR_CLASSES = (
    t.KCN1DecodeErrorV1,
    t.KCS1DecodeErrorV1,
    t.KRR1DecodeErrorV1,
    t.KRL1DecodeErrorV1,
    t.KRF1DecodeErrorV1,
    t.KAR1DecodeErrorV1,
)
_DECODE_RESULT_CLASSES = (
    t.KCN1DecodeErrorResultV1,
    t.KCS1DecodeErrorResultV1,
    t.KRR1DecodeErrorResultV1,
    t.KRL1DecodeErrorResultV1,
    t.KRF1DecodeErrorResultV1,
    t.KAR1DecodeErrorResultV1,
)
_DECODED_CLASSES = (
    t.KCN1DecodedResultV1,
    t.KCS1DecodedResultV1,
    t.KRR1DecodedResultV1,
    t.KRL1DecodedResultV1,
    t.KRF1DecodedResultV1,
    t.KAR1DecodedResultV1,
)
_RESOURCE_ARM_CLASSES = (
    t.KCN1CodecResourceResultV1,
    t.KCS1CodecResourceResultV1,
    t.KRR1CodecResourceResultV1,
    t.KRL1CodecResourceResultV1,
    t.KRF1CodecResourceResultV1,
    t.KAR1CodecResourceResultV1,
)
_INTEGRITY_ARM_CLASSES = (
    t.KCN1IntegrityResultV1,
    t.KCS1IntegrityResultV1,
    t.KRR1IntegrityResultV1,
    t.KRL1IntegrityResultV1,
    t.KRF1IntegrityResultV1,
    t.KAR1IntegrityResultV1,
)
_ENCODED_CLASSES = (
    t.KCN1EncodedResultV1,
    t.KCS1EncodedResultV1,
    t.KRR1EncodedResultV1,
    t.KRL1EncodedResultV1,
    t.KRF1EncodedResultV1,
    t.KAR1EncodedResultV1,
)

_NODE_CLASSES = (
    t.KCS1EntryNodeV1,
    t.KCS1ParseNodeV1,
    t.KCS1InferNodeV1,
    t.KCS1ReduceNodeV1,
    t.KCS1CompareTypesNodeV1,
    t.KCS1ReturnTypedNodeV1,
)
_STATE_CLASSES = (t.KCS1RunStateV1, t.KCS1AcceptStateV1, t.KCS1RejectStateV1)
_REDUCTION_CLASSES = (t.KCS1NFResultSyntaxV1, t.KCS1StepResultSyntaxV1)
_LOCUS_CLASSES = (
    t.KCS1InputOffsetLocusV1,
    t.KCS1StateStepLocusV1,
    t.KCS1StructuralCountLocusV1,
    t.KCS1NoLocusV1,
)
_ATTEMPT_CLASSES = (t.KCS1TerminalAttemptV1, t.KCS1ResourceAttemptV1, t.KCS1InternalAttemptV1)
_DOMAIN_CLASSES = (
    _NODE_CLASSES,
    _STATE_CLASSES,
    _REDUCTION_CLASSES,
    _LOCUS_CLASSES,
    (t.KCS1AttemptResourceSyntaxV1,),
    _ATTEMPT_CLASSES,
)
_ARITIES = (
    (1, 1, 1, 1, 3, 1),
    (7, 2, 2),
    (1, 1),
    (1, 1, 1, 0),
    (4,),
    (1, 1, 2),
)
_TAG_BY_CLASS = tuple(
    MappingProxyType({cls: index for index, cls in enumerate(classes)}) for classes in _DOMAIN_CLASSES
)
_LIMIT_NAMES = tuple(field.name for field in fields(t.KCS1CodecLimitsV1))
_LIMIT_SLOTS = tuple(vars(t.KCS1CodecLimitsV1)[name] for name in _LIMIT_NAMES)
_DEFAULT_LIMITS = t.DEFAULT_KCS1_CODEC_LIMITS_V1
_DEFAULT_VALUES = (1_048_576, 1_048_576, 132, 20_000, 4096, 1_048_576, 4096, 64)


class _Getter(Protocol):
    def __get__(self, instance: object, owner: type[object]) -> object: ...


def _domain_index(name: str) -> int:
    logger.debug("_domain_index entry name=%s", name)
    try:
        result = _DOMAIN_NAMES.index(name)
    except ValueError:
        logger.error("_domain_index error name=%s", name)
        raise ValueError("kcs1-domain") from None
    logger.debug("_domain_index exit index=%d", result)
    return result


def validate_kcs1_common_integrity_v1() -> None:
    """Reject table, enum, class, default, and slot drift."""
    logger.debug("validate_kcs1_common_integrity_v1 entry")
    validate_kcs1_builder_integrity_v1()
    values = tuple(cast(_Getter, slot).__get__(_DEFAULT_LIMITS, t.KCS1CodecLimitsV1) for slot in _LIMIT_SLOTS)
    drift = (
        globals().get("KCN1_PREFIX") != b"KCN1"
        or globals().get("KCS1_PREFIX") != b"KCS1"
        or globals().get("KRR1_PREFIX") != b"KRR1"
        or globals().get("KRL1_PREFIX") != b"KRL1"
        or globals().get("KRF1_PREFIX") != b"KRF1"
        or globals().get("KAR1_PREFIX") != b"KAR1"
        or t.DEFAULT_KCS1_CODEC_LIMITS_V1 is not _DEFAULT_LIMITS
        or values != _DEFAULT_VALUES
        or any(
            vars(t.KCS1CodecLimitsV1).get(name) is not slot or type(slot) is not MemberDescriptorType
            for name, slot in zip(_LIMIT_NAMES, _LIMIT_SLOTS, strict=True)
        )
        or any(
            len(enum_cls) != 11
            or any(
                type(enum_cls(index)) is not enum_cls or object.__getattribute__(enum_cls(index), "_value_") != index
                for index in range(11)
            )
            for enum_cls in _DECODE_ENUMS
        )
    )
    if drift:
        logger.error("validate_kcs1_common_integrity_v1 error drift")
        raise ValueError("kcs1-common-integrity")
    logger.debug("validate_kcs1_common_integrity_v1 exit")


def _slot(cls: type[object], name: str, value: object) -> object:
    logger.debug("_slot entry class=%s field=%s", cls.__name__, name)
    descriptor = vars(cls).get(name)
    if type(value) is not cls or type(descriptor) is not MemberDescriptorType:
        logger.error("_slot error host-shape")
        raise ValueError("kcs1-host-shape")
    try:
        result = cast(_Getter, descriptor).__get__(value, cls)
    except Exception as exc:
        logger.error("_slot error exception=%s", type(exc).__name__)
        raise ValueError("kcs1-host-shape") from None
    logger.debug("_slot exit")
    return result


def _snapshot_limits(limits: t.KCS1CodecLimitsV1) -> tuple[int, ...]:
    logger.debug("_snapshot_limits entry")
    validate_kcs1_common_integrity_v1()
    if type(limits) is not t.KCS1CodecLimitsV1:
        logger.error("_snapshot_limits error class")
        raise ValueError("kcs1-limit-drift")
    raw_values = tuple(cast(_Getter, slot).__get__(limits, t.KCS1CodecLimitsV1) for slot in _LIMIT_SLOTS)
    if any(type(value) is not int for value in raw_values):
        logger.error("_snapshot_limits error type")
        raise ValueError("kcs1-limit-drift")
    values = cast(tuple[int, ...], raw_values)
    if any(type(value) is not int or not 0 < value < 2**64 for value in values) or values[2] > KCS1_MAX_SAFE_DEPTH:
        logger.error("_snapshot_limits error value")
        raise ValueError("kcs1-limit-drift")
    logger.debug("_snapshot_limits exit")
    return values


def _u64(value: int) -> bytes:
    logger.debug("_u64 entry")
    if type(value) is not int or not 0 <= value < 2**64:
        raise ValueError("kcs1-u64")
    result = value.to_bytes(8, "big")
    logger.debug("_u64 exit")
    return result


def _mag(value: int) -> bytes:
    logger.debug("_mag entry")
    if type(value) is not int or value < 0:
        raise ValueError("kcs1-nat")
    size = 0 if value == 0 else (value.bit_length() + 7) // 8
    result = value.to_bytes(size, "big")
    logger.debug("_mag exit bytes=%d", size)
    return result


def _nat(value: int) -> bytes:
    logger.debug("_nat entry")
    magnitude = _mag(value)
    result = _u64(len(magnitude)) + magnitude
    logger.debug("_nat exit bytes=%d", len(result))
    return result


def _frame(payload: bytes) -> bytes:
    logger.debug("_frame entry")
    if type(payload) is not bytes:
        raise ValueError("kcs1-frame")
    result = _u64(len(payload)) + payload
    logger.debug("_frame exit bytes=%d", len(result))
    return result


def _decode_arm(domain: str, ordinal: int, offset: int) -> object:
    logger.debug("_decode_arm entry domain=%s", domain)
    index = _domain_index(domain)
    if type(ordinal) is not int or not 0 <= ordinal < 11 or type(offset) is not int or not 0 <= offset < 2**64:
        raise ValueError("kcs1-decode-arm")
    error = _build_result_v1(_DECODE_ERROR_CLASSES[index], (_DECODE_ENUMS[index](ordinal), offset))
    result = _build_result_v1(_DECODE_RESULT_CLASSES[index], (error,))
    logger.error("%s decode rejected code=%s offset=%d", domain, _DECODE_ENUMS[index](ordinal).name, offset)
    logger.debug("_decode_arm exit")
    return result


def _resource_arm(domain: str, kind: t.KCS1CodecResourceKindV1, allowed: int, required: int, offset: int) -> object:
    logger.debug("_resource_arm entry domain=%s", domain)
    index = _domain_index(domain)
    if (
        type(kind) is not t.KCS1CodecResourceKindV1
        or any(type(x) is not int or not 0 <= x < 2**64 for x in (allowed, required, offset))
        or required <= allowed
    ):
        raise ValueError("kcs1-resource-arm")
    resource = _build_result_v1(t.KCS1CodecResourceV1, (kind, allowed, required, offset))
    result = _build_result_v1(_RESOURCE_ARM_CLASSES[index], (resource,))
    logger.error(
        "%s resource refused kind=%s allowed=%d required=%d offset=%d", domain, kind.name, allowed, required, offset
    )
    logger.debug("_resource_arm exit")
    return result


def _integrity_arm(domain: str, code: t.KCS1IntegrityCodeV1) -> object:
    logger.debug("_integrity_arm entry domain=%s", domain)
    index = _domain_index(domain)
    error = _build_result_v1(t.KCS1IntegrityV1, (code,))
    result = _build_result_v1(_INTEGRITY_ARM_CLASSES[index], (error,))
    logger.error("%s integrity refused code=%s", domain, code.name)
    logger.debug("_integrity_arm exit")
    return result


def _decoded_arm(domain: str, value: object, end: int) -> object:
    logger.debug("_decoded_arm entry domain=%s", domain)
    index = _domain_index(domain)
    if type(value) not in _DOMAIN_CLASSES[index] or type(end) is not int or not 0 <= end < 2**64:
        raise ValueError("kcs1-decoded-arm")
    result = _build_result_v1(_DECODED_CLASSES[index], (value, end))
    logger.debug("_decoded_arm exit")
    return result


def _encoded_arm(domain: str, wire: bytes) -> object:
    logger.debug("_encoded_arm entry domain=%s", domain)
    index = _domain_index(domain)
    if type(wire) is not bytes:
        raise ValueError("kcs1-encoded-arm")
    result = _build_result_v1(_ENCODED_CLASSES[index], (wire,))
    logger.debug("_encoded_arm exit")
    return result
