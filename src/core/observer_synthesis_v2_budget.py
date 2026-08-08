"""Deterministic precharged resource ledger for observer synthesis v2."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging
import time
from typing import NoReturn

from .observer_synthesis_v2_types import SynthesisStatus

logger = logging.getLogger(__name__)
MIB = 1024 * 1024
MAX_CANDIDATES = 2048
MAX_CANONICAL_BYTES = 8 * MIB
MAX_EVALUATIONS = 100_000
MAX_TRANSCRIPT_OUTPUT_BYTES = 8 * MIB
MAX_WALL_SECONDS = 5
MAX_PROCESS_AS_BYTES = 512 * MIB
MAX_LEDGER_INTEGER = (1 << 63) - 1
NANOSECONDS_PER_SECOND = 1_000_000_000
@dataclass(frozen=True, slots=True)
class BudgetLimits:
    """Immutable search ceilings; lower custom ceilings remain admissible."""

    candidate_limit: int = MAX_CANDIDATES
    canonical_bytes_limit: int = MAX_CANONICAL_BYTES
    evaluation_limit: int = MAX_EVALUATIONS
    transcript_output_bytes_limit: int = MAX_TRANSCRIPT_OUTPUT_BYTES
    wall_seconds: int = MAX_WALL_SECONDS
    process_as_bytes_limit: int = MAX_PROCESS_AS_BYTES


DEFAULT_BUDGET_LIMITS = BudgetLimits()
MAXIMUM_BUDGET_LIMITS = DEFAULT_BUDGET_LIMITS
class BudgetCutoffReason(str, Enum):
    """Typed hard-cutoff reasons reserved for later INCOMPLETE reports."""

    CANDIDATES = "candidate-limit"
    CANONICAL_BYTES = "canonical-bytes-limit"
    EVALUATIONS = "evaluation-limit"
    TRANSCRIPT_OUTPUT_BYTES = "transcript-output-bytes-limit"
    WALL_TIME = "wall-time-limit"
    PROCESS_ADDRESS_SPACE = "process-address-space-limit"
@dataclass(frozen=True, slots=True)
class BudgetLedgerSnapshot:
    """Immutable monotone accounting view without payload or process data."""

    limits: BudgetLimits
    candidates: int
    canonical_bytes: int
    evaluations: int
    transcript_output_bytes: int
    elapsed_ns: int
    cutoff_reason: BudgetCutoffReason | None


class BudgetValidationError(ValueError):
    """Malformed limits, charges, or clock values; later mapped to INVALID."""


class BudgetLimitExceeded(RuntimeError):
    """Internal terminal cutoff that can only map to INCOMPLETE."""

    status = SynthesisStatus.INCOMPLETE

    def __init__(self, reason: BudgetCutoffReason) -> None:
        logger.debug("BudgetLimitExceeded.__init__ entry reason=%s", reason.value)
        self.reason = reason
        super().__init__(reason.value)
        logger.error(
            "BudgetLimitExceeded.__init__ terminal status=%s reason=%s",
            self.status.value,
            reason.value,
        )


def _invalid(reason: str) -> NoReturn:
    logger.error("observer synthesis budget invalid reason=%s", reason)
    raise BudgetValidationError(reason)


def validate_budget_limits(limits: object) -> BudgetLimits:
    """Return only exact positive BudgetLimits within hard maxima."""
    logger.debug("validate_budget_limits entry type=%s", type(limits).__name__)
    if type(limits) is not BudgetLimits:
        _invalid("invalid-budget-limits-type")
    pairs = (
        (limits.candidate_limit, MAX_CANDIDATES),
        (limits.canonical_bytes_limit, MAX_CANONICAL_BYTES),
        (limits.evaluation_limit, MAX_EVALUATIONS),
        (limits.transcript_output_bytes_limit, MAX_TRANSCRIPT_OUTPUT_BYTES),
        (limits.wall_seconds, MAX_WALL_SECONDS),
        (limits.process_as_bytes_limit, MAX_PROCESS_AS_BYTES),
    )
    if any(type(value) is not int or value <= 0 or value > maximum for value, maximum in pairs):
        _invalid("invalid-budget-limits")
    logger.debug("validate_budget_limits exit")
    return limits


def snapshot_budget_limits(limits: object) -> BudgetLimits:
    """Capture caller-owned limits once, then validate the trusted copy."""
    logger.debug("snapshot_budget_limits entry type=%s", type(limits).__name__)
    if type(limits) is not BudgetLimits:
        _invalid("invalid-budget-limits-type")
    try:
        captured = BudgetLimits(
            limits.candidate_limit, limits.canonical_bytes_limit, limits.evaluation_limit,
            limits.transcript_output_bytes_limit, limits.wall_seconds,
            limits.process_as_bytes_limit,
        )
    except AttributeError:
        _invalid("invalid-budget-limits-fields")
    result = validate_budget_limits(captured)
    logger.debug("snapshot_budget_limits exit")
    return result


def _validate_charge(amount: object) -> int:
    logger.debug("_validate_charge entry type=%s", type(amount).__name__)
    if type(amount) is not int or amount < 0 or amount > MAX_LEDGER_INTEGER:
        _invalid("invalid-budget-charge")
    logger.debug("_validate_charge exit amount=%d", amount)
    return amount


_monotonic_ns = time.monotonic_ns


def _read_monotonic_ns() -> int:
    logger.debug("_read_monotonic_ns entry")
    now = _monotonic_ns()
    if type(now) is not int or now < 0 or now > MAX_LEDGER_INTEGER:
        _invalid("invalid-budget-clock")
    logger.debug("_read_monotonic_ns exit")
    return now


class BudgetLedger:
    """Mutable monotone ledger whose charge methods must precede each action."""

    __slots__ = (
        "_limits",
        "_started_ns",
        "_last_clock_ns",
        "_elapsed_ns",
        "_candidates",
        "_canonical_bytes",
        "_evaluations",
        "_transcript_output_bytes",
        "_cutoff_reason",
    )

    def __init__(self, limits: BudgetLimits = DEFAULT_BUDGET_LIMITS) -> None:
        logger.debug("BudgetLedger.__init__ entry")
        self._limits = snapshot_budget_limits(limits)
        started = _read_monotonic_ns()
        self._started_ns = started
        self._last_clock_ns = started
        self._elapsed_ns = 0
        self._candidates = 0
        self._canonical_bytes = 0
        self._evaluations = 0
        self._transcript_output_bytes = 0
        self._cutoff_reason: BudgetCutoffReason | None = None
        logger.info("BudgetLedger.__init__ exit state=ready")

    def _cutoff(self, reason: BudgetCutoffReason) -> NoReturn:
        logger.debug("BudgetLedger._cutoff entry reason=%s", reason.value)
        if self._cutoff_reason is None:
            self._cutoff_reason = reason
            logger.warning("BudgetLedger state ready->cutoff reason=%s", reason.value)
        logger.error("BudgetLedger._cutoff exit=error reason=%s", self._cutoff_reason.value)
        raise BudgetLimitExceeded(self._cutoff_reason)

    def _ensure_open(self) -> None:
        logger.debug("BudgetLedger._ensure_open entry")
        if self._cutoff_reason is not None:
            logger.error("BudgetLedger._ensure_open error=%s", self._cutoff_reason.value)
            raise BudgetLimitExceeded(self._cutoff_reason)
        logger.debug("BudgetLedger._ensure_open exit")

    def _checkpoint_clock(self) -> None:
        logger.debug("BudgetLedger._checkpoint_clock entry")
        self._ensure_open()
        now = _read_monotonic_ns()
        if now < self._last_clock_ns:
            _invalid("budget-clock-regressed")
        self._last_clock_ns = now
        self._elapsed_ns = now - self._started_ns
        limit_ns = self._limits.wall_seconds * NANOSECONDS_PER_SECOND
        logger.debug("BudgetLedger clock elapsed_ns=%d limit_ns=%d", self._elapsed_ns, limit_ns)
        if self._elapsed_ns >= limit_ns:
            self._cutoff(BudgetCutoffReason.WALL_TIME)
        logger.debug("BudgetLedger._checkpoint_clock exit")

    @staticmethod
    def _exceeds(current: int, charge: int, limit: int) -> bool:
        logger.debug(
            "BudgetLedger._exceeds entry current=%d charge=%d limit=%d",
            current,
            charge,
            limit,
        )
        result = current > limit or charge > limit - current
        logger.debug("BudgetLedger._exceeds exit result=%s", result)
        return result

    def snapshot(self) -> BudgetLedgerSnapshot:
        """Return the last checked immutable state without reading the clock."""
        logger.debug("BudgetLedger.snapshot entry")
        limits = self._limits
        limits_copy = BudgetLimits(
            limits.candidate_limit, limits.canonical_bytes_limit, limits.evaluation_limit,
            limits.transcript_output_bytes_limit, limits.wall_seconds,
            limits.process_as_bytes_limit,
        )
        result = BudgetLedgerSnapshot(
            limits_copy,
            self._candidates,
            self._canonical_bytes,
            self._evaluations,
            self._transcript_output_bytes,
            self._elapsed_ns,
            self._cutoff_reason,
        )
        logger.debug("BudgetLedger.snapshot exit")
        return result

    def checkpoint(self) -> BudgetLedgerSnapshot:
        """Check the private monotonic wall clock before/after bounded work."""
        logger.debug("BudgetLedger.checkpoint entry")
        self._checkpoint_clock()
        result = self.snapshot()
        logger.debug("BudgetLedger.checkpoint exit elapsed_ns=%d", result.elapsed_ns)
        return result

    def charge_candidate(self, canonical_bytes: object) -> BudgetLedgerSnapshot:
        """Atomically precharge one candidate and its retained canonical bytes."""
        logger.debug("BudgetLedger.charge_candidate entry")
        self._ensure_open()
        byte_count = _validate_charge(canonical_bytes)
        if byte_count == 0:
            _invalid("invalid-budget-charge")
        self._checkpoint_clock()
        if self._exceeds(self._candidates, 1, self._limits.candidate_limit):
            self._cutoff(BudgetCutoffReason.CANDIDATES)
        if self._exceeds(
            self._canonical_bytes,
            byte_count,
            self._limits.canonical_bytes_limit,
        ):
            self._cutoff(BudgetCutoffReason.CANONICAL_BYTES)
        self._candidates += 1
        self._canonical_bytes += byte_count
        logger.info(
            "BudgetLedger candidate state candidates=%d canonical_bytes=%d",
            self._candidates,
            self._canonical_bytes,
        )
        result = self.snapshot()
        logger.debug("BudgetLedger.charge_candidate exit")
        return result

    def charge_evaluations(self, count: object = 1) -> BudgetLedgerSnapshot:
        """Precharge observer-case evaluations before executing them."""
        logger.debug("BudgetLedger.charge_evaluations entry")
        self._ensure_open()
        amount = _validate_charge(count)
        self._checkpoint_clock()
        if self._exceeds(self._evaluations, amount, self._limits.evaluation_limit):
            self._cutoff(BudgetCutoffReason.EVALUATIONS)
        self._evaluations += amount
        logger.info("BudgetLedger evaluation state evaluations=%d", self._evaluations)
        result = self.snapshot()
        logger.debug("BudgetLedger.charge_evaluations exit")
        return result

    def charge_output(self, byte_count: object) -> BudgetLedgerSnapshot:
        """Precharge retained transcript/stdout/stderr bytes before emission."""
        logger.debug("BudgetLedger.charge_output entry")
        self._ensure_open()
        amount = _validate_charge(byte_count)
        self._checkpoint_clock()
        if self._exceeds(
            self._transcript_output_bytes,
            amount,
            self._limits.transcript_output_bytes_limit,
        ):
            self._cutoff(BudgetCutoffReason.TRANSCRIPT_OUTPUT_BYTES)
        self._transcript_output_bytes += amount
        logger.info(
            "BudgetLedger output state transcript_output_bytes=%d",
            self._transcript_output_bytes,
        )
        result = self.snapshot()
        logger.debug("BudgetLedger.charge_output exit")
        return result
