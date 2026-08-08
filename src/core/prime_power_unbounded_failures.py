"""Lane-closed, digest-bound supported nonpositive P3-N6 results."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import TypeAlias

from .prime_power_unbounded_common import exact_digest, reject
from .prime_power_unbounded_formal_failures import (
    N6SanitizedDiagnosticV1 as _N6SanitizedDiagnosticV1,
    N6EFormalFailureV1,
    N6WFormalFailureV1,
)
from .prime_power_unbounded_results import PowerInjectionJudgmentV1
from .prime_power_unbounded_result_digests import open_result_digest
from .prime_power_unbounded_types import (
    N6EOpenReason,
    N6GoalID,
    N6Lane,
    N6Status,
    N6WOpenReason,
)

logger = logging.getLogger(__name__)
N6SanitizedDiagnosticV1 = _N6SanitizedDiagnosticV1


def _digests(*rows: tuple[str, object]) -> None:
    """Validate exact result digests without coercion."""
    logger.debug("_digests entry fields=%d", len(rows))
    for label, value in rows:
        exact_digest(value, f"n6-result-{label}")
    logger.debug("_digests exit")


@dataclass(frozen=True, slots=True)
class N6EOpenV1:
    """Legacy untrusted E-OPEN syntax; not an admitted N6EResultV1 arm."""

    status: N6Status
    reason: N6EOpenReason
    missing_goal_id: N6GoalID
    request_digest: str
    open_digest: str

    def __post_init__(self) -> None:
        logger.debug("N6EOpenV1 post_init entry")
        if (
            self.status is not N6Status.OPEN
            or type(self.reason) is not N6EOpenReason
            or self.missing_goal_id is not N6GoalID.EXACT_EQUALITY_ADAPTER
        ):
            reject("n6-e-open-lane-or-goal-invalid")
        _digests(("e-open-request", self.request_digest), ("e-open", self.open_digest))
        expected = open_result_digest(
            N6Lane.E_POWER_INJECTION,
            self.reason.value,
            self.missing_goal_id,
            self.request_digest,
        )
        if self.open_digest != expected:
            reject("n6-e-open-digest-drift")
        logger.debug("N6EOpenV1 post_init exit")


@dataclass(frozen=True, slots=True)
class N6WOpenV1:
    """The W outcome for an explicit missing completed-infinity input."""

    status: N6Status
    reason: N6WOpenReason
    missing_goal_id: N6GoalID
    request_digest: str
    open_digest: str

    def __post_init__(self) -> None:
        logger.debug("N6WOpenV1 post_init entry")
        if (
            self.status is not N6Status.OPEN
            or type(self.reason) is not N6WOpenReason
            or self.missing_goal_id is not N6GoalID.COMPLETED_INFINITY_ADMISSION
        ):
            reject("n6-w-open-lane-or-goal-invalid")
        _digests(("w-open-request", self.request_digest), ("w-open", self.open_digest))
        expected = open_result_digest(
            N6Lane.W_INFORMATION_GROWTH,
            self.reason.value,
            self.missing_goal_id,
            self.request_digest,
        )
        if self.open_digest != expected:
            reject("n6-w-open-digest-drift")
        logger.debug("N6WOpenV1 post_init exit")


N6EResultV1: TypeAlias = (
    PowerInjectionJudgmentV1 | N6EFormalFailureV1
)
N6WResultV1: TypeAlias = N6WOpenV1 | N6WFormalFailureV1
