"""Parent orchestration for five separately isolated R14.4b subjects."""
from __future__ import annotations

import logging
import os
import subprocess
import time

from .observer_synthesis_v2_baselines import build_trial_subject_manifest_v2
from .observer_synthesis_v2_budget import (
    DEFAULT_BUDGET_LIMITS,
    BudgetValidationError,
    snapshot_budget_limits,
)
from .observer_synthesis_v2_cegis_codec import limits_digest_v2
from .observer_synthesis_v2_corpus import DEFAULT_LOCKED_CORPUS
from .observer_synthesis_v2_trial_assembly import assemble_locked_trial_report_v2
from .observer_synthesis_v2_trial_validation import (
    DEFAULT_LOCKED_WINNER_V2,
    EXPECTED_CASE_DIGESTS,
    EXPECTED_CASE_IDS,
    InvalidTrialV2,
    snapshot_locked_corpus_for_trial_v2,
    snapshot_locked_winner_v2,
)
from .observer_synthesis_v2_trial_worker_codec import (
    trial_subject_request_bytes_v2,
)
from .observer_synthesis_v2_trial_worker_types import (
    ISOLATED_TRIAL_RESULT_SCHEMA,
    TRIAL_SUBJECT_REQUEST_SCHEMA,
    IsolatedObserverTrialResultV2,
    TrialSubjectWorkerRequestV2,
)
from .observer_synthesis_v2_trial_worker_validation import (
    parse_trial_subject_result_payload_v2,
    validate_trial_subject_request_v2,
)
from .observer_synthesis_v2_types import SynthesisStatus
from .observer_synthesis_v2_worker_codec import (
    FRAME_BYTES,
    MAX_WORKER_FRAME_BYTES,
    frame_bytes_v2,
)
from .observer_synthesis_v2_worker_runtime import (
    FixedWorkerKindV2,
    apply_verified_limits_v2,
    run_fixed_child_v2,
    unframe_exact_result_v2,
)

logger = logging.getLogger(__name__)

_apply_limits = apply_verified_limits_v2


def _terminal(
    status: SynthesisStatus,
    detail: str,
    limits_digest: str,
    report: object = None,
) -> IsolatedObserverTrialResultV2:
    logger.debug("_terminal entry status=%s detail=%s", status.value, detail)
    from .observer_synthesis_v2_trial_types import ObserverTrialReportV2

    trusted_report = report if type(report) is ObserverTrialReportV2 else None
    result = IsolatedObserverTrialResultV2(
        ISOLATED_TRIAL_RESULT_SCHEMA,
        status,
        detail,
        limits_digest,
        trusted_report,
        None if trusted_report is None else trusted_report.report_digest,
    )
    logger.debug("_terminal exit")
    return result


def build_trial_subject_requests_v2(
    winner: object = DEFAULT_LOCKED_WINNER_V2,
    corpus: object = DEFAULT_LOCKED_CORPUS,
    limits: object = DEFAULT_BUDGET_LIMITS,
) -> tuple[TrialSubjectWorkerRequestV2, ...]:
    """Prebuild all five exact requests before any child result exists."""
    logger.debug("build_trial_subject_requests_v2 entry")
    trusted_winner = snapshot_locked_winner_v2(winner)
    trusted_corpus = snapshot_locked_corpus_for_trial_v2(corpus)
    try:
        trusted_limits = snapshot_budget_limits(limits)
    except BudgetValidationError as exc:
        raise InvalidTrialV2("invalid-trial-limits") from exc
    manifest = build_trial_subject_manifest_v2(trusted_winner)
    digest = limits_digest_v2(trusted_limits)
    result = tuple(
        validate_trial_subject_request_v2(
            TrialSubjectWorkerRequestV2(
                TRIAL_SUBJECT_REQUEST_SCHEMA,
                index,
                subject.subject_id,
                subject.role,
                subject.digest,
                trusted_winner.digest,
                trusted_corpus.corpus_digest,
                manifest.manifest_digest,
                EXPECTED_CASE_IDS,
                EXPECTED_CASE_DIGESTS,
                trusted_limits,
                digest,
            )
        )
        for index, subject in enumerate(manifest.subjects)
    )
    logger.debug("build_trial_subject_requests_v2 exit requests=%d", len(result))
    return result


