"""In-process finite R14.5 receipts over exact R11 and R12 replay."""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import logging

from .intrinsic_vam_lowering import lower_r11_echo, raise_r11_echo
from .intrinsic_vam_receipts import (
    digest_transport_data,
    intrinsic_transport_envelope_data,
)
from .observer_core_codec import canonical_observer_bytes
from .observer_core_support import outcome_data
from .observer_core_types import (
    Apply,
    DomainBlocked,
    Echo,
    Input,
    Mismatch,
    PrimitiveId,
)
from .observer_synthesis_v2_grammar import EXPECTED_DEFAULT_CATALOG_DIGEST
from .observer_synthesis_v2_protocol import ExpectedRelation, OUTCOME_SCHEMA
from .observer_synthesis_v2_receipt_codec import (
    BOUNDARY,
    RECEIPT_SCHEMA,
    ROW_SCHEMA,
    _bundle_body_data_v2,
    _row_body_data_v2,
)
from .observer_synthesis_v2_receipt_pins import (
    EXPECTED_BINDING_DIGESTS,
    EXPECTED_CASE_IDS,
    EXPECTED_ENVELOPE_DIGESTS,
    EXPECTED_IR_DIGESTS,
    EXPECTED_OUTCOME_DIGESTS,
    EXPECTED_PAYLOAD_DIGESTS,
    EXPECTED_RECEIPT_BUNDLE_DIGEST,
    EXPECTED_SOURCE_DIGESTS,
)
from .observer_synthesis_v2_receipt_types import (
    ObserverSynthesisReceiptBundleV2,
    ObserverSynthesisReceiptRowV2,
)
from .observer_synthesis_v2_trial import (
    EXPECTED_GUARANTEE_DIGEST,
    EXPECTED_TRIAL_REPORT_DIGEST,
    run_locked_trials_v2,
)
from .observer_synthesis_v2_trial_types import (
    TrialCaseResultV2,
    TrialSubjectRoleV2,
)
from .observer_synthesis_v2_trial_provenance import require_trial_report_brand_v2
from .observer_synthesis_v2_trial_validation import (
    DEFAULT_LOCKED_WINNER_V2,
    snapshot_locked_corpus_for_trial_v2,
    snapshot_locked_winner_v2,
)
from .observer_synthesis_v2_corpus import DEFAULT_LOCKED_CORPUS, ObserverCaseV2
from .proof_core_codec import canonical_json, digest_data
from .shadow_effect_types import BridgeCapability, EvidenceClass, EvidenceScope

logger = logging.getLogger(__name__)


def _actual_relation_v2(outcome: object) -> ExpectedRelation:
    """Map only the three exact R11 echo outcomes into the R14 vocabulary."""
    logger.debug("_actual_relation_v2 entry type=%s", type(outcome).__name__)
    if type(outcome) is Echo:
        result = ExpectedRelation.ECHO
    elif type(outcome) is Mismatch:
        result = ExpectedRelation.SEPARATE
    elif type(outcome) is DomainBlocked:
        result = ExpectedRelation.DOMAIN_BLOCKED
    else:
        logger.error("_actual_relation_v2 invalid type=%s", type(outcome).__name__)
        raise RuntimeError("r14.5-invalid-raised-outcome")
    logger.debug("_actual_relation_v2 exit actual=%s", result.value)
    return result


def _replayed_outcome_digest_v2(outcome: object) -> str:
    """Independently reconstruct the exact R14.3a outcome-domain digest."""
    logger.debug("_replayed_outcome_digest_v2 entry")
    canonical = canonical_json(
        {"outcome": outcome_data(outcome), "schema": OUTCOME_SCHEMA}
    ).encode("utf-8")
    result = sha256(OUTCOME_SCHEMA.encode("ascii") + b"\0" + canonical).hexdigest()
    logger.debug("_replayed_outcome_digest_v2 exit digest=%s", result[:12])
    return result


