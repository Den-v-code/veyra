"""Bounded optimizer witness ledger for regression evidence."""
from __future__ import annotations

from hashlib import sha256
import json
import logging
from typing import Any, Iterable

from .equivalence import EquivalenceSummary, summarize_equivalence
from .interpreter import execute
from .model import Instruction
from .optimizer import OptimizationReport, optimize
from .optimizer_obligations import (
    CLAIM as OBLIGATION_CLAIM,
    BOUNDARY as OBLIGATION_BOUNDARY,
    optimizer_obligation_coverage_payload,
    optimizer_obligation_payload,
)
from .report import canonical_report, instruction_rows

logger = logging.getLogger(__name__)

BOUNDARY = "bounded-witness-ledger"
CLAIM = "regression-evidence-not-proof"
DIGEST_ALGORITHM = "sha256-json-v1"

JsonDict = dict[str, Any]


def optimizer_witness_ledger(program: Iterable[Instruction]) -> JsonDict:
    """Build a deterministic, bounded witness ledger for one optimizer run."""
    original_program = tuple(program)
    logger.debug("optimizer_witness_ledger entry instructions=%d", len(original_program))
    report = optimize(original_program)
    summary = summarize_equivalence(report.original, report.optimized)
    original_rows = instruction_rows(report.original)
    optimized_rows = instruction_rows(report.optimized)
    optimizer_decisions = _optimizer_rows(report)
    optimizer_obligations = _optimizer_obligation_ledger(report)
    equivalence = _equivalence_summary(summary)
    semantic_core = _semantic_core_pair(report)
    digests = {
        "original_instruction_rows": stable_digest(original_rows),
        "optimized_instruction_rows": stable_digest(optimized_rows),
        "optimizer_rows": stable_digest(optimizer_decisions),
        "optimizer_obligation_ledger": stable_digest(optimizer_obligations),
        "equivalence_summary_checks": stable_digest(equivalence),
        "semantic_core_report": stable_digest(semantic_core),
    }
    body: JsonDict = {
        "profile": "vam-optimizer-witness-v1",
        "boundary": BOUNDARY,
        "claim": CLAIM,
        "status": _bounded_status(summary),
        "digest_algorithm": DIGEST_ALGORITHM,
        "digests": digests,
        "original_instruction_rows": original_rows,
        "optimized_instruction_rows": optimized_rows,
        "optimizer_rows": optimizer_decisions,
        "optimizer_obligation_ledger": optimizer_obligations,
        "equivalence_summary": equivalence,
        "semantic_core_report": semantic_core,
    }
    body["ledger_digest"] = stable_digest(body)
    logger.debug("optimizer_witness_ledger exit status=%s rows=%d", body["status"], len(report.rows))
    return body


def stable_digest(value: Any) -> str:
    """Return a byte-stable SHA-256 digest for JSON-compatible data."""
    logger.debug("stable_digest entry type=%s", type(value).__name__)
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    result = sha256(payload.encode("utf-8")).hexdigest()
    logger.debug("stable_digest exit digest=%s", result[:12])
    return result


def semantic_core_report(program: Iterable[Instruction]) -> JsonDict:
    """Return the bounded canonical semantic core used by the witness ledger."""
    program_tuple = tuple(program)
    logger.debug("semantic_core_report entry instructions=%d", len(program_tuple))
    report = canonical_report(program_tuple, execute(program_tuple))
    result = {
        "profile": report["profile"],
        "final_pc": report["final_pc"],
        "trace": report["trace"],
        "registers": report["registers"],
        "certs": report["certs"],
        "obstructions": report["obstructions"],
    }
    logger.debug(
        "semantic_core_report exit trace=%d registers=%d obstructions=%d",
        len(result["trace"]),
        len(result["registers"]),
        len(result["obstructions"]),
    )
    return result


def _optimizer_rows(report: OptimizationReport) -> JsonDict:
    logger.debug("optimizer_rows entry rows=%d", len(report.rows))
    all_rows = [
        {
            "pass_name": row.pass_name,
            "action": row.action,
            "detail": row.detail,
            "accepted": row.accepted,
        }
        for row in report.rows
    ]
    result = {
        "all": all_rows,
        "accepted": [row for row in all_rows if row["accepted"] is True],
        "rejected": [row for row in all_rows if row["accepted"] is False],
    }
    logger.debug(
        "optimizer_rows exit accepted=%d rejected=%d",
        len(result["accepted"]),
        len(result["rejected"]),
    )
    return result


def _optimizer_obligation_ledger(report: OptimizationReport) -> JsonDict:
    logger.debug("_optimizer_obligation_ledger entry rows=%d", len(report.rows))
    result = {
        "boundary": OBLIGATION_BOUNDARY,
        "claim": OBLIGATION_CLAIM,
        "rows": optimizer_obligation_payload(),
        "coverage": optimizer_obligation_coverage_payload(report.rows),
    }
    logger.debug(
        "_optimizer_obligation_ledger exit rows=%d coverage=%d",
        len(result["rows"]),
        len(result["coverage"]),
    )
    return result


def _equivalence_summary(summary: EquivalenceSummary) -> JsonDict:
    logger.debug("equivalence_summary entry status=%s checks=%d", summary.status, len(summary.checks))
    result = {
        "status": summary.status,
        "verdict": summary.verdict,
        "original_ops": summary.original_ops,
        "optimized_ops": summary.optimized_ops,
        "original_trace": summary.original_trace,
        "optimized_trace": summary.optimized_trace,
        "checks": [
            {
                "name": check.name,
                "status": check.status,
                "detail": check.detail,
                "original": check.original,
                "optimized": check.optimized,
            }
            for check in summary.checks
        ],
    }
    logger.debug("equivalence_summary exit verdict=%s", result["verdict"])
    return result


def _semantic_core_pair(report: OptimizationReport) -> JsonDict:
    logger.debug("semantic_core_pair entry original=%d optimized=%d", len(report.original), len(report.optimized))
    result = {
        "original": semantic_core_report(report.original),
        "optimized": semantic_core_report(report.optimized),
    }
    logger.debug("semantic_core_pair exit")
    return result


def _bounded_status(summary: EquivalenceSummary) -> str:
    if summary.status == "equivalent":
        return "bounded-regression-match"
    if summary.status == "blocked":
        return "bounded-regression-blocked"
    return "bounded-regression-inconclusive"