def run_isolated_locked_trials_v2(
    winner: object = DEFAULT_LOCKED_WINNER_V2,
    corpus: object = DEFAULT_LOCKED_CORPUS,
    limits: object = DEFAULT_BUDGET_LIMITS,
) -> IsolatedObserverTrialResultV2:
    """Run five fixed children and purely assemble the existing trial report."""
    logger.debug("run_isolated_locked_trials_v2 entry")
    try:
        trusted_winner = snapshot_locked_winner_v2(winner)
        trusted_corpus = snapshot_locked_corpus_for_trial_v2(corpus)
        requests = build_trial_subject_requests_v2(
            trusted_winner,
            trusted_corpus,
            limits,
        )
    except (InvalidTrialV2, TypeError, ValueError):
        return _terminal(SynthesisStatus.INVALID, "invalid-isolated-trial-request", "")
    limits_digest = requests[0].limits_digest
    subjects = []
    state_details = {
        "limit-bootstrap": "trial-worker-limit-bootstrap",
        "pipe-bootstrap": "trial-worker-pipe-bootstrap",
        "wall": "trial-worker-wall",
        "output": "trial-worker-output",
        "child": "trial-worker-child",
        "runtime": "trial-worker-runtime",
        "cancelled": "trial-worker-cancelled",
    }
    for request in requests:
        logger.debug(
            "run_isolated_locked_trials_v2 child entry index=%d",
            request.subject_index,
        )
        outcome = run_fixed_child_v2(
            FixedWorkerKindV2.TRIAL_SUBJECT,
            frame_bytes_v2(trial_subject_request_bytes_v2(request)),
            request.limits,
            popen=subprocess.Popen,
            pipe=os.pipe,
            write=os.write,
            clock=time.monotonic_ns,
            apply_limits=_apply_limits,
        )
        if outcome.state == "invalid":
            return _terminal(
                SynthesisStatus.INVALID,
                "invalid-trial-worker-result",
                limits_digest,
            )
        if outcome.state != "ok":
            return _terminal(
                SynthesisStatus.INCOMPLETE,
                state_details[outcome.state],
                limits_digest,
            )
        try:
            payload = unframe_exact_result_v2(
                outcome.framed_result,
                FRAME_BYTES,
                MAX_WORKER_FRAME_BYTES,
            )
            parsed = parse_trial_subject_result_payload_v2(payload, request)
        except (EOFError, OSError, subprocess.SubprocessError):
            return _terminal(
                SynthesisStatus.INCOMPLETE,
                "trial-worker-runtime",
                limits_digest,
            )
        except (TypeError, UnicodeError, ValueError):
            return _terminal(
                SynthesisStatus.INVALID,
                "invalid-trial-worker-result",
                limits_digest,
            )
        if parsed.status is not SynthesisStatus.FOUND or parsed.subject is None:
            return _terminal(parsed.status, parsed.detail, limits_digest)
        subjects.append(parsed.subject)
        logger.debug(
            "run_isolated_locked_trials_v2 child exit index=%d",
            request.subject_index,
        )
    try:
        manifest = build_trial_subject_manifest_v2(trusted_winner)
        report = assemble_locked_trial_report_v2(
            trusted_winner,
            trusted_corpus,
            manifest,
            tuple(subjects),
        )
    except (InvalidTrialV2, RuntimeError, TypeError, ValueError):
        return _terminal(
            SynthesisStatus.INVALID,
            "invalid-isolated-trial-assembly",
            limits_digest,
        )
    result = _terminal(
        SynthesisStatus.FOUND,
        "isolated-trial-complete",
        limits_digest,
        report,
    )
    logger.debug("run_isolated_locked_trials_v2 exit digest=%s", result.report_digest)
    return result