def _check_trial_case_v2(
    case: ObserverCaseV2,
    trial_row: TrialCaseResultV2,
    actual: ExpectedRelation,
    outcome_digest: str,
) -> None:
    """Require the independent R12 replay to equal the retained R14 trial row."""
    logger.debug("_check_trial_case_v2 entry case_id=%d", case.case_id)
    if (
        type(trial_row) is not TrialCaseResultV2
        or trial_row.case_id != case.case_id
        or trial_row.case_digest != case.case_digest
        or trial_row.split is not case.split
        or trial_row.expected is not case.expected
        or trial_row.required_for_winner is not case.required_for_winner
        or trial_row.actual is not actual
        or trial_row.matched is not (actual is case.expected)
        or trial_row.outcome_digest != outcome_digest
    ):
        logger.error("_check_trial_case_v2 drift case_id=%d", case.case_id)
        raise RuntimeError("r14.5-trial-replay-drift")
    logger.debug("_check_trial_case_v2 exit")


def _build_receipt_row_v2(
    ordinal: int,
    observer: Apply,
    case: ObserverCaseV2,
    trial_row: TrialCaseResultV2,
) -> ObserverSynthesisReceiptRowV2:
    """Lower, envelope, raise, and self-bind one exact default-corpus row."""
    logger.debug("_build_receipt_row_v2 entry ordinal=%d case_id=%d", ordinal, case.case_id)
    transport = lower_r11_echo(observer, case.left, case.right)
    envelope = intrinsic_transport_envelope_data(transport)
    raised = raise_r11_echo(observer, case.left, case.right, transport)
    actual = _actual_relation_v2(raised)
    outcome_digest = _replayed_outcome_digest_v2(raised)
    _check_trial_case_v2(case, trial_row, actual, outcome_digest)
    receipt = transport.receipt
    provisional = ObserverSynthesisReceiptRowV2(
        ordinal,
        case.case_id,
        case.group_id,
        case.case_digest,
        case.payload_digest,
        case.clone_digest,
        case.split,
        case.expected,
        case.required_for_winner,
        actual,
        actual is case.expected,
        outcome_digest,
        (receipt.source_digests[0], receipt.source_digests[1]),
        receipt.observer_digest,
        receipt.response_kind_digest,
        receipt.payload_digest,
        receipt.ir_digest,
        receipt.binding_digest,
        digest_transport_data(envelope),
        transport,
        "",
    )
    result = replace(
        provisional,
        row_digest=digest_data(
            _row_body_data_v2(provisional),
            f"{ROW_SCHEMA}.binding",
        ),
    )
    logger.debug("_build_receipt_row_v2 exit digest=%s", result.row_digest[:12])
    return result


def _verify_literal_vectors_v2(
    rows: tuple[ObserverSynthesisReceiptRowV2, ...],
) -> None:
    """Fail closed unless every reviewed ten-case digest vector is unchanged."""
    logger.debug("_verify_literal_vectors_v2 entry rows=%d", len(rows))
    actual = (
        tuple(row.case_id for row in rows),
        tuple(row.source_digests for row in rows),
        tuple(row.r12_binding_digest for row in rows),
        tuple(row.r12_payload_digest for row in rows),
        tuple(row.ir_digest for row in rows),
        tuple(row.envelope_digest for row in rows),
        tuple(row.outcome_digest for row in rows),
    )
    expected = (
        EXPECTED_CASE_IDS,
        EXPECTED_SOURCE_DIGESTS,
        EXPECTED_BINDING_DIGESTS,
        EXPECTED_PAYLOAD_DIGESTS,
        EXPECTED_IR_DIGESTS,
        EXPECTED_ENVELOPE_DIGESTS,
        EXPECTED_OUTCOME_DIGESTS,
    )
    if actual != expected:
        logger.error("_verify_literal_vectors_v2 digest vector drift")
        raise RuntimeError("r14.5-receipt-vector-drift")
    logger.debug("_verify_literal_vectors_v2 exit")


