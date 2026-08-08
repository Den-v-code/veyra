"""Context-bound fresh reconstruction for supported P3-N6 result arms."""

from __future__ import annotations

import logging
from typing import cast

from .prime_power_unbounded_common import (
    FrozenLayoutV1,
    exact_shape,
    freeze_layout,
    reject,
)
from .prime_power_unbounded_failures import (
    N6EOpenV1,
    N6EResultV1,
    N6WOpenV1,
    N6WResultV1,
)
from .prime_power_unbounded_formal_failures import (
    N6SanitizedDiagnosticV1,
    N6EFormalFailureV1,
    N6WFormalFailureV1,
)
from .prime_power_unbounded_results import (
    _ADAPTER_RAW_LAYOUT,
    _EVIDENCE_RAW_LAYOUT,
    _JUDGMENT_RAW_LAYOUT,
    PPEqualityAdapterV1,
    PowerInjectionEvidenceV1,
    PowerInjectionJudgmentV1,
    _validate_adapter,
    _validate_evidence,
    _validate_judgment,
)
from .prime_power_unbounded_requests import snapshot_e_request, snapshot_w_request
from .prime_power_unbounded_types import (
    N6DiagnosticCode,
    N6EOpenReason,
    N6ERequestV1,
    N6FormalFailureKind,
    N6GoalID,
    N6Status,
    N6WOpenReason,
    N6WRequestV1,
)

logger = logging.getLogger(__name__)
_E_OPEN = freeze_layout(N6EOpenV1, (
    "status", "reason", "missing_goal_id", "request_digest", "open_digest",
))
_W_OPEN = freeze_layout(N6WOpenV1, (
    "status", "reason", "missing_goal_id", "request_digest", "open_digest",
))
_DIAGNOSTIC = freeze_layout(N6SanitizedDiagnosticV1, ("code", "detail_digest"))
_W_FORMAL = freeze_layout(N6WFormalFailureV1, (
    "kind", "request_digest", "source_digest", "toolchain_id", "policy_digest",
    "output_digest", "attempt_digest", "diagnostic",
))
_E_FORMAL = freeze_layout(N6EFormalFailureV1, (
    "kind", "request_digest", "source_digest", "toolchain_id", "policy_digest",
    "output_digest", "attempt_digest", "diagnostic",
))
_E_POSITIVE = freeze_layout(
    PowerInjectionJudgmentV1, ("status", "raw", "evidence"),
)
_E_EVIDENCE = freeze_layout(PowerInjectionEvidenceV1, ("raw", "adapter"))
_E_ADAPTER = freeze_layout(PPEqualityAdapterV1, ("raw",))


def _layout_values(
    value: object, layout: FrozenLayoutV1, label: str,
) -> tuple[object, ...]:
    """Read one already-validated exact layout without invoking class equality."""
    logger.debug("_layout_values entry label=%s", label)
    fields = exact_shape(value, layout, label)
    result = tuple(fields[name] for name, _ in layout.fields)
    logger.debug("_layout_values exit label=%s fields=%d", label, len(result))
    return result


def _positive_transcript(value: PowerInjectionJudgmentV1) -> tuple[object, ...]:
    """Expose every primitive positive field for structural replay comparison."""
    logger.debug("_positive_transcript entry")
    outer = exact_shape(value, _E_POSITIVE, "n6-e-replay-positive")
    owned_evidence = exact_shape(outer["evidence"], _E_EVIDENCE, "n6-e-replay-evidence")
    owned_adapter = exact_shape(
        owned_evidence["adapter"], _E_ADAPTER, "n6-e-replay-adapter",
    )
    judgment = _layout_values(outer["raw"], _JUDGMENT_RAW_LAYOUT, "n6-e-replay-judgment")
    evidence = _layout_values(
        owned_evidence["raw"], _EVIDENCE_RAW_LAYOUT, "n6-e-replay-evidence-raw",
    )
    adapter = _layout_values(
        owned_adapter["raw"], _ADAPTER_RAW_LAYOUT, "n6-e-replay-adapter-raw",
    )
    result = (outer["status"], judgment[:2] + judgment[3:], evidence, adapter)
    logger.debug("_positive_transcript exit")
    return result


