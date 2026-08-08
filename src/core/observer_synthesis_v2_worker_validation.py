"""Exact request and independently replayed result gates for R14.2b."""
from __future__ import annotations

from collections.abc import Sequence
from hashlib import sha256
import logging

from .observer_synthesis_v2_budget import (
    BudgetValidationError,
    snapshot_budget_limits,
)
from .observer_synthesis_v2_cegis_codec import (
    limits_digest_v2,
    training_digest_v2,
)
from .observer_synthesis_v2_corpus import (
    DEFAULT_CASES,
    EXPECTED_DEFAULT_CORPUS_DIGEST,
)
from .observer_synthesis_v2_grammar import EXPECTED_DEFAULT_CATALOG_DIGEST
from .observer_synthesis_v2_types import SynthesisStatus
from .observer_synthesis_v2_worker_codec import (
    request_bytes_v2,
    request_from_bytes_v2,
)
from .observer_synthesis_v2_worker_types import (
    WORKER_REQUEST_SCHEMA,
    WORKER_RESULT_SCHEMA,
    ObserverWorkerRequestV2,
)
from .proof_core_codec import canonical_json, load_canonical

logger = logging.getLogger(__name__)

EXPECTED_TRAIN_IDS = (101, 102)
EXPECTED_TRAIN_DIGESTS = tuple(case.case_digest for case in DEFAULT_CASES[:2])
EXPECTED_WINNER_DIGEST = "7eb8dcdbd11c47eb2f8553c26ca2cd4f4a09027deccb2a2a69bee881f927e502"
EXPECTED_TRACE_DIGEST = "d27aaa2d61a7a7bd69e46bfd43eab76fadd1ac666e144d9241466bc5222e0da7"
EXPECTED_WINNER_CANONICAL = (
    '{"observer":{"child":{"tag":"input"},"primitive":"crest","tag":"apply"},'
    '"schema":"veyra.observer-core.v2"}'
)
TRACE_DOMAIN = b"veyra.observer-synthesis-v2.cegis-trace.r14.3b.v1\0transcript\0"
TRACE_SCHEMA = "veyra.observer-synthesis-v2.cegis-trace.r14.3b.v1"
EXPECTED_INPUT_DIGEST = "5eb21cbbf9ace8fb6c9264119177bf610a4c6f3dcaec5cad5820f8f2729542c4"
EXPECTED_COUNTEREXAMPLE_DIGEST = (
    "8046893653457efe1e81ca45f14b74ec3a856c66f1dc9a33bbda6de166c2c064"
)
EXPECTED_LEDGER = {
    "candidates": 1565,
    "canonical_bytes": 488550,
    "cutoff_reason": None,
    "evaluations": 6,
    "transcript_output_bytes": 1463,
}
INCOMPLETE_DETAILS = {
    "candidate-limit",
    "canonical-bytes-limit",
    "evaluation-limit",
    "transcript-output-bytes-limit",
    "wall-time-limit",
    "process-address-space-limit",
}


def validate_worker_request_v2(request: object) -> ObserverWorkerRequestV2:
    logger.debug("validate_worker_request_v2 entry type=%s", type(request).__name__)
    if type(request) is not ObserverWorkerRequestV2:
        raise ValueError("invalid-worker-request-type")
    schema = request.schema
    catalog = request.catalog_digest
    corpus = request.corpus_digest
    ids = request.train_case_ids
    digests = request.train_case_digests
    limits = request.limits
    if (
        type(schema) is not str
        or schema != WORKER_REQUEST_SCHEMA
        or type(catalog) is not str
        or catalog != EXPECTED_DEFAULT_CATALOG_DIGEST
        or type(corpus) is not str
        or corpus != EXPECTED_DEFAULT_CORPUS_DIGEST
        or type(ids) is not tuple
        or len(ids) != len(EXPECTED_TRAIN_IDS)
        or any(type(item) is not int for item in ids)
        or ids != EXPECTED_TRAIN_IDS
        or type(digests) is not tuple
        or len(digests) != len(EXPECTED_TRAIN_DIGESTS)
        or any(type(item) is not str for item in digests)
        or digests != EXPECTED_TRAIN_DIGESTS
    ):
        raise ValueError("invalid-worker-request-binding")
    try:
        checked_limits = snapshot_budget_limits(limits)
        trusted = ObserverWorkerRequestV2(
            schema,
            catalog,
            corpus,
            tuple(item for item in ids),
            tuple(item for item in digests),
            checked_limits,
        )
        encoded = request_bytes_v2(trusted)
        if request_from_bytes_v2(encoded) != trusted:
            raise ValueError("worker-request-roundtrip-mismatch")
    except BudgetValidationError as exc:
        logger.error("validate_worker_request_v2 invalid limits")
        raise ValueError("invalid-worker-request-limits") from exc
    logger.debug("validate_worker_request_v2 exit")
    return trusted


