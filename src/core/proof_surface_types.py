"""Immutable versioned syntax for the proof-grade recurrence surface language."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging


logger = logging.getLogger(__name__)


SURFACE_LANGUAGE_ID = "veyra.proof-surface.v1"
SURFACE_VERSION = 1
ABSOLUTE_SAFE_DEPTH = 128
ABSOLUTE_TYPED_AST_NODES = 4_096
CAPTURED_SOURCE_DOMAIN = b"veyra-proof-elaboration-source-v1\0"


@dataclass(frozen=True, order=True)
class SourceSpan:
    """Half-open UTF-8/ASCII source offsets for deterministic diagnostics."""

    start: int
    end: int


class SurfaceLanguageError(ValueError):
    """A stable parser/elaborator rejection with a precise source span."""

    def __init__(self, stage: str, code: str, span: SourceSpan | None = None) -> None:
        logger.debug("SurfaceLanguageError.__init__ entry stage=%s code=%s span=%r", stage, code, span)
        safe_span = span if type(span) is SourceSpan else None
        self.stage = stage
        self.code = code
        self.span = safe_span
        location = "" if safe_span is None else f"@{safe_span.start}:{safe_span.end}"
        super().__init__(f"{stage}:{code}{location}")
        logger.debug("SurfaceLanguageError.__init__ exit state=initialized")


class TermOp(str, Enum):
    """Surface recurrence-term constructors."""

    VARIABLE = "var"
    SILENCE = "silence"
    PULSE = "pulse"
    STITCH = "stitch"
    WEAVE = "weave"


class PropOp(str, Enum):
    """Surface proposition constructors."""

    EQUAL = "equal"
    IMPLIES = "implies"
    FORALL = "forall"
    RESONATES = "resonates"


class ProofOp(str, Enum):
    """One explicit constructor for every R7 ``RuleId``."""

    ASSUME = "assume"
    IMP_INTRO = "imp-intro"
    IMP_ELIM = "imp-elim"
    FORALL_INTRO = "forall-intro"
    FORALL_ELIM = "forall-elim"
    EQ_REFL = "eq-refl"
    EQ_SYM = "eq-sym"
    EQ_TRANS = "eq-trans"
    NATIVE_LAW = "native-law"
    RESONANCE_INTRO = "resonance-intro"


@dataclass(frozen=True)
class TermSyntax:
    """A parsed recurrence term before name resolution."""

    op: TermOp
    span: SourceSpan
    children: tuple["TermSyntax", ...] = ()
    name: str | None = None


@dataclass(frozen=True)
class PropSyntax:
    """A parsed proposition before binder resolution."""

    op: PropOp
    span: SourceSpan
    terms: tuple[TermSyntax, ...] = ()
    props: tuple["PropSyntax", ...] = ()
    binder_name: str | None = None
    binder_type: str | None = None


@dataclass(frozen=True)
class ProofSyntax:
    """A parsed explicit proof tree before binder resolution."""

    op: ProofOp
    span: SourceSpan
    proofs: tuple["ProofSyntax", ...] = ()
    terms: tuple[TermSyntax, ...] = ()
    props: tuple[PropSyntax, ...] = ()
    name: str | None = None
    binder_type: str | None = None
    law_id: str | None = None


@dataclass(frozen=True)
class SurfaceProgram:
    """A closed claim and explicit proof in one exact language version."""

    language_id: str
    version: int
    claim: PropSyntax
    proof: ProofSyntax
    span: SourceSpan


@dataclass(frozen=True)
class SourceLimits:
    """Fail-closed parser budgets."""

    max_bytes: int = 32_768
    max_tokens: int = 4_096
    max_nodes: int = 2_048
    max_depth: int = 96
    max_identifier_bytes: int = 64


@dataclass(frozen=True)
class ElaborationLimits:
    """Fail-closed binder and recursive-elaboration budgets."""

    max_depth: int = 96
    max_binders: int = 96
    max_nodes: int = 2_048


DEFAULT_SOURCE_LIMITS = SourceLimits()
DEFAULT_ELABORATION_LIMITS = ElaborationLimits()
