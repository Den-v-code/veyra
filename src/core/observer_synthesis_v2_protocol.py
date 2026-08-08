"""Closed immutable case and evaluation protocol for R14.3a."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging
from typing import NoReturn, TypeAlias

from .observer_core_semantics import ObserverCoreError, validate_closed_recurrence
from .proof_core_codec import digest_data, term_data
from .proof_core_types import CoreTerm
from .observer_synthesis_v2_types import SynthesisStatus

logger = logging.getLogger(__name__)

CASE_SCHEMA = "veyra.observer-synthesis-v2.case.r14.3a.v1"
OUTCOME_SCHEMA = "veyra.observer-synthesis-v2.outcome.r14.3a.v1"
MAX_CASE_ID = (1 << 31) - 1
MAX_GROUP_ID = MAX_CASE_ID


class ExpectedRelation(str, Enum):
    """The complete expected relation vocabulary for one corpus case."""

    ECHO = "ECHO"
    SEPARATE = "SEPARATE"
    DOMAIN_BLOCKED = "DOMAIN_BLOCKED"


class SplitId(str, Enum):
    """The complete locked corpus split vocabulary."""

    TRAIN = "TRAIN"
    HOLDOUT = "HOLDOUT"
    UNSEEN = "UNSEEN"
    ADVERSARIAL = "ADVERSARIAL"


class CacheDisposition(str, Enum):
    """Whether this semantic pair was evaluated or reused exactly."""

    MISS = "MISS"
    HIT = "HIT"


class EvaluationInvalidReason(str, Enum):
    """Typed malformed-input reasons; each maps only to INVALID."""

    CASE = "invalid-case"
    OBSERVER = "invalid-observer"
    LEDGER = "invalid-ledger"
    CACHE = "invalid-cache"
    OUTCOME = "invalid-outcome"


@dataclass(frozen=True, slots=True)
class ObserverCaseV2:
    """One ordered left/right recurrence pair with committed expectation."""

    case_id: int
    group_id: int
    split: SplitId
    left: CoreTerm
    right: CoreTerm
    expected: ExpectedRelation
    required_for_winner: bool
    payload_digest: str
    clone_digest: str
    case_digest: str


@dataclass(frozen=True, slots=True)
class CaseEvaluationV2:
    """One exact R11 evaluation, including explicit cache charging policy."""

    observer_digest: str
    case_digest: str
    expected: ExpectedRelation
    actual: ExpectedRelation
    canonical_outcome: bytes
    outcome_digest: str
    matched: bool
    cache_disposition: CacheDisposition
    evaluation_charge: int


@dataclass(frozen=True, slots=True)
class InvalidCaseEvaluationV2:
    """Typed non-success result for malformed observer/case/configuration."""

    status: SynthesisStatus
    reason: EvaluationInvalidReason


CaseEvaluationResultV2: TypeAlias = CaseEvaluationV2 | InvalidCaseEvaluationV2


class ObserverSynthesisProtocolError(ValueError):
    """Stable fail-closed protocol validation rejection."""


def _reject(reason: str) -> NoReturn:
    logger.error("observer synthesis v2 protocol rejected reason=%s", reason)
    raise ObserverSynthesisProtocolError(reason)


def _ordered_payload_data(left: CoreTerm, right: CoreTerm) -> list[object]:
    logger.debug("_ordered_payload_data entry")
    try:
        validate_closed_recurrence(left)
        validate_closed_recurrence(right)
        result = ["left-right", term_data(left), term_data(right)]
    except (ObserverCoreError, TypeError, ValueError, RecursionError):
        _reject("invalid-case-recurrence")
    logger.debug("_ordered_payload_data exit")
    return result


def ordered_payload_digest(left: CoreTerm, right: CoreTerm) -> str:
    """Hash the canonical left/right sequence without sorting its sides."""
    logger.debug("ordered_payload_digest entry")
    try:
        result = digest_data(
            _ordered_payload_data(left, right),
            f"{CASE_SCHEMA}.ordered-payload",
        )
    except ObserverSynthesisProtocolError:
        raise
    except (TypeError, ValueError, UnicodeError):
        _reject("invalid-case-digest")
    logger.debug("ordered_payload_digest exit digest=%s", result[:12])
    return result


def clone_payload_digest(left: CoreTerm, right: CoreTerm) -> str:
    """Bind unordered clone identity without changing ordered payload identity."""
    logger.debug("clone_payload_digest entry")
    ordered = _ordered_payload_data(left, right)
    try:
        sides = sorted(
            digest_data(item, f"{CASE_SCHEMA}.clone-side")
            for item in ordered[1:]
        )
        result = digest_data(sides, f"{CASE_SCHEMA}.clone-pair")
    except ObserverSynthesisProtocolError:
        raise
    except (TypeError, ValueError, UnicodeError):
        _reject("invalid-case-digest")
    logger.debug("clone_payload_digest exit digest=%s", result[:12])
    return result


def _is_digest(value: object) -> bool:
    logger.debug("_is_digest entry type=%s", type(value).__name__)
    result = (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )
    logger.debug("_is_digest exit result=%s", result)
    return result


def _case_digest(
    case_id: int,
    group_id: int,
    split: SplitId,
    expected: ExpectedRelation,
    required_for_winner: bool,
    payload_digest: str,
    clone_digest: str,
) -> str:
    logger.debug("_case_digest entry case_id=%d", case_id)
    try:
        result = digest_data(
            {
                "case_id": case_id,
                "clone_digest": clone_digest,
                "expected": expected.value,
                "group_id": group_id,
                "payload_digest": payload_digest,
                "required_for_winner": required_for_winner,
                "schema": CASE_SCHEMA,
                "split": split.value,
            },
            f"{CASE_SCHEMA}.case",
        )
    except (TypeError, ValueError, UnicodeError):
        _reject("invalid-case-digest")
    logger.debug("_case_digest exit digest=%s", result[:12])
    return result


def build_observer_case_v2(
    case_id: object,
    group_id: object,
    split: object,
    left: CoreTerm,
    right: CoreTerm,
    expected: object,
    required_for_winner: object,
) -> ObserverCaseV2:
    """Build one exact frozen case; strings and callables are not extensions."""
    logger.debug(
        "build_observer_case_v2 entry id_type=%s group_type=%s split_type=%s",
        type(case_id).__name__,
        type(group_id).__name__,
        type(split).__name__,
    )
    if (
        type(case_id) is not int
        or not 0 < case_id <= MAX_CASE_ID
        or type(group_id) is not int
        or not 0 < group_id <= MAX_GROUP_ID
        or type(split) is not SplitId
        or type(expected) is not ExpectedRelation
        or type(required_for_winner) is not bool
    ):
        _reject("invalid-case-header")
    payload = ordered_payload_digest(left, right)
    clone = clone_payload_digest(left, right)
    result = ObserverCaseV2(
        case_id,
        group_id,
        split,
        left,
        right,
        expected,
        required_for_winner,
        payload,
        clone,
        _case_digest(
            case_id,
            group_id,
            split,
            expected,
            required_for_winner,
            payload,
            clone,
        ),
    )
    logger.debug("build_observer_case_v2 exit case_id=%d", result.case_id)
    return result


def validate_observer_case_v2(case: object) -> ObserverCaseV2:
    """Replay every exact field and both ordered recurrence payloads."""
    logger.debug("validate_observer_case_v2 entry type=%s", type(case).__name__)
    if type(case) is not ObserverCaseV2:
        _reject("invalid-case-type")
    if (
        type(case.case_id) is not int
        or not 0 < case.case_id <= MAX_CASE_ID
        or type(case.group_id) is not int
        or not 0 < case.group_id <= MAX_GROUP_ID
        or type(case.split) is not SplitId
        or type(case.expected) is not ExpectedRelation
        or type(case.required_for_winner) is not bool
        or not _is_digest(case.payload_digest)
        or not _is_digest(case.clone_digest)
        or not _is_digest(case.case_digest)
    ):
        _reject("invalid-case-fields")
    payload = ordered_payload_digest(case.left, case.right)
    clone = clone_payload_digest(case.left, case.right)
    expected_case_digest = _case_digest(
        case.case_id,
        case.group_id,
        case.split,
        case.expected,
        case.required_for_winner,
        payload,
        clone,
    )
    if (
        case.payload_digest != payload
        or case.clone_digest != clone
        or case.case_digest != expected_case_digest
    ):
        _reject("invalid-case-binding")
    logger.debug("validate_observer_case_v2 exit case_id=%d", case.case_id)
    return case
