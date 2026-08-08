"""Exact budgeted R11 case evaluation with deterministic semantic caching."""
from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import logging
from typing import cast

from .observer_core_codec import (
    ObserverCodecError,
    canonical_observer_bytes,
)
from .observer_core_semantics import ObserverCoreError, echo
from .observer_core_support import outcome_data
from .observer_core_types import DomainBlocked, Echo, Mismatch, ObserverExpr
from .proof_core_codec import canonical_json
from .observer_synthesis_v2_budget import MAX_EVALUATIONS, BudgetLedger, BudgetValidationError
from .observer_synthesis_v2_protocol import (
    OUTCOME_SCHEMA,
    CacheDisposition,
    CaseEvaluationResultV2,
    CaseEvaluationV2,
    EvaluationInvalidReason,
    ExpectedRelation,
    InvalidCaseEvaluationV2,
    ObserverSynthesisProtocolError,
    validate_observer_case_v2,
)
from .observer_synthesis_v2_types import SynthesisStatus

logger = logging.getLogger(__name__)

EvaluationCacheKey = tuple[str, str]


@dataclass(frozen=True, slots=True)
class _CachedEvaluationV2:
    """Run-bound untrusted cache row accepted only after exact R11 replay."""

    run_nonce: object
    result: CaseEvaluationV2


class EvaluationCacheV2:
    """Run-bound cache whose hits are charged exact audit re-evaluations."""

    __slots__ = ("_rows", "_ledger", "_run_nonce")

    def __init__(self) -> None:
        logger.debug("EvaluationCacheV2.__init__ entry")
        self._rows: dict[EvaluationCacheKey, _CachedEvaluationV2] = {}
        self._ledger: BudgetLedger | None = None
        self._run_nonce = object()
        logger.debug("EvaluationCacheV2.__init__ exit")

    def _bind_ledger(self, ledger: BudgetLedger) -> bool:
        logger.debug("EvaluationCacheV2._bind_ledger entry")
        if self._ledger is None:
            self._ledger = ledger
            logger.info("EvaluationCacheV2 state=bound")
        result = self._ledger is ledger
        if not result:
            logger.error("EvaluationCacheV2 ledger transplant rejected")
        logger.debug("EvaluationCacheV2._bind_ledger exit result=%s", result)
        return result

    def _lookup(self, key: EvaluationCacheKey) -> _CachedEvaluationV2 | None:
        logger.debug("EvaluationCacheV2._lookup entry")
        if (
            type(self._rows) is not dict or len(self._rows) > MAX_EVALUATIONS
            or any(
                type(stored) is not tuple
                or len(stored) != 2
                or any(type(item) is not str for item in stored)
                for stored in self._rows
            )
        ):
            logger.error("EvaluationCacheV2._lookup invalid storage")
            raise ValueError("invalid-evaluation-cache-storage")
        result = self._rows.get(key)
        logger.debug(
            "EvaluationCacheV2._lookup exit disposition=%s",
            "hit" if result is not None else "miss",
        )
        return result

    def _store(
        self,
        key: EvaluationCacheKey,
        result: CaseEvaluationV2,
    ) -> None:
        logger.debug("EvaluationCacheV2._store entry")
        if key in self._rows:
            logger.error("EvaluationCacheV2._store duplicate key")
            raise ValueError("duplicate-evaluation-cache-key")
        self._rows[key] = _CachedEvaluationV2(self._run_nonce, result)
        logger.debug("EvaluationCacheV2._store exit rows=%d", len(self._rows))

    def size(self) -> int:
        logger.debug("EvaluationCacheV2.size entry")
        result = len(self._rows)
        logger.debug("EvaluationCacheV2.size exit rows=%d", result)
        return result


def _invalid(reason: EvaluationInvalidReason) -> InvalidCaseEvaluationV2:
    logger.error("R14.3a evaluation invalid reason=%s", reason.value)
    result = InvalidCaseEvaluationV2(SynthesisStatus.INVALID, reason)
    logger.debug("_invalid exit status=%s", result.status.value)
    return result


def _actual_relation(outcome: object) -> ExpectedRelation:
    logger.debug("_actual_relation entry type=%s", type(outcome).__name__)
    if type(outcome) is Echo:
        result = ExpectedRelation.ECHO
    elif type(outcome) is Mismatch:
        result = ExpectedRelation.SEPARATE
    elif type(outcome) is DomainBlocked:
        result = ExpectedRelation.DOMAIN_BLOCKED
    else:
        logger.error("_actual_relation invalid outcome type=%s", type(outcome).__name__)
        raise ValueError("invalid-evaluation-outcome")
    logger.debug("_actual_relation exit relation=%s", result.value)
    return result


def _observer_identity(observer: object) -> tuple[ObserverExpr, str]:
    logger.debug("_observer_identity entry type=%s", type(observer).__name__)
    canonical = canonical_observer_bytes(observer)
    result = cast(ObserverExpr, observer), sha256(canonical).hexdigest()
    logger.debug("_observer_identity exit digest=%s", result[1][:12])
    return result


def _outcome_digest(canonical_outcome: bytes) -> str:
    logger.debug("_outcome_digest entry bytes=%d", len(canonical_outcome))
    result = sha256(
        OUTCOME_SCHEMA.encode("ascii") + b"\0" + canonical_outcome
    ).hexdigest()
    logger.debug("_outcome_digest exit digest=%s", result[:12])
    return result


