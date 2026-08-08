"""Immutable proof syntax for the conservative R11 observer core."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from .observer_core_types import EchoOutcome, Observation, ObserverExpr, PathStep
from .proof_core_types import CheckedJudgment, CoreProp, CoreTerm, ProofContext, ProofTerm


class ObserverRuleId(str, Enum):
    """The complete proof-rule vocabulary of the first observer kernel."""

    EMBED_R7 = "embed-r7"
    EQUALITY_READY_ECHO = "equality-ready-echo"
    CREST_PULSE_ECHO = "crest-pulse-echo"
    TAIL_SILENCE_OBSTRUCTION = "tail-silence-obstruction"


class ObserverLawId(str, Enum):
    """Closed observer laws admitted by the R11 kernel."""

    EQUALITY_READY_ECHO = "equality-ready-echo"
    CREST_PULSE_ECHO = "crest-pulse-echo"
    TAIL_SILENCE_OBSTRUCTION = "tail-silence-obstruction"


class ObserverSupportId(str, Enum):
    """Replay-derived trusted support surfaces."""

    R7_KERNEL = "r7-proof-kernel"
    OBSERVER_SEMANTICS = "observer-core-semantics"
    OBSERVER_CODEC = "observer-core-codec"
    STRUCTURAL_TOTALITY = "observer-structural-totality"
    CREST_PULSE_LAW = "crest-pulse-law"
    TAIL_SILENCE_LAW = "tail-silence-law"


@dataclass(frozen=True)
class EmbeddedR7:
    """An R7 proposition rechecked by the unchanged R7 kernel."""

    proposition: CoreProp


@dataclass(frozen=True)
class Echoes:
    """Two closed recurrences have one exact defined observer response."""

    observer: ObserverExpr
    left: CoreTerm
    right: CoreTerm


@dataclass(frozen=True)
class Obstructed:
    """A closed recurrence is outside an observer's native domain."""

    observer: ObserverExpr
    recurrence: CoreTerm


ObserverConclusion: TypeAlias = EmbeddedR7 | Echoes | Obstructed


@dataclass(frozen=True)
class EmbedR7:
    """Embed evidence, never a caller-declared R7 proposition."""

    evidence: ProofTerm


@dataclass(frozen=True)
class EqualityReadyEcho:
    """Transport an R7 equality through a structurally total observer."""

    observer: ObserverExpr
    equality: "ObserverProof"


@dataclass(frozen=True)
class CrestPulseEcho:
    """The exact crest(Pulse(_)) = pulse echo law."""

    left_tail: CoreTerm
    right_tail: CoreTerm


@dataclass(frozen=True)
class TailSilenceObstruction:
    """The exact tail(Silence) domain obstruction law."""


ObserverProof: TypeAlias = EmbedR7 | EqualityReadyEcho | CrestPulseEcho | TailSilenceObstruction
ObserverProofOutcome: TypeAlias = CheckedJudgment | EchoOutcome | Observation


@dataclass(frozen=True)
class ObserverCheckedJudgment:
    """A fully replay-derived observer judgment and its exact support closure."""

    context: ProofContext
    conclusion: ObserverConclusion
    outcome: ObserverProofOutcome
    obstruction_paths: tuple[tuple[PathStep, ...], ...]
    rule_trace: tuple[ObserverRuleId, ...]
    rule_closure: tuple[ObserverRuleId, ...]
    observer_law_closure: tuple[ObserverLawId, ...]
    r7_rule_closure: tuple[str, ...]
    r7_native_law_closure: tuple[str, ...]
    support: tuple[ObserverSupportId, ...]