def _formal_transcript(value: N6EFormalFailureV1) -> tuple[object, ...]:
    """Expose every formal-failure and nested diagnostic field for replay."""
    logger.debug("_formal_transcript entry")
    raw = exact_shape(value, _E_FORMAL, "n6-e-replay-formal")
    diagnostic = _layout_values(raw["diagnostic"], _DIAGNOSTIC, "n6-e-replay-diagnostic")
    result = tuple(raw[name] for name, _ in _E_FORMAL.fields[:-1]) + (diagnostic,)
    logger.debug("_formal_transcript exit")
    return result


def _reconstruct_e_open(value: object) -> N6EOpenV1:
    logger.debug("_reconstruct_e_open entry")
    raw = exact_shape(value, _E_OPEN, "n6-e-open-result")
    result = N6EOpenV1(
        cast(N6Status, raw["status"]),
        cast(N6EOpenReason, raw["reason"]),
        cast(N6GoalID, raw["missing_goal_id"]),
        cast(str, raw["request_digest"]), cast(str, raw["open_digest"]),
    )
    logger.debug("_reconstruct_e_open exit")
    return result


def _reconstruct_w_open(value: object) -> N6WOpenV1:
    logger.debug("_reconstruct_w_open entry")
    raw = exact_shape(value, _W_OPEN, "n6-w-open-result")
    result = N6WOpenV1(
        cast(N6Status, raw["status"]),
        cast(N6WOpenReason, raw["reason"]),
        cast(N6GoalID, raw["missing_goal_id"]),
        cast(str, raw["request_digest"]), cast(str, raw["open_digest"]),
    )
    logger.debug("_reconstruct_w_open exit")
    return result


def _reconstruct_formal(
    value: object, layout: FrozenLayoutV1,
) -> N6EFormalFailureV1 | N6WFormalFailureV1:
    logger.debug("_reconstruct_formal entry")
    raw = exact_shape(value, layout, "n6-formal-result")
    diagnostic_raw = exact_shape(raw["diagnostic"], _DIAGNOSTIC, "n6-formal-diagnostic")
    diagnostic = N6SanitizedDiagnosticV1(
        cast(N6DiagnosticCode, diagnostic_raw["code"]),
        cast(str, diagnostic_raw["detail_digest"]),
    )
    arguments = (
        cast(N6FormalFailureKind, raw["kind"]),
        cast(str, raw["request_digest"]),
        cast(str, raw["source_digest"]),
        cast(str, raw["toolchain_id"]),
        cast(str, raw["policy_digest"]),
        cast(str, raw["output_digest"]),
        cast(str, raw["attempt_digest"]),
        diagnostic,
    )
    result = (
        N6EFormalFailureV1(*arguments)
        if type(value) is N6EFormalFailureV1
        else N6WFormalFailureV1(*arguments)
    )
    logger.debug("_reconstruct_formal exit kind=%s", result.kind.value)
    return result


def _validate_e_positive(value: object) -> PowerInjectionJudgmentV1:
    """Validate owned shape and all nested raw transcript bindings."""
    logger.debug("_validate_e_positive entry")
    if type(value) is not PowerInjectionJudgmentV1:
        reject("n6-e-positive-exact-type-required")
    outer = exact_shape(value, _E_POSITIVE, "n6-e-positive")
    if outer["status"] is not N6Status.ESTABLISHED:
        reject("n6-e-positive-status-invalid")
    evidence_fields = exact_shape(outer["evidence"], _E_EVIDENCE, "n6-e-evidence")
    adapter_fields = exact_shape(evidence_fields["adapter"], _E_ADAPTER, "n6-e-adapter")
    adapter = _validate_adapter(adapter_fields["raw"])
    evidence = _validate_evidence(evidence_fields["raw"])
    judgment = _validate_judgment(outer["raw"], evidence)
    if (judgment.evidence is not evidence
            or evidence.equality_adapter_digest != adapter.adapter_digest
            or evidence.pomega2_package_digest != adapter.pomega2_package_digest
            or evidence.doctrine_digest != adapter.doctrine_digest
            or evidence.carrier_id != adapter.carrier_id
            or evidence.equality_id != adapter.equality_id
            or evidence.theorem_source_digest != adapter.theorem_source_digest):
        reject("n6-e-positive-nested-binding-invalid")
    logger.debug("_validate_e_positive exit")
    return value