def build_receipts_from_validated_trial_v2(
    trial: object,
) -> ObserverSynthesisReceiptBundleV2:
    """Build ten receipts from one already validated exact trial report."""
    logger.debug("build_receipts_from_validated_trial_v2 entry")
    try:
        trial = require_trial_report_brand_v2(trial)
    except ValueError as exc:
        logger.error("build_receipts_from_validated_trial_v2 unbranded trial")
        raise RuntimeError("r14.5-invalid-validated-trial") from exc
    winner = snapshot_locked_winner_v2(DEFAULT_LOCKED_WINNER_V2)
    corpus = snapshot_locked_corpus_for_trial_v2(DEFAULT_LOCKED_CORPUS)
    observer = Apply(PrimitiveId.CREST, Input())
    if (
        canonical_observer_bytes(observer) != winner.canonical
        or sha256(winner.canonical).hexdigest() != winner.digest
    ):
        logger.error("build_receipts_from_validated_trial_v2 winner AST drift")
        raise RuntimeError("r14.5-winner-ast-drift")
    try:
        subject = trial.subjects[0]
        false_claims = (
            trial.guarantee.general_completeness,
            trial.guarantee.general_minimality,
            trial.guarantee.novelty,
            trial.guarantee.superiority,
            trial.guarantee.evidence_accepted,
            trial.guarantee.promotion_ready,
            trial.guarantee.taxonomy_changed,
            trial.guarantee.proof_complete,
        )
    except (AttributeError, IndexError) as exc:
        logger.error("build_receipts_from_validated_trial_v2 malformed trial")
        raise RuntimeError("r14.5-invalid-validated-trial") from exc
    if (
        trial.report_digest != EXPECTED_TRIAL_REPORT_DIGEST
        or trial.guarantee.guarantee_digest != EXPECTED_GUARANTEE_DIGEST
        or trial.winner_digest != winner.digest
        or subject.role is not TrialSubjectRoleV2.SYNTHESIZED
        or subject.observer_digest != winner.digest
        or len(subject.cases) != len(corpus.cases)
        or any(flag is not False for flag in false_claims)
    ):
        logger.error("build_receipts_from_validated_trial_v2 trial drift")
        raise RuntimeError("r14.5-trial-binding-drift")
    rows = tuple(
        _build_receipt_row_v2(ordinal, observer, case, trial_row)
        for ordinal, (case, trial_row) in enumerate(
            zip(corpus.cases, subject.cases, strict=True)
        )
    )
    _verify_literal_vectors_v2(rows)
    provisional = ObserverSynthesisReceiptBundleV2(
        RECEIPT_SCHEMA,
        EXPECTED_DEFAULT_CATALOG_DIGEST,
        winner.ordinal,
        winner.cost,
        winner.depth,
        winner.canonical,
        winner.digest,
        corpus.corpus_digest,
        trial.report_digest,
        trial.manifest_digest,
        trial.guarantee.guarantee_digest,
        subject.retained_digest,
        (BridgeCapability.PRESERVES,),
        EvidenceClass.EXECUTABLE_WITNESS,
        EvidenceScope.FINITE,
        (2, 4, 25, 5),
        rows,
        False, False, False, False, False, False, False, False,
        BOUNDARY,
        "",
    )
    result = replace(
        provisional,
        bundle_digest=digest_data(
            _bundle_body_data_v2(provisional),
            f"{RECEIPT_SCHEMA}.binding",
        ),
    )
    if result.bundle_digest != EXPECTED_RECEIPT_BUNDLE_DIGEST:
        logger.error(
            "build_receipts_from_validated_trial_v2 bundle drift actual=%s",
            result.bundle_digest,
        )
        raise RuntimeError(f"r14.5-receipt-bundle-drift:{result.bundle_digest}")
    logger.debug(
        "build_receipts_from_validated_trial_v2 exit digest=%s",
        result.bundle_digest[:12],
    )
    return result


def build_observer_synthesis_receipts_v2() -> ObserverSynthesisReceiptBundleV2:
    """Preserve the reviewed in-process API while delegating pure receipt work."""
    logger.debug("build_observer_synthesis_receipts_v2 entry")
    trial = run_locked_trials_v2()
    result = build_receipts_from_validated_trial_v2(trial)
    logger.debug(
        "build_observer_synthesis_receipts_v2 exit digest=%s",
        result.bundle_digest[:12],
    )
    return result
