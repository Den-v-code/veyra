"""Bounded optimizer proof-obligation ledger for VAM v1.9."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import logging
from typing import Iterable

from .optimizer import OptimizationRow

logger = logging.getLogger(__name__)

BOUNDARY = "proof-obligation-ledger"
CLAIM = "obligation-map-not-proof"
OVERCLAIM_TERMS = (
    "proof-grade",
    "formal proof",
    "machine-checked",
    "verified theorem",
    "soundness proof",
)


@dataclass(frozen=True)
class OptimizerObligation:
    """Static ledger row for one optimizer pass family."""

    pass_name: str
    obligation_id: str
    precondition: str
    postcondition: str
    invariant: str
    boundary: str = BOUNDARY
    claim: str = CLAIM


@dataclass(frozen=True)
class OptimizerObligationCoverage:
    """One optimizer decision row mapped onto its bounded obligation."""

    pass_name: str
    obligation_id: str
    action: str
    detail: str
    accepted: bool
    coverage_status: str
    precondition: str
    postcondition: str
    invariant: str
    boundary: str = BOUNDARY
    claim: str = CLAIM


_OBLIGATIONS = (
    OptimizerObligation(
        pass_name="observer-alias",
        obligation_id="observer-alias-boundary-v1",
        precondition="duplicate OBSERVER kind rewrites only when the candidate register has a single definition",
        postcondition="optimized rows reuse the first observer register and do not introduce new observer kinds",
        invariant="observer identity remains a bounded alias rewrite ledger entry rather than a semantic proof",
    ),
    OptimizerObligation(
        pass_name="compress-alias",
        obligation_id="compress-alias-boundary-v1",
        precondition="duplicate COMPRESS source/observer pairs rewrite only when single-definition and obstruction-preservation guards hold",
        postcondition="accepted rows drop redundant compress aliases and rejected rows preserve the original candidate",
        invariant="compression shadow boundaries must stay explicit whenever obstruction evidence could be erased",
    ),
    OptimizerObligation(
        pass_name="compress-idempotent",
        obligation_id="compress-idempotent-boundary-v1",
        precondition="same-observer nested COMPRESS rows rewrite only when the observer contract is bounded-idempotent and visible uses stay aligned",
        postcondition="accepted rows alias the outer compress to the inner source and rejected rows keep the nested step intact",
        invariant="observer-kind contracts and obstruction-preservation checks remain explicit ledger guards",
    ),
    OptimizerObligation(
        pass_name="dead-shadow",
        obligation_id="dead-shadow-boundary-v1",
        precondition="unused OBSERVE/COMPRESS candidates rewrite only when the destination has one definition and carries no obstruction boundary",
        postcondition="accepted rows drop dead shadows while rejected rows keep potentially evidence-bearing candidates",
        invariant="dead-code pruning must not erase bounded obstruction evidence or overwrite ambiguity",
    ),
)

_OBLIGATION_BY_PASS = {row.pass_name: row for row in _OBLIGATIONS}


def optimizer_obligation_rows() -> tuple[OptimizerObligation, ...]:
    """Return the deterministic bounded obligation ledger for current optimizer passes."""
    logger.debug("optimizer_obligation_rows entry")
    logger.debug("optimizer_obligation_rows exit rows=%d", len(_OBLIGATIONS))
    return _OBLIGATIONS


def optimizer_obligation_payload() -> tuple[dict[str, str], ...]:
    """Return JSON-friendly obligation rows."""
    logger.debug("optimizer_obligation_payload entry")
    result = tuple(asdict(row) for row in optimizer_obligation_rows())
    logger.debug("optimizer_obligation_payload exit rows=%d", len(result))
    return result


def optimizer_obligation_coverage(rows: Iterable[OptimizationRow]) -> tuple[OptimizerObligationCoverage, ...]:
    """Map optimizer decision rows onto bounded proof-obligation coverage rows."""
    rows_tuple = tuple(rows)
    logger.debug("optimizer_obligation_coverage entry rows=%d", len(rows_tuple))
    coverage: list[OptimizerObligationCoverage] = []
    for row in rows_tuple:
        obligation = _OBLIGATION_BY_PASS.get(row.pass_name)
        if obligation is None:
            logger.debug("optimizer_obligation_coverage skip unknown_pass=%s", row.pass_name)
            continue
        coverage.append(
            OptimizerObligationCoverage(
                pass_name=row.pass_name,
                obligation_id=obligation.obligation_id,
                action=row.action,
                detail=row.detail,
                accepted=row.accepted,
                coverage_status="accepted-covered" if row.accepted else "rejected-covered",
                precondition=obligation.precondition,
                postcondition=obligation.postcondition,
                invariant=obligation.invariant,
            )
        )
    result = tuple(coverage)
    logger.debug("optimizer_obligation_coverage exit rows=%d", len(result))
    return result


def optimizer_obligation_coverage_payload(rows: Iterable[OptimizationRow]) -> tuple[dict[str, str | bool], ...]:
    """Return JSON-friendly coverage rows."""
    logger.debug("optimizer_obligation_coverage_payload entry")
    result = tuple(asdict(row) for row in optimizer_obligation_coverage(rows))
    logger.debug("optimizer_obligation_coverage_payload exit rows=%d", len(result))
    return result


def optimizer_obligation_summary(rows: Iterable[OptimizationRow]) -> dict[str, tuple[str, ...]]:
    """Return deterministic per-pass coverage statuses."""
    rows_tuple = tuple(rows)
    logger.debug("optimizer_obligation_summary entry rows=%d", len(rows_tuple))
    per_pass = {row.pass_name: [] for row in optimizer_obligation_rows()}
    for item in optimizer_obligation_coverage(rows_tuple):
        per_pass[item.pass_name].append(item.coverage_status)
    result = {name: tuple(statuses) for name, statuses in per_pass.items()}
    logger.debug("optimizer_obligation_summary exit passes=%d", len(result))
    return result


def assert_no_overclaim_terms(rows: Iterable[OptimizerObligation | OptimizerObligationCoverage]) -> None:
    """Raise if a ledger row uses overclaim language."""
    rows_tuple = tuple(rows)
    logger.debug("assert_no_overclaim_terms entry rows=%d", len(rows_tuple))
    for row in rows_tuple:
        text = "\n".join(str(value).lower() for value in asdict(row).values())
        for term in OVERCLAIM_TERMS:
            if term in text:
                logger.debug("assert_no_overclaim_terms fail term=%s", term)
                raise ValueError(f"overclaim term present: {term}")
    logger.debug("assert_no_overclaim_terms exit ok")