def _bind_context(
    result: N6EResultV1 | N6WResultV1,
    request: N6ERequestV1 | N6WRequestV1,
) -> None:
    logger.debug("_bind_context entry")
    if type(result) is PowerInjectionJudgmentV1:
        raw_positive = exact_shape(result, _E_POSITIVE, "n6-positive-context")
        raw_judgment = _validate_judgment(
            raw_positive["raw"],
            result.evidence.raw,
        )
        if raw_judgment.request_digest != request.request_digest:
            reject("n6-result-request-context-mismatch")
        logger.debug("_bind_context exit lane=e-positive")
        return
    raw_result = exact_shape(
        result,
        _W_OPEN if type(result) is N6WOpenV1 else
        _E_FORMAL if type(result) is N6EFormalFailureV1 else _W_FORMAL,
        "n6-result-context",
    )
    if raw_result["request_digest"] != request.request_digest:
        reject("n6-result-request-context-mismatch")
    if "source_digest" in raw_result and (
        raw_result["source_digest"] != request.theorem.source_digest
        or raw_result["policy_digest"] != request.policy.policy_digest
    ):
        reject("n6-result-execution-context-mismatch")
    logger.debug("_bind_context exit lane=nonpositive")


def validate_e_result(
    value: N6EResultV1, expected_request: N6ERequestV1
) -> N6EResultV1:
    """Replay supported E arm and bind it to one freshly replayed request."""
    logger.debug("validate_e_result entry")
    request = snapshot_e_request(expected_request)
    result: N6EResultV1
    if type(value) is PowerInjectionJudgmentV1:
        result = _validate_e_positive(value)
    elif type(value) is N6EFormalFailureV1:
        result = cast(N6EFormalFailureV1, _reconstruct_formal(value, _E_FORMAL))
    else:
        reject("n6-e-result-supported-arm-required")
    _bind_context(result, request)
    from .prime_power_unbounded_requests import e_result

    expected = e_result(request)
    if type(result) is not type(expected):
        reject("n6-e-result-replay-variant-mismatch")
    if type(result) is PowerInjectionJudgmentV1:
        expected = cast(PowerInjectionJudgmentV1, expected)
        if _positive_transcript(result) != _positive_transcript(expected):
            reject("n6-e-result-positive-replay-mismatch")
    else:
        formal_result = cast(N6EFormalFailureV1, result)
        formal_expected = cast(N6EFormalFailureV1, expected)
        if _formal_transcript(formal_result) != _formal_transcript(formal_expected):
            reject("n6-e-result-formal-replay-mismatch")
    logger.debug("validate_e_result exit")
    return result


def validate_w_result(
    value: N6WResultV1, expected_request: N6WRequestV1
) -> N6WResultV1:
    """Replay supported W arm and bind it to one freshly replayed request."""
    logger.debug("validate_w_result entry")
    request = snapshot_w_request(expected_request)
    result: N6WResultV1
    if request.completed_infinity is None and type(value) is N6WOpenV1:
        result = _reconstruct_w_open(value)
    elif (
        request.completed_infinity is not None
        and type(value) is N6WFormalFailureV1
    ):
        result = cast(N6WFormalFailureV1, _reconstruct_formal(value, _W_FORMAL))
    else:
        reject("n6-w-result-request-alternative-arm-mismatch")
    if (
        type(result) is N6WFormalFailureV1
        and result.kind is not N6FormalFailureKind.DEPENDENCY_REPLAY_FAILURE
    ):
        reject("n6-w-result-formal-kind-mismatch")
    _bind_context(result, request)
    logger.debug("validate_w_result exit")
    return result
