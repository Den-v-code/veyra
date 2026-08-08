"""Immutable syntax for the proof-carrying Veyra recurrence core."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias


class CoreType(str, Enum):
    """Types admitted by the first trusted proof core."""

    RECURRENCE = "recurrence"


class RuleId(str, Enum):
    """Inference rules admitted by the trusted checker."""

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


class NativeLawId(str, Enum):
    """Closed native-law templates justified independently in Lean."""

    STITCH_SILENCE_LEFT = "stitch-silence-left"
    STITCH_SILENCE_RIGHT = "stitch-silence-right"
    WEAVE_SILENCE_RIGHT = "weave-silence-right"
    WEAVE_PULSE = "weave-pulse"
    WEAVE_UNIT_RIGHT = "weave-unit-right"


@dataclass(frozen=True)
class Bound:
    """A de Bruijn variable, zero being the innermost binder."""

    index: int


@dataclass(frozen=True)
class Silence:
    """The empty recurrence."""


@dataclass(frozen=True)
class Pulse:
    """One pulse followed by a recurrence."""

    tail: "CoreTerm"


@dataclass(frozen=True)
class Stitch:
    """Structural recurrence concatenation."""

    left: "CoreTerm"
    right: "CoreTerm"


@dataclass(frozen=True)
class Weave:
    """Structural repetition of one recurrence along another."""

    left: "CoreTerm"
    right: "CoreTerm"


CoreTerm: TypeAlias = Bound | Silence | Pulse | Stitch | Weave


@dataclass(frozen=True)
class Equal:
    """Structural equality proposition."""

    left: CoreTerm
    right: CoreTerm


@dataclass(frozen=True)
class Implies:
    """Implication proposition."""

    premise: "CoreProp"
    conclusion: "CoreProp"


@dataclass(frozen=True)
class Forall:
    """Universal proposition; its body binds de Bruijn index zero."""

    binder_type: CoreType
    body: "CoreProp"


@dataclass(frozen=True)
class Resonates:
    """A weave witness exists from factor to carrier."""

    factor: CoreTerm
    carrier: CoreTerm


CoreProp: TypeAlias = Equal | Implies | Forall | Resonates


@dataclass(frozen=True)
class ProofContext:
    """Typed term binders and proposition assumptions, innermost first."""

    term_types: tuple[CoreType, ...] = ()
    assumptions: tuple[CoreProp, ...] = ()


@dataclass(frozen=True)
class Assume:
    """Select one proposition assumption by de Bruijn index."""

    index: int


@dataclass(frozen=True)
class ImpIntro:
    """Discharge one proposition assumption."""

    premise: CoreProp
    body: "ProofTerm"


@dataclass(frozen=True)
class ImpElim:
    """Apply an implication proof to its premise proof."""

    function: "ProofTerm"
    argument: "ProofTerm"


@dataclass(frozen=True)
class ForallIntro:
    """Introduce a fresh typed term binder."""

    binder_type: CoreType
    body: "ProofTerm"


@dataclass(frozen=True)
class ForallElim:
    """Instantiate a universal proof with a typed term."""

    universal: "ProofTerm"
    argument: CoreTerm


@dataclass(frozen=True)
class EqRefl:
    """Structural equality reflexivity."""

    term: CoreTerm


@dataclass(frozen=True)
class EqSym:
    """Structural equality symmetry."""

    evidence: "ProofTerm"


@dataclass(frozen=True)
class EqTrans:
    """Structural equality transitivity with ordered premises."""

    left: "ProofTerm"
    right: "ProofTerm"


@dataclass(frozen=True)
class NativeLaw:
    """Instantiate one strict native-law template."""

    law_id: NativeLawId
    args: tuple[CoreTerm, ...]


@dataclass(frozen=True)
class ResonanceIntro:
    """Introduce resonance from an exact weave reconstruction equality."""

    factor: CoreTerm
    carrier: CoreTerm
    witness: CoreTerm
    equality: "ProofTerm"


ProofTerm: TypeAlias = (
    Assume | ImpIntro | ImpElim | ForallIntro | ForallElim | EqRefl | EqSym
    | EqTrans | NativeLaw | ResonanceIntro
)


@dataclass(frozen=True)
class CheckedJudgment:
    """A checker-derived conclusion and exact rule/law closures."""

    context: ProofContext
    conclusion: CoreProp
    rule_trace: tuple[RuleId, ...]
    rule_closure: tuple[RuleId, ...]
    native_law_closure: tuple[NativeLawId, ...]
