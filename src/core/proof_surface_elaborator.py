"""Source-bound proof-grade elaboration into the independently checked R7 core."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import NoReturn

from .proof_core_artifact import ProofArtifact, make_proof_artifact
from .proof_core_kernel import ProofKernelError, infer_proof
from .proof_core_types import CheckedJudgment, CoreProp, ProofContext, ProofTerm
from .proof_surface_codec import surface_syntax_digest
from .proof_surface_lowering import lower_surface_program
from .proof_surface_parser import parse_surface_program
from .proof_surface_trace import traced
from .proof_surface_types import (
    ABSOLUTE_SAFE_DEPTH, ABSOLUTE_TYPED_AST_NODES, DEFAULT_ELABORATION_LIMITS,
    DEFAULT_SOURCE_LIMITS, ElaborationLimits, SourceLimits, SourceSpan,
    SurfaceLanguageError, SurfaceProgram, SURFACE_LANGUAGE_ID, SURFACE_VERSION,
)
from .proof_surface_validation import captured_source_digest, validate_captured_surface


logger = logging.getLogger(__name__)
trace = traced(logger)


@dataclass(frozen=True)
class ElaboratedProgram:
    """Checked theorem bound to exact captured source, syntax, and semantics."""

    surface: SurfaceProgram
    claim: CoreProp
    proof: ProofTerm
    judgment: CheckedJudgment
    artifact: ProofArtifact
    source_digest: str
    syntax_digest: str
    semantic_digest: str


@trace
def _fail(code: str, span: SourceSpan | None = None) -> NoReturn:
    logger.error("surface elaboration rejection state code=%s span=%r", code, span)
    raise SurfaceLanguageError("elaborate", code, span)


@trace
def _checked_limits(limits: ElaborationLimits, span: SourceSpan | None) -> ElaborationLimits:
    if (
        type(limits) is not ElaborationLimits
        or type(limits.max_depth) is not int or not 0 < limits.max_depth <= ABSOLUTE_SAFE_DEPTH
        or type(limits.max_binders) is not int or not 0 < limits.max_binders <= ABSOLUTE_SAFE_DEPTH
        or type(limits.max_nodes) is not int or not 0 < limits.max_nodes <= ABSOLUTE_TYPED_AST_NODES
    ):
        _fail("invalid-elaboration-limits", span)
    return limits


@trace
def _finish_captured(
    program: SurfaceProgram, source: bytes, limits: ElaborationLimits,
) -> ElaboratedProgram:
    if (
        type(program) is not SurfaceProgram
        or program.language_id != SURFACE_LANGUAGE_ID
        or program.version != SURFACE_VERSION
    ):
        _fail("invalid-surface-program", getattr(program, "span", None))
    checked = _checked_limits(limits, program.span)
    validate_captured_surface(program, len(source), checked.max_nodes)
    claim, proof = lower_surface_program(program, checked)
    try:
        judgment = infer_proof(ProofContext(), proof)
    except ProofKernelError as exc:
        _fail(f"kernel-rejected/{exc}", program.proof.span)
    if judgment.conclusion != claim:
        _fail("declared-conclusion-mismatch", program.claim.span)
    artifact = make_proof_artifact(SURFACE_LANGUAGE_ID, ProofContext(), proof)
    result = ElaboratedProgram(
        program, claim, proof, judgment, artifact, captured_source_digest(source),
        surface_syntax_digest(program), artifact.proof_digest,
    )
    logger.debug("_finish_captured state semantic-digest=%s", result.semantic_digest)
    return result


@trace
def _decode_capture(source: bytes) -> str:
    if type(source) is not bytes:
        _fail("captured-source-must-be-bytes")
    try:
        result = source.decode("ascii")
    except UnicodeDecodeError:
        _fail("captured-source-not-ascii")
    logger.debug("_decode_capture state bytes=%d", len(source))
    return result


@trace
def elaborate_surface_program(
    program: SurfaceProgram,
    limits: ElaborationLimits = DEFAULT_ELABORATION_LIMITS,
    captured_source: bytes | None = None,
    *,
    source_digest: str | None = None,
) -> ElaboratedProgram:
    """Low-level compatibility path; reject ASTs not replayed from captured bytes."""
    try:
        if source_digest is not None:
            _fail("forged-source-digest", getattr(program, "span", None))
        if captured_source is None:
            _fail("unbound-typed-ast", getattr(program, "span", None))
        if type(captured_source) is not bytes:
            _fail("captured-source-must-be-bytes", getattr(program, "span", None))
        checked = _checked_limits(limits, getattr(program, "span", None))
        validate_captured_surface(program, len(captured_source), checked.max_nodes)
        text = _decode_capture(captured_source)
        if parse_surface_program(text) != program:
            _fail("captured-source-ast-mismatch", program.span)
        return _finish_captured(program, captured_source, checked)
    except RecursionError:
        _fail("safe-recursion-limit", getattr(program, "span", None))


@trace
def compile_surface_program(
    source: str,
    source_limits: SourceLimits = DEFAULT_SOURCE_LIMITS,
    elaboration_limits: ElaborationLimits = DEFAULT_ELABORATION_LIMITS,
) -> ElaboratedProgram:
    """Public proof-grade path: parse, lower, and check only captured source."""
    try:
        program = parse_surface_program(source, source_limits)
        result = _finish_captured(program, source.encode("ascii"), elaboration_limits)
    except RecursionError:
        _fail("safe-recursion-limit")
    logger.debug("compile_surface_program state source-digest=%s", result.source_digest)
    return result