def _valid_cached_result(
    cached: object,
    key: EvaluationCacheKey,
    replayed: CaseEvaluationV2,
    run_nonce: object,
) -> bool:
    logger.debug("_valid_cached_result entry type=%s", type(cached).__name__)
    valid = (
        type(cached) is _CachedEvaluationV2
        and cached.run_nonce is run_nonce
        and type(cached.result) is CaseEvaluationV2
    )
    if valid:
        result = cast(_CachedEvaluationV2, cached).result
        valid = (
            type(result.observer_digest) is str
            and result.observer_digest == key[0]
            and type(result.case_digest) is str
            and result.case_digest == key[1]
            and type(result.expected) is ExpectedRelation
            and type(result.actual) is ExpectedRelation
            and type(result.canonical_outcome) is bytes
            and bool(result.canonical_outcome)
            and type(result.outcome_digest) is str
            and result.outcome_digest
            == _outcome_digest(result.canonical_outcome)
            and type(result.matched) is bool
            and result.matched is (result.actual is result.expected)
            and result.cache_disposition is CacheDisposition.MISS
            and type(result.evaluation_charge) is int
            and result.evaluation_charge == 1
        )
        if valid:
            valid = (
                result.observer_digest == replayed.observer_digest
                and result.case_digest == replayed.case_digest
                and result.expected is replayed.expected
                and result.actual is replayed.actual
                and result.canonical_outcome == replayed.canonical_outcome
                and result.outcome_digest == replayed.outcome_digest
                and result.matched is replayed.matched
                and result.cache_disposition is replayed.cache_disposition
                and result.evaluation_charge == replayed.evaluation_charge
            )
    logger.debug("_valid_cached_result exit valid=%s", valid)
    return valid


def _replay_exact(
    observer: ObserverExpr,
    observer_digest: str,
    case: object,
) -> CaseEvaluationV2:
    logger.debug("_replay_exact entry")
    valid_case = validate_observer_case_v2(case)
    outcome = echo(observer, valid_case.left, valid_case.right)
    actual = _actual_relation(outcome)
    canonical_outcome = canonical_json(
        {"outcome": outcome_data(outcome), "schema": OUTCOME_SCHEMA}
    ).encode("utf-8")
    result = CaseEvaluationV2(
        observer_digest,
        valid_case.case_digest,
        valid_case.expected,
        actual,
        canonical_outcome,
        _outcome_digest(canonical_outcome),
        actual is valid_case.expected,
        CacheDisposition.MISS,
        1,
    )
    logger.debug("_replay_exact exit matched=%s", result.matched)
    return result


def evaluate_observer_case_v2(
    observer: object,
    case: object,
    ledger: object,
    cache: object,
) -> CaseEvaluationResultV2:
    """Evaluate one exact semantic pair; a miss precharges exactly one eval."""
    logger.debug(
        "evaluate_observer_case_v2 entry observer_type=%s case_type=%s",
        type(observer).__name__,
        type(case).__name__,
    )
    if type(ledger) is not BudgetLedger:
        return _invalid(EvaluationInvalidReason.LEDGER)
    if type(cache) is not EvaluationCacheV2:
        return _invalid(EvaluationInvalidReason.CACHE)
    try:
        valid_case = validate_observer_case_v2(case)
    except ObserverSynthesisProtocolError:
        return _invalid(EvaluationInvalidReason.CASE)
    try:
        valid_observer, observer_digest = _observer_identity(observer)
    except (ObserverCodecError, ObserverCoreError, TypeError, ValueError, RecursionError):
        return _invalid(EvaluationInvalidReason.OBSERVER)
    if not cache._bind_ledger(ledger):
        return _invalid(EvaluationInvalidReason.CACHE)
    key = (observer_digest, valid_case.case_digest)
    try:
        cached = cache._lookup(key)
    except (RuntimeError, TypeError, ValueError):
        return _invalid(EvaluationInvalidReason.CACHE)
    if cached is not None:
        try:
            ledger.checkpoint()
            ledger.charge_evaluations(1)
            replayed = _replay_exact(valid_observer, observer_digest, valid_case)
        except BudgetValidationError:
            return _invalid(EvaluationInvalidReason.LEDGER)
        except (
            ObserverSynthesisProtocolError,
            ObserverCoreError,
            TypeError,
            ValueError,
            RecursionError,
        ):
            return _invalid(EvaluationInvalidReason.OUTCOME)
        if not _valid_cached_result(cached, key, replayed, cache._run_nonce):
            return _invalid(EvaluationInvalidReason.CACHE)
        result = replace(
            replayed,
            cache_disposition=CacheDisposition.HIT,
            evaluation_charge=1,
        )
        logger.info(
            "evaluate_observer_case_v2 cache state=hit case_id=%d",
            valid_case.case_id,
        )
        logger.debug("evaluate_observer_case_v2 exit matched=%s", result.matched)
        return result
    try:
        ledger.charge_evaluations(1)
    except BudgetValidationError:
        return _invalid(EvaluationInvalidReason.LEDGER)
    try:
        result = _replay_exact(valid_observer, observer_digest, valid_case)
    except (
        ObserverSynthesisProtocolError,
        ObserverCoreError,
        TypeError,
        ValueError,
        RecursionError,
    ):
        return _invalid(EvaluationInvalidReason.OUTCOME)
    cache._store(key, result)
    logger.info(
        "evaluate_observer_case_v2 cache state=miss case_id=%d matched=%s",
        valid_case.case_id,
        result.matched,
    )
    logger.debug("evaluate_observer_case_v2 exit matched=%s", result.matched)
    return result