def _trace_digest(rows: Sequence[object], expected_limits: str) -> str:
    logger.debug("_trace_digest entry rows=%d", len(rows))
    digest = sha256(TRACE_DOMAIN)
    for row in rows:
        if type(row) is not str:
            raise ValueError("invalid-worker-trace-row")
        raw = row.encode()
        parsed = load_canonical(row)
        if (
            type(parsed) is not dict
            or parsed.get("limits_digest") != expected_limits
            or "elapsed_ns" in parsed
            or "transcript_output_bytes" in parsed
            or "cache" in parsed
            or "nonce" in parsed
        ):
            raise ValueError("invalid-worker-trace-binding")
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    result = digest.hexdigest()
    logger.debug("_trace_digest exit digest=%s", result[:12])
    return result


def _expected_trace_rows(expected_limits: str) -> list[str]:
    logger.debug("_expected_trace_rows entry limits=%s", expected_limits[:12])
    shared = {
        "charged_candidates": 1565,
        "charged_canonical_bytes": 488550,
        "limits_digest": expected_limits,
        "schema": TRACE_SCHEMA,
    }
    specifications = (
        (EXPECTED_INPUT_DIGEST, 0, 0, None, None, "SEED"),
        (
            EXPECTED_INPUT_DIGEST, 0, 2, EXPECTED_COUNTEREXAMPLE_DIGEST,
            102, "COUNTEREXAMPLE",
        ),
        (EXPECTED_WINNER_DIGEST, 1, 6, None, None, "WINNER"),
    )
    result = [
        canonical_json(
            {
                **shared,
                "candidate_digest": digest,
                "candidate_ordinal": ordinal,
                "charged_evaluations": evaluations,
                "counterexample_case_digest": case_digest,
                "counterexample_case_id": case_id,
                "event": event,
                "sequence": sequence,
            }
        )
        for sequence, (
            digest, ordinal, evaluations, case_digest, case_id, event,
        ) in enumerate(specifications, 1)
    ]
    logger.debug("_expected_trace_rows exit rows=%d", len(result))
    return result


