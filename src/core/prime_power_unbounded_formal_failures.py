"""Exact execution-bound operational failure arms for P3-N6."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .prime_power_unbounded_common import exact_digest, reject
from .prime_power_unbounded_result_digests import formal_attempt_digest
from .prime_power_unbounded_sources import policy, theorem_source
from .prime_power_unbounded_types import (
    N6DiagnosticCode, N6FormalFailureKind, N6Lane,
)

logger = logging.getLogger(__name__)
_FAILURE_CODES = {
    N6FormalFailureKind.TIMEOUT: N6DiagnosticCode.TIMEOUT,
    N6FormalFailureKind.OUTPUT_LIMIT: N6DiagnosticCode.OUTPUT_LIMIT,
    N6FormalFailureKind.COMPILE_ERROR: N6DiagnosticCode.COMPILE_ERROR,
    N6FormalFailureKind.CONTINUITY_DRIFT: N6DiagnosticCode.CONTINUITY_DRIFT,
    N6FormalFailureKind.DEPENDENCY_REPLAY_FAILURE:
        N6DiagnosticCode.DEPENDENCY_REPLAY_FAILURE,
}


@dataclass(frozen=True, slots=True)
class N6SanitizedDiagnosticV1:
    code: N6DiagnosticCode
    detail_digest: str

    def __post_init__(self) -> None:
        logger.debug("N6SanitizedDiagnosticV1 post_init entry")
        if type(self.code) is not N6DiagnosticCode:
            reject("n6-diagnostic-code-exact-enum-required")
        exact_digest(self.detail_digest, "n6-diagnostic-detail")
        logger.debug("N6SanitizedDiagnosticV1 post_init exit")


@dataclass(frozen=True, slots=True)
class _N6FormalFailureBaseV1:
    kind: N6FormalFailureKind
    request_digest: str
    source_digest: str
    toolchain_id: str
    policy_digest: str
    output_digest: str
    attempt_digest: str
    diagnostic: N6SanitizedDiagnosticV1

    def __post_init__(self) -> None:
        logger.debug("_N6FormalFailureBaseV1 post_init entry")
        lane = {
            N6EFormalFailureV1: N6Lane.E_POWER_INJECTION,
            N6WFormalFailureV1: N6Lane.W_INFORMATION_GROWTH,
        }.get(type(self))
        if lane is None:
            reject("n6-formal-failure-exact-lane-arm-required")
        self._validate(lane)
        logger.debug("_N6FormalFailureBaseV1 post_init exit")

    def _validate(self, lane: N6Lane) -> None:
        logger.debug("_N6FormalFailureBaseV1 validate entry lane=%s", lane.value)
        if (type(self.kind) is not N6FormalFailureKind
                or type(self.diagnostic) is not N6SanitizedDiagnosticV1
                or _FAILURE_CODES[self.kind] is not self.diagnostic.code):
            reject("n6-formal-failure-code-invalid")
        for label, value in (
            ("request", self.request_digest), ("source", self.source_digest),
            ("policy", self.policy_digest), ("output", self.output_digest),
            ("attempt", self.attempt_digest),
        ):
            exact_digest(value, f"n6-formal-{label}")
        if (self.toolchain_id != "leanprover/lean4:v4.30.0-rc2"
                or self.source_digest != theorem_source(lane).source_digest
                or self.policy_digest != policy().policy_digest):
            reject("n6-formal-execution-identity-invalid")
        expected = formal_attempt_digest(
            lane, self.kind, self.request_digest, self.source_digest,
            self.toolchain_id, self.policy_digest, self.output_digest,
            self.diagnostic.code.value, self.diagnostic.detail_digest,
        )
        if self.attempt_digest != expected:
            reject("n6-formal-attempt-digest-drift")
        logger.debug("_N6FormalFailureBaseV1 validate exit")


@dataclass(frozen=True, slots=True)
class N6EFormalFailureV1(_N6FormalFailureBaseV1):
    pass


@dataclass(frozen=True, slots=True)
class N6WFormalFailureV1(_N6FormalFailureBaseV1):
    pass
