"""Exact canonical trial snapshot used by the isolated R14.5 receipt child."""
from __future__ import annotations

from hashlib import sha256
import logging

from .observer_synthesis_v2_baselines import build_trial_subject_manifest_v2
from .observer_synthesis_v2_corpus import DEFAULT_LOCKED_CORPUS
from .observer_synthesis_v2_trial import (
    EXPECTED_GUARANTEE_DIGEST,
    EXPECTED_TRIAL_REPORT_DIGEST,
)
from .observer_synthesis_v2_trial_assembly import assemble_locked_trial_report_v2
from .observer_synthesis_v2_trial_codec import guarantee_data_v2
from .observer_synthesis_v2_trial_types import ObserverTrialReportV2
from .observer_synthesis_v2_trial_validation import (
    DEFAULT_LOCKED_WINNER_V2,
    EXPECTED_CORPUS_DIGEST,
    EXPECTED_WINNER_DIGEST,
    snapshot_locked_corpus_for_trial_v2,
    snapshot_locked_winner_v2,
)
from .observer_synthesis_v2_trial_worker import build_trial_subject_requests_v2
from .observer_synthesis_v2_trial_worker_codec import full_subject_data_v2
from .observer_synthesis_v2_trial_worker_subject_validation import (
    validate_complete_trial_subject_data_v2,
)
from .proof_core_codec import canonical_json, load_canonical

logger = logging.getLogger(__name__)

TRIAL_PAYLOAD_BYTES = 19_980
TRIAL_PAYLOAD_SHA256 = (
    "0ab3ffadfb493641915c970728bb08db294d29cb398c26ee9678d82ce80438fb"
)


def _trial_report_data_v2(report: ObserverTrialReportV2) -> dict[str, object]:
    """Serialize the full report, including all fifty retained case rows."""
    logger.debug("_trial_report_data_v2 entry")
    result: dict[str, object] = {
        "boundary": report.boundary,
        "corpus_digest": report.corpus_digest,
        "guarantee": {
            **guarantee_data_v2(report.guarantee),
            "guarantee_digest": report.guarantee.guarantee_digest,
        },
        "manifest_digest": report.manifest_digest,
        "report_digest": report.report_digest,
        "schema": report.schema,
        "subjects": [full_subject_data_v2(row) for row in report.subjects],
        "winner_digest": report.winner_digest,
    }
    logger.debug("_trial_report_data_v2 exit")
    return result


def trial_report_payload_v2(report: object) -> bytes:
    """Return only the exact reviewed full canonical report snapshot."""
    logger.debug("trial_report_payload_v2 entry type=%s", type(report).__name__)
    if type(report) is not ObserverTrialReportV2:
        raise ValueError("invalid-receipt-trial-type")
    try:
        payload = canonical_json(_trial_report_data_v2(report)).encode()
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("invalid-receipt-trial-shape") from exc
    if (
        len(payload) != TRIAL_PAYLOAD_BYTES
        or sha256(payload).hexdigest() != TRIAL_PAYLOAD_SHA256
    ):
        raise ValueError("invalid-receipt-trial-payload")
    logger.debug("trial_report_payload_v2 exit bytes=%d", len(payload))
    return payload


def trial_report_from_payload_v2(payload: object) -> ObserverTrialReportV2:
    """Rebuild trusted DTOs without executing observer or receipt semantics."""
    logger.debug(
        "trial_report_from_payload_v2 entry type=%s",
        type(payload).__name__,
    )
    if (
        type(payload) is not bytes
        or len(payload) != TRIAL_PAYLOAD_BYTES
        or sha256(payload).hexdigest() != TRIAL_PAYLOAD_SHA256
    ):
        raise ValueError("invalid-receipt-trial-payload")
    try:
        data = load_canonical(payload.decode())
        canonical = canonical_json(data).encode()
    except (RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("invalid-receipt-trial-canonical") from exc
    keys = {
        "boundary", "corpus_digest", "guarantee", "manifest_digest",
        "report_digest", "schema", "subjects", "winner_digest",
    }
    if (
        type(data) is not dict
        or set(data) != keys
        or canonical != payload
        or type(data["subjects"]) is not list
        or len(data["subjects"]) != 5
        or type(data["guarantee"]) is not dict
    ):
        raise ValueError("invalid-receipt-trial-shape")
    winner = snapshot_locked_winner_v2(DEFAULT_LOCKED_WINNER_V2)
    corpus = snapshot_locked_corpus_for_trial_v2(DEFAULT_LOCKED_CORPUS)
    manifest = build_trial_subject_manifest_v2(winner)
    roots = (
        data["winner_digest"],
        data["corpus_digest"],
        data["manifest_digest"],
        data["report_digest"],
        data["guarantee"].get("guarantee_digest"),
    )
    if roots != (
        EXPECTED_WINNER_DIGEST,
        EXPECTED_CORPUS_DIGEST,
        manifest.manifest_digest,
        EXPECTED_TRIAL_REPORT_DIGEST,
        EXPECTED_GUARANTEE_DIGEST,
    ):
        raise ValueError("invalid-receipt-trial-roots")
    requests = build_trial_subject_requests_v2()
    subjects = tuple(
        validate_complete_trial_subject_data_v2(row, request)
        for row, request in zip(data["subjects"], requests, strict=True)
    )
    report = assemble_locked_trial_report_v2(winner, corpus, manifest, subjects)
    expected_guarantee = {
        **guarantee_data_v2(report.guarantee),
        "guarantee_digest": report.guarantee.guarantee_digest,
    }
    if (
        data["guarantee"] != expected_guarantee
        or data != _trial_report_data_v2(report)
    ):
        raise ValueError("invalid-receipt-trial-binding")
    logger.debug("trial_report_from_payload_v2 exit digest=%s", report.report_digest[:12])
    return report


def snapshot_receipt_trial_v2(report: object) -> ObserverTrialReportV2:
    """Deep snapshot one exact already-validated report."""
    logger.debug("snapshot_receipt_trial_v2 entry")
    result = trial_report_from_payload_v2(trial_report_payload_v2(report))
    logger.debug("snapshot_receipt_trial_v2 exit")
    return result
