"""Preflight-first construction of P1-D2 certificates and refusals."""

from __future__ import annotations

from dataclasses import replace
import logging

from .productivity_counterpressure_digest import (
    certificate_digest, evidence_digest, refusal_digest,
)
from .productivity_counterpressure_replay import replay_counterpressure
from .productivity_counterpressure_types import (
    CounterpressureCertificate, CounterpressurePolicy, CounterpressureRequest,
    CounterpressureResourceLimit, CounterpressureResult,
)
from .productivity_counterpressure_validation import (
    DEFAULT_POLICY, first_failed_bound, prepare_request, snapshot_policy,
)

logger = logging.getLogger(__name__)


def _derive_counterpressure_result(
    request: CounterpressureRequest, policy: CounterpressurePolicy,
) -> CounterpressureResult:
    """Internal nonrecursive derivation used by construction and revalidation."""
    logger.debug("_derive_counterpressure_result entry")
    prepared = prepare_request(request)
    captured_policy = snapshot_policy(policy)
    failure = first_failed_bound(prepared, captured_policy)
    if failure is not None:
        bound, required, allowed = failure
        provisional = CounterpressureResourceLimit(
            prepared.kind, prepared.digest, bound, required, allowed,
            captured_policy.policy_digest, "0" * 64,
        )
        result: CounterpressureResult = replace(
            provisional, refusal_digest=refusal_digest(provisional)
        )
        logger.debug("_derive_counterpressure_result exit refusal=%s", bound.value)
        return result
    inference, outcome, status, evidence, basis_use, basis = replay_counterpressure(
        prepared.request
    )
    evidence_commitment = evidence_digest(evidence)
    provisional_certificate = CounterpressureCertificate(
        prepared.kind, prepared.digest, inference, outcome, status, evidence,
        evidence_commitment, basis_use, basis, captured_policy.policy_digest, "0" * 64,
    )
    result = replace(
        provisional_certificate,
        certificate_digest=certificate_digest(provisional_certificate),
    )
    logger.debug("_derive_counterpressure_result exit certificate=%s", inference.value)
    return result


def counterpressure_result(
    request: CounterpressureRequest, policy: CounterpressurePolicy = DEFAULT_POLICY,
) -> CounterpressureResult:
    """Construct then internally revalidate a fresh closed D2 result."""
    logger.debug("counterpressure_result entry")
    candidate = _derive_counterpressure_result(request, policy)
    from .productivity_counterpressure_result_validation import (
        validate_counterpressure_result,
    )
    result = validate_counterpressure_result(candidate, request, policy)
    logger.debug("counterpressure_result exit type=%s", type(result).__name__)
    return result
