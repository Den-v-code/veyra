"""Closed DTOs for P1-D2 finite-to-universal counterpressure."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias


class CounterpressureRequestKind(str, Enum):
    LEDGER = "nonuniform-ledger"
    DESCENT = "natural-strict-descent-tree"
    CHOOSER = "target-dependent-chooser"
    LONG_RUN = "long-finite-run"
    SHRINKING = "shrinking-nonempty-stages"


class CounterpressureInference(str, Enum):
    LEDGER_GENERATOR = "finite-ledger-establishes-uniform-generator"
    FINITE_DEPTH_BRANCH = "arbitrary-finite-depth-implies-infinite-branch"
    POSTHOC_INDEPENDENCE = "posthoc-match-implies-target-independence"
    LONG_RUN_FAMILY = "long-finite-run-establishes-all-depth-family"
    NESTED_COMMON_POINT = "nested-nonempty-stages-imply-common-point"


class CounterpressureOutcomeKind(str, Enum):
    EVIDENCE_INSUFFICIENCY = "evidence-insufficiency"
    MATHEMATICAL_COUNTERMODEL = "mathematical-countermodel"


class CounterpressureStatus(str, Enum):
    INSUFFICIENT_TO_ESTABLISH = "insufficient-to-establish"
    REFUTES_MATHEMATICAL_IMPLICATION = "refutes-mathematical-implication"


class BasisUse(str, Enum):
    BOUND = "bound"
    NONE = "none"


class DerivationKind(str, Enum):
    LEAN_CHECKED_THEOREM = "lean-checked-theorem"


class GeneratorNonexistence(str, Enum):
    NOT_PROVED = "not-proved"


class AllDepthFamilyStatus(str, Enum):
    OPEN = "open"


class CompletedCarrierStatus(str, Enum):
    NOT_ESTABLISHED = "not-established"


class HistoricalTargetIndependence(str, Enum):
    NOT_ESTABLISHED = "not-established"


class ChooserTargetIndependence(str, Enum):
    REFUTED = "refuted"


class CounterpressureResourceBound(str, Enum):
    REQUEST_BYTES = "request-bytes"
    SYMBOLIC_COST = "symbolic-cost"


@dataclass(frozen=True)
class CounterpressureBasisSource:
    version: str
    basis_id: str
    derivation_kind: DerivationKind
    foundation_id: str
    artifact_name: str
    artifact_sha256: str
    theorem_ids: tuple[str, ...]
    toolchain_id: str
    tcb_digest: str
    basis_digest: str


@dataclass(frozen=True)
class CounterpressureAlphabet:
    version: str
    symbols: tuple[str, ...]
    alphabet_digest: str


@dataclass(frozen=True)
class LedgerRow:
    depth: int
    witness_label: str
    selector_label: str


@dataclass(frozen=True)
class NonuniformLedgerRequest:
    version: str
    rows: tuple[LedgerRow, ...]


@dataclass(frozen=True)
class DecreasingTreeRequest:
    version: str
    sample_depth: int
    basis: CounterpressureBasisSource


@dataclass(frozen=True)
class TargetChooserRequest:
    version: str
    alphabet: CounterpressureAlphabet
    target: tuple[str, ...]


@dataclass(frozen=True)
class LongRunRequest:
    version: str
    steps: int


@dataclass(frozen=True)
class ShrinkingStageRequest:
    version: str
    sample_index: int
    basis: CounterpressureBasisSource


CounterpressureRequest: TypeAlias = (
    NonuniformLedgerRequest | DecreasingTreeRequest | TargetChooserRequest |
    LongRunRequest | ShrinkingStageRequest
)


@dataclass(frozen=True)
class CounterpressurePolicy:
    version: str
    max_request_bytes: int
    max_symbolic_cost: int
    policy_digest: str


@dataclass(frozen=True)
class LedgerInsufficiencyEvidence:
    row_count: int
    depths: tuple[int, ...]
    selector_count: int
    common_source_supplied: bool
    status: CounterpressureStatus


@dataclass(frozen=True)
class DescentCountermodelEvidence:
    sample_depth: int
    witness_length: int
    first_or_none: int | None
    last_or_none: int | None
    witness_formula_digest: str
    basis_digest: str
    status: CounterpressureStatus


@dataclass(frozen=True)
class TargetDependenceEvidence:
    target_length: int
    target_digest: str
    output_digest: str
    exact_match: bool
    target_read: bool
    chooser_target_independence: ChooserTargetIndependence
    chooser_rule_id: str
    status: CounterpressureStatus


@dataclass(frozen=True)
class FiniteRunInsufficiencyEvidence:
    first_depth: int
    last_depth: int
    executed_count: int
    materialized: bool
    status: CounterpressureStatus


@dataclass(frozen=True)
class ShrinkingTailCountermodelEvidence:
    sample_index: int
    local_witness: int
    nested_from: int
    nested_into: int
    diagonal_candidate: int
    excluding_stage: int
    basis_digest: str
    status: CounterpressureStatus


CounterpressureEvidence: TypeAlias = (
    LedgerInsufficiencyEvidence | DescentCountermodelEvidence |
    TargetDependenceEvidence | FiniteRunInsufficiencyEvidence |
    ShrinkingTailCountermodelEvidence
)


@dataclass(frozen=True)
class CounterpressureCertificate:
    request_kind: CounterpressureRequestKind
    request_digest: str
    inference_id: CounterpressureInference
    outcome_kind: CounterpressureOutcomeKind
    status: CounterpressureStatus
    evidence: CounterpressureEvidence
    evidence_digest: str
    basis_use: BasisUse
    basis_digest: str | None
    policy_digest: str
    certificate_digest: str
    generator_nonexistence: GeneratorNonexistence = GeneratorNonexistence.NOT_PROVED
    all_depth_family: AllDepthFamilyStatus = AllDepthFamilyStatus.OPEN
    completed_carrier: CompletedCarrierStatus = CompletedCarrierStatus.NOT_ESTABLISHED
    historical_target_independence: HistoricalTargetIndependence = (
        HistoricalTargetIndependence.NOT_ESTABLISHED
    )
    scope: str = "counterpressure-only"


@dataclass(frozen=True)
class CounterpressureResourceLimit:
    request_kind: CounterpressureRequestKind
    request_digest: str
    failed_bound: CounterpressureResourceBound
    required_value: int
    allowed_value: int
    policy_digest: str
    refusal_digest: str
    generator_nonexistence: GeneratorNonexistence = GeneratorNonexistence.NOT_PROVED
    all_depth_family: AllDepthFamilyStatus = AllDepthFamilyStatus.OPEN
    completed_carrier: CompletedCarrierStatus = CompletedCarrierStatus.NOT_ESTABLISHED
    historical_target_independence: HistoricalTargetIndependence = (
        HistoricalTargetIndependence.NOT_ESTABLISHED
    )
    scope: str = "counterpressure-only"


CounterpressureResult: TypeAlias = CounterpressureCertificate | CounterpressureResourceLimit
