"""Closed immutable value vocabulary for the R12.2 intrinsic VAM sidecar."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias


@dataclass(frozen=True, slots=True)
class IntrinsicAnchorIR:
    """The fixed R9 ``intrinsic-origin`` anchor."""


@dataclass(frozen=True, slots=True)
class IntrinsicTactIR:
    """The fixed R9 self-loop ``intrinsic-successor`` tact."""


@dataclass(frozen=True, slots=True)
class IntrinsicRecurrenceIR:
    """Exact R9-image breath shape: silence has anchor; pulses have tacts."""

    tacts: tuple[IntrinsicTactIR, ...]
    anchor: IntrinsicAnchorIR | None


class IntrinsicMarkIR(str, Enum):
    """Closed R11 crest marks."""

    SILENT = "silent"
    PULSE = "pulse"


class IntrinsicPathStepIR(str, Enum):
    """Closed outer-to-inner obstruction path steps."""

    APPLY_TAIL = "apply-tail"
    APPLY_CREST = "apply-crest"
    PAIR_LEFT = "pair-left"
    PAIR_RIGHT = "pair-right"


class IntrinsicObstructionCodeIR(str, Enum):
    """Closed R11 obstruction vocabulary."""

    TAIL_OF_SILENCE = "tail-of-silence"


@dataclass(frozen=True, slots=True)
class IntrinsicObstructionIR:
    """One typed obstruction and its outer-to-inner path."""

    code: IntrinsicObstructionCodeIR
    path: tuple[IntrinsicPathStepIR, ...]


@dataclass(frozen=True, slots=True)
class IntrinsicRecurrenceValueIR:
    """A recurrence response value."""

    recurrence: IntrinsicRecurrenceIR


@dataclass(frozen=True, slots=True)
class IntrinsicMarkValueIR:
    """A crest-mark response value."""

    mark: IntrinsicMarkIR


@dataclass(frozen=True, slots=True)
class IntrinsicPairValueIR:
    """An ordered product response."""

    left: "IntrinsicResponseValueIR"
    right: "IntrinsicResponseValueIR"


IntrinsicResponseValueIR: TypeAlias = (
    IntrinsicRecurrenceValueIR | IntrinsicMarkValueIR | IntrinsicPairValueIR
)


@dataclass(frozen=True, slots=True)
class IntrinsicReadyIR:
    """A defined typed response."""

    value: IntrinsicResponseValueIR


@dataclass(frozen=True, slots=True)
class IntrinsicBlockedIR:
    """A nonempty tuple of typed obstructions."""

    obstructions: tuple[IntrinsicObstructionIR, ...]


@dataclass(frozen=True, slots=True)
class IntrinsicEchoIR:
    """Two defined observations share one response."""

    value: IntrinsicResponseValueIR


@dataclass(frozen=True, slots=True)
class IntrinsicMismatchIR:
    """Two defined responses differ."""

    left: IntrinsicResponseValueIR
    right: IntrinsicResponseValueIR


@dataclass(frozen=True, slots=True)
class IntrinsicDomainBlockedIR:
    """At least one comparison side is obstructed."""

    left: tuple[IntrinsicObstructionIR, ...]
    right: tuple[IntrinsicObstructionIR, ...]


IntrinsicObservationIR: TypeAlias = IntrinsicReadyIR | IntrinsicBlockedIR
IntrinsicEchoOutcomeIR: TypeAlias = IntrinsicEchoIR | IntrinsicMismatchIR | IntrinsicDomainBlockedIR
IntrinsicIR: TypeAlias = (
    IntrinsicAnchorIR
    | IntrinsicTactIR
    | IntrinsicRecurrenceIR
    | IntrinsicMarkIR
    | IntrinsicResponseValueIR
    | IntrinsicObstructionIR
    | IntrinsicObservationIR
    | IntrinsicEchoOutcomeIR
)
