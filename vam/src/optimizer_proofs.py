"""Bounded optimizer proof bridge for VAM checked local-law slices."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import logging
from pathlib import Path
import shutil
import subprocess
from typing import Iterable

from .optimizer_obligations import OptimizerObligation, optimizer_obligation_rows
from .optimizer_proof_catalog import CHECKED_ARTIFACT, checked_laws_for_pass, missing_required_lean_symbols

logger = logging.getLogger(__name__)

BOUNDARY = "optimizer-proof-bridge"
CLAIM = "checked-local-laws-not-full-correctness"
OVERCLAIM_TERMS = (
    "proof-grade",
    "formal proof",
    "full correctness",
    "global correctness",
    "verified theorem",
    "complete verification",
    "soundness proof",
)


@dataclass(frozen=True)
class OptimizerProofRow:
    """One optimizer obligation row bound to one bounded proof artifact status."""

    pass_name: str
    obligation_id: str
    local_law: str
    proof_artifact: str
    lean_symbol: str
    formal_status: str
    evidence_scope: str
    boundary: str = BOUNDARY
    claim: str = CLAIM


@dataclass(frozen=True)
class OptimizerProofSummary:
    """Deterministic summary of the current optimizer proof bridge slice."""

    total_rows: int
    lean_checked_local_laws: int
    obligation_only_rows: int
    checked_local_laws: tuple[str, ...]
    obligation_backed_passes: tuple[str, ...]
    boundary: str = BOUNDARY
    claim: str = CLAIM


@dataclass(frozen=True)
class OptimizerLeanCheckResult:
    """Result of checking the optimizer Lean slice artifact."""

    path: str
    status: str
    stdout: str
    stderr: str


def _repo_root() -> Path:
    logger.debug("optimizer_proof_repo_root entry")
    result = Path(__file__).resolve().parents[2]
    logger.debug("optimizer_proof_repo_root exit path=%s", result)
    return result


def lean_optimizer_export_path(root: Path | None = None) -> Path:
    """Return the checked optimizer bridge Lean artifact path."""
    logger.debug("lean_optimizer_export_path entry root=%s", root)
    base = root or _repo_root()
    result = base / CHECKED_ARTIFACT
    logger.debug("lean_optimizer_export_path exit path=%s", result)
    return result


def check_lean_optimizer_export(path: Path | None = None) -> OptimizerLeanCheckResult:
    """Run Lean on the optimizer proof bridge artifact and bind all required local laws."""
    logger.debug("check_lean_optimizer_export entry path=%s", path)
    target = path or lean_optimizer_export_path()
    try:
        text = target.read_text(encoding="utf-8")
    except OSError as exc:
        result = OptimizerLeanCheckResult(str(target), "blocked", "", f"read-error:{exc}")
        logger.debug("check_lean_optimizer_export exit status=%s", result.status)
        return result
    missing = missing_required_lean_symbols(text)
    if missing:
        result = OptimizerLeanCheckResult(str(target), "blocked", "", f"missing-symbols:{','.join(missing)}")
        logger.debug("check_lean_optimizer_export exit status=%s missing=%r", result.status, missing)
        return result
    command = _lean_command()
    if command is None:
        result = OptimizerLeanCheckResult(str(target), "blocked", "", "lean-not-found")
        logger.debug("check_lean_optimizer_export exit status=%s", result.status)
        return result
    proc = subprocess.run(command + [str(target)], cwd=_repo_root(), text=True, capture_output=True, check=False)
    result = OptimizerLeanCheckResult(str(target), "checked" if proc.returncode == 0 else "blocked", proc.stdout.strip(), proc.stderr.strip())
    logger.debug("check_lean_optimizer_export exit status=%s", result.status)
    return result


def optimizer_proof_rows(lean_status: str | None = None) -> tuple[OptimizerProofRow, ...]:
    """Return deterministic proof-bridge rows for all current optimizer obligations."""
    logger.debug("optimizer_proof_rows entry lean_status=%s", lean_status)
    result = optimizer_proof_rows_from_obligations(optimizer_obligation_rows(), lean_status)
    logger.debug("optimizer_proof_rows exit rows=%d", len(result))
    return result


def optimizer_proof_rows_from_obligations(
    obligation_rows: Iterable[OptimizerObligation],
    lean_status: str | None = None,
) -> tuple[OptimizerProofRow, ...]:
    """Bind optimizer obligation rows to their current checked-artifact status."""
    obligations = tuple(obligation_rows)
    logger.debug("optimizer_proof_rows_from_obligations entry rows=%d lean_status=%s", len(obligations), lean_status)
    rows: list[OptimizerProofRow] = []
    for obligation in obligations:
        rows.extend(_proof_rows_from_obligation(obligation, lean_status))
    result = tuple(rows)
    logger.debug("optimizer_proof_rows_from_obligations exit rows=%d", len(result))
    return result


def optimizer_proof_summary(
    obligation_rows: Iterable[OptimizerObligation] | None = None,
    lean_status: str | None = None,
) -> OptimizerProofSummary:
    """Summarize the current bounded proof bridge without overclaiming coverage."""
    logger.debug("optimizer_proof_summary entry custom=%s", obligation_rows is not None)
    rows = optimizer_proof_rows(lean_status) if obligation_rows is None else optimizer_proof_rows_from_obligations(obligation_rows, lean_status)
    checked = tuple(row.local_law for row in rows if row.formal_status == "lean-checked-local-law")
    obligation_only = tuple(row.pass_name for row in rows if row.formal_status == "obligation-only")
    summary = OptimizerProofSummary(
        total_rows=len(rows),
        lean_checked_local_laws=len(checked),
        obligation_only_rows=len(obligation_only),
        checked_local_laws=checked,
        obligation_backed_passes=tuple(dict.fromkeys(row.pass_name for row in rows)),
    )
    logger.debug("optimizer_proof_summary exit total=%d checked=%d pending=%d", summary.total_rows, summary.lean_checked_local_laws, summary.obligation_only_rows)
    return summary


def optimizer_proof_payload(lean_status: str | None = None) -> tuple[dict[str, str], ...]:
    """Return JSON-friendly proof bridge rows."""
    logger.debug("optimizer_proof_payload entry lean_status=%s", lean_status)
    result = tuple(asdict(row) for row in optimizer_proof_rows(lean_status))
    logger.debug("optimizer_proof_payload exit rows=%d", len(result))
    return result


def assert_no_optimizer_proof_overclaim_terms(rows: Iterable[OptimizerProofRow | OptimizerProofSummary]) -> None:
    """Raise if bridge rows use proof-language beyond the bounded slice claim."""
    checked_rows = tuple(rows)
    logger.debug("optimizer_proof_assert_no_overclaim_terms entry rows=%d", len(checked_rows))
    for row in checked_rows:
        text = "\n".join(str(value).lower() for value in asdict(row).values())
        for term in OVERCLAIM_TERMS:
            if term in text:
                logger.debug("optimizer_proof_assert_no_overclaim_terms fail term=%s", term)
                raise ValueError(f"overclaim term present: {term}")
    logger.debug("optimizer_proof_assert_no_overclaim_terms exit ok")


def _proof_rows_from_obligation(row: OptimizerObligation, lean_status: str | None) -> tuple[OptimizerProofRow, ...]:
    logger.debug("_proof_rows_from_obligation entry pass=%s lean_status=%s", row.pass_name, lean_status)
    checked_laws = checked_laws_for_pass(row.pass_name)
    if checked_laws:
        status = "lean-checked-local-law" if lean_status == "checked" else "lean-check-required-local-law"
        result = tuple(
            OptimizerProofRow(
                pass_name=row.pass_name,
                obligation_id=row.obligation_id,
                local_law=law_id,
                proof_artifact=artifact,
                lean_symbol=symbol,
                formal_status=status,
                evidence_scope=scope,
            )
            for _, law_id, artifact, symbol, scope in checked_laws
        )
        logger.debug("_proof_rows_from_obligation exit local_laws pass=%s rows=%d", row.pass_name, len(result))
        return result
    result = (
        OptimizerProofRow(
            pass_name=row.pass_name,
            obligation_id=row.obligation_id,
            local_law="pending",
            proof_artifact="pending-proof-artifact",
            lean_symbol="pending",
            formal_status="obligation-only",
            evidence_scope="tracked obligation without a checked local-law artifact in the current bridge",
        ),
    )
    logger.debug("_proof_rows_from_obligation exit pending pass=%s", row.pass_name)
    return result


def _lean_command() -> list[str] | None:
    logger.debug("optimizer_proof_lean_command entry")
    elan = shutil.which("elan")
    if elan is not None:
        listed = subprocess.run([elan, "toolchain", "list"], text=True, capture_output=True, check=False)
        if "leanprover/lean4:v4.30.0-rc2" in listed.stdout:
            result = [elan, "run", "leanprover/lean4:v4.30.0-rc2", "lean"]
            logger.debug("optimizer_proof_lean_command exit explicit=%r", result)
            return result
    lean = shutil.which("lean")
    result = [lean] if lean else None
    logger.debug("optimizer_proof_lean_command exit result=%r", result)
    return result