def validate_complete_result_data_v2(
    data: object,
    request: ObserverWorkerRequestV2,
) -> tuple[SynthesisStatus, str]:
    logger.debug("validate_complete_result_data_v2 entry")
    keys = {
        "active_case_ids", "catalog_digest", "detail", "ledger",
        "limits_digest", "status", "trace", "trace_digest",
        "training_digest", "traversed_candidates", "winner",
    }
    if (
        type(data) is not dict
        or any(type(key) is not str for key in data)
        or set(data) != keys
        or type(data["status"]) is not str
    ):
        raise ValueError("invalid-worker-report-shape")
    try:
        status = SynthesisStatus(data["status"])
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid-worker-report-status") from exc
    if status is not SynthesisStatus.FOUND:
        raise ValueError("worker-report-not-complete")
    expected_limits = limits_digest_v2(request.limits)
    expected_training = training_digest_v2(request.train_case_digests)
    trace = data["trace"]
    ledger = data["ledger"]
    expected_trace = _expected_trace_rows(expected_limits)
    expected_trace_digest = _trace_digest(expected_trace, expected_limits)
    if (
        type(data["detail"]) is not str
        or type(data["catalog_digest"]) is not str
        or data["catalog_digest"] != request.catalog_digest
        or type(data["limits_digest"]) is not str
        or data["limits_digest"] != expected_limits
        or type(data["training_digest"]) is not str
        or data["training_digest"] != expected_training
        or type(trace) is not list
        or any(type(row) is not str for row in trace)
        or type(data["trace_digest"]) is not str
        or data["trace_digest"] != _trace_digest(trace, expected_limits)
        or trace != expected_trace
        or type(data["active_case_ids"]) is not list
        or any(type(item) is not int for item in data["active_case_ids"])
        or type(data["traversed_candidates"]) is not int
        or type(ledger) is not dict
        or any(type(key) is not str for key in ledger)
        or set(ledger) != set(EXPECTED_LEDGER)
        or any(
            type(ledger[key]) is not int
            for key in EXPECTED_LEDGER
            if key != "cutoff_reason"
        )
        or ledger["cutoff_reason"] is not None
    ):
        raise ValueError("invalid-worker-report-binding")
    winner = data["winner"]
    winner_keys = {"canonical", "cost", "depth", "digest", "ordinal"}
    if (
        type(winner) is not dict
        or any(type(key) is not str for key in winner)
        or set(winner) != winner_keys
        or type(winner["ordinal"]) is not int
        or type(winner["cost"]) is not int
        or type(winner["depth"]) is not int
        or type(winner["digest"]) is not str
        or type(winner["canonical"]) is not str
        or winner["ordinal"] != 1
        or winner["cost"] != 1
        or winner["depth"] != 1
        or winner["digest"] != EXPECTED_WINNER_DIGEST
        or winner["canonical"] != EXPECTED_WINNER_CANONICAL
        or sha256(winner["canonical"].encode()).hexdigest() != winner["digest"]
        or data["detail"] != "first-train-satisfying-candidate"
        or data["active_case_ids"] != [101, 102]
        or data["traversed_candidates"] != 2
        or data["trace_digest"] != expected_trace_digest
        or len(trace) != 3
        or ledger != EXPECTED_LEDGER
    ):
        raise ValueError("invalid-worker-winner")
    logger.debug("validate_complete_result_data_v2 exit status=%s", status.value)
    return status, data["detail"]


def parse_result_payload_v2(
    payload: bytes,
    request: ObserverWorkerRequestV2,
) -> tuple[SynthesisStatus, str, object | None]:
    logger.debug("parse_result_payload_v2 entry bytes=%d", len(payload))
    try:
        data = load_canonical(payload.decode())
    except (RecursionError, TypeError, UnicodeError, ValueError) as exc:
        logger.debug("parse_result_payload_v2 invalid canonical payload", exc_info=True)
        raise ValueError("invalid-worker-result-shape") from exc
    if (
        type(data) is not dict
        or any(type(key) is not str for key in data)
        or set(data) != {"detail", "report", "schema", "status"}
        or type(data["schema"]) is not str
        or data["schema"] != WORKER_RESULT_SCHEMA
        or type(data["detail"]) is not str
        or type(data["status"]) is not str
    ):
        raise ValueError("invalid-worker-result-shape")
    try:
        status = SynthesisStatus(data["status"])
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid-worker-result-status") from exc
    report = data["report"]
    if status is SynthesisStatus.FOUND:
        complete_status, detail = validate_complete_result_data_v2(report, request)
        if complete_status is not status or detail != data["detail"]:
            raise ValueError("worker-result-report-mismatch")
    elif (
        status is not SynthesisStatus.INCOMPLETE
        or report is not None
        or data["detail"] not in INCOMPLETE_DETAILS
    ):
        raise ValueError("invalid-worker-noncomplete-result")
    logger.debug("parse_result_payload_v2 exit status=%s", status.value)
    return status, data["detail"], report
