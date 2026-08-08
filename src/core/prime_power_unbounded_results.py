"""Lane-closed raw and sealed owned positive records for P3-N6."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import cast

from .prime_power_unbounded_common import (
    digest, exact_digest, exact_nonnegative_int, exact_shape, exact_text,
    exact_text_tuple, freeze_layout, reject,
)
from .prime_power_unbounded_sources import (
    EQUALITY_DEFINITION_ID, POWER_MAP_DEFINITION_ID,
)
from .prime_power_unbounded_ledger import (
    EQUALITY_ADAPTER_THEOREM_ID, INJECTION_THEOREM_IDS,
)
from .prime_power_unbounded_types import N6Kind, N6Status, N6_NONCLAIMS

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PPEqualityAdapterRawV1:
    """Unowned adapter fields; this record establishes nothing."""

    pomega2_package_digest: str
    doctrine_digest: str
    carrier_id: str
    equality_id: str
    equality_definition_id: str
    theorem_source_digest: str
    proof_id: str
    adapter_digest: str


@dataclass(frozen=True, slots=True)
class PowerInjectionEvidenceRawV1:
    """Unowned evidence fields; only the derivation may own them."""

    prime_digest: str
    pomega2_package_digest: str
    n1_zero_package_digest: str
    pomega2_judgment_digest: str
    n1_zero_judgment_digest: str
    pomega2_theorem_source_digest: str
    n1_theorem_source_digest: str
    doctrine_digest: str
    carrier_id: str
    equality_id: str
    theorem_source_digest: str
    ledger_digest: str
    launcher_attestation_digest: str
    formal_run_digest: str
    equality_adapter_digest: str
    power_map_definition_id: str
    proof_ids: tuple[str, ...]
    theorem_axiom_closure: tuple[str, ...]
    evidence_digest: str


@dataclass(frozen=True, slots=True)
class PowerInjectionJudgmentRawV1:
    """Unowned positive fields without an ESTABLISHED status."""

    kind: N6Kind
    request_digest: str
    evidence: PowerInjectionEvidenceRawV1
    map_domain: str
    map_definition_id: str
    carrier_id: str
    equality_id: str
    promotions: int
    nonclaims: tuple[str, ...]
    judgment_digest: str


_ADAPTER_RAW_LAYOUT = freeze_layout(PPEqualityAdapterRawV1, (
    "pomega2_package_digest", "doctrine_digest", "carrier_id", "equality_id",
    "equality_definition_id", "theorem_source_digest", "proof_id", "adapter_digest",
))
_EVIDENCE_RAW_LAYOUT = freeze_layout(PowerInjectionEvidenceRawV1, (
    "prime_digest", "pomega2_package_digest", "n1_zero_package_digest",
    "pomega2_judgment_digest", "n1_zero_judgment_digest",
    "pomega2_theorem_source_digest", "n1_theorem_source_digest",
    "doctrine_digest", "carrier_id", "equality_id",
    "theorem_source_digest", "ledger_digest", "launcher_attestation_digest",
    "formal_run_digest", "equality_adapter_digest",
    "power_map_definition_id", "proof_ids", "theorem_axiom_closure", "evidence_digest",
))
_JUDGMENT_RAW_LAYOUT = freeze_layout(PowerInjectionJudgmentRawV1, (
    "kind", "request_digest", "evidence", "map_domain", "map_definition_id",
    "carrier_id", "equality_id", "promotions", "nonclaims", "judgment_digest",
))


def _adapter_digest(raw: PPEqualityAdapterRawV1) -> str:
    """Recompute the exact equality-adapter transcript."""
    logger.debug("_adapter_digest entry")
    result = digest("veyra.p3n6.equality-adapter.v1", (
        ("pomega2", raw.pomega2_package_digest.encode()),
        ("doctrine", raw.doctrine_digest.encode()), ("carrier", raw.carrier_id.encode()),
        ("equality", raw.equality_id.encode()),
        ("equality-definition", raw.equality_definition_id.encode()),
        ("theorem-source", raw.theorem_source_digest.encode()),
        ("proof", raw.proof_id.encode()),
    ))
    logger.debug("_adapter_digest exit")
    return result


def _validate_adapter(raw: object) -> PPEqualityAdapterRawV1:
    """Freshly validate and recompute every adapter field."""
    logger.debug("_validate_adapter entry")
    exact_shape(raw, _ADAPTER_RAW_LAYOUT, "n6-adapter-raw")
    raw = cast(PPEqualityAdapterRawV1, raw)
    for label, value in (
        ("pomega2", raw.pomega2_package_digest), ("doctrine", raw.doctrine_digest),
        ("theorem", raw.theorem_source_digest), ("adapter", raw.adapter_digest),
    ):
        exact_digest(value, f"n6-adapter-{label}")
    for label, value in (("carrier", raw.carrier_id), ("equality", raw.equality_id)):
        exact_text(value, f"n6-adapter-{label}")
    if (raw.equality_definition_id != EQUALITY_DEFINITION_ID
            or raw.proof_id != EQUALITY_ADAPTER_THEOREM_ID):
        reject("n6-adapter-definition-or-proof-invalid")
    if _adapter_digest(raw) != raw.adapter_digest:
        reject("n6-adapter-digest-drift")
    logger.debug("_validate_adapter exit")
    return raw


def _evidence_digest(raw: PowerInjectionEvidenceRawV1) -> str:
    """Recompute the exact power-injection evidence transcript."""
    logger.debug("_evidence_digest entry")
    rows = (
        ("prime", raw.prime_digest.encode()), ("pomega2", raw.pomega2_package_digest.encode()),
        ("n1-zero", raw.n1_zero_package_digest.encode()),
        ("pomega2-judgment", raw.pomega2_judgment_digest.encode()),
        ("n1-zero-judgment", raw.n1_zero_judgment_digest.encode()),
        ("pomega2-theorem", raw.pomega2_theorem_source_digest.encode()),
        ("n1-theorem", raw.n1_theorem_source_digest.encode()),
        ("doctrine", raw.doctrine_digest.encode()),
        ("carrier", raw.carrier_id.encode()), ("equality", raw.equality_id.encode()),
        ("theorem-source", raw.theorem_source_digest.encode()),
        ("ledger", raw.ledger_digest.encode()),
        ("launcher-attestation", raw.launcher_attestation_digest.encode()),
        ("formal-run", raw.formal_run_digest.encode()),
        ("adapter", raw.equality_adapter_digest.encode()),
        ("power-map", raw.power_map_definition_id.encode()),
        *((f"proof-{index}", item.encode()) for index, item in enumerate(raw.proof_ids)),
        *((f"axiom-{index}", item.encode()) for index, item in enumerate(raw.theorem_axiom_closure)),
    )
    result = digest("veyra.p3n6.power-injection-evidence.v1", rows)
    logger.debug("_evidence_digest exit")
    return result


def _validate_evidence(raw: object) -> PowerInjectionEvidenceRawV1:
    """Freshly validate and recompute every evidence field."""
    logger.debug("_validate_evidence entry")
    exact_shape(raw, _EVIDENCE_RAW_LAYOUT, "n6-evidence-raw")
    raw = cast(PowerInjectionEvidenceRawV1, raw)
    for label, value in (
        ("prime", raw.prime_digest), ("pomega2", raw.pomega2_package_digest),
        ("n1-zero", raw.n1_zero_package_digest), ("theorem", raw.theorem_source_digest),
        ("pomega2-judgment", raw.pomega2_judgment_digest),
        ("n1-zero-judgment", raw.n1_zero_judgment_digest),
        ("pomega2-theorem", raw.pomega2_theorem_source_digest),
        ("n1-theorem", raw.n1_theorem_source_digest),
        ("doctrine", raw.doctrine_digest),
        ("ledger", raw.ledger_digest),
        ("launcher-attestation", raw.launcher_attestation_digest),
        ("formal-run", raw.formal_run_digest),
        ("adapter", raw.equality_adapter_digest),
        ("evidence", raw.evidence_digest),
    ):
        exact_digest(value, f"n6-evidence-{label}")
    proofs = exact_text_tuple(raw.proof_ids, "n6-evidence-proofs", maximum_items=2)
    axioms = exact_text_tuple(raw.theorem_axiom_closure, "n6-evidence-axioms", maximum_items=1)
    for label, value in (("carrier", raw.carrier_id), ("equality", raw.equality_id)):
        exact_text(value, f"n6-evidence-{label}")
    if (raw.power_map_definition_id != POWER_MAP_DEFINITION_ID
            or proofs != INJECTION_THEOREM_IDS or axioms != ("propext",)):
        reject("n6-evidence-theorem-boundary-invalid")
    if _evidence_digest(raw) != raw.evidence_digest:
        reject("n6-evidence-digest-drift")
    logger.debug("_validate_evidence exit")
    return raw


def _judgment_digest(raw: PowerInjectionJudgmentRawV1) -> str:
    """Recompute the exact established-judgment transcript."""
    logger.debug("_judgment_digest entry")
    result = digest("veyra.p3n6.power-injection-judgment.v1", (
        ("kind", raw.kind.value.encode()), ("request", raw.request_digest.encode()),
        ("evidence", raw.evidence.evidence_digest.encode()),
        ("map-domain", raw.map_domain.encode()), ("map", raw.map_definition_id.encode()),
        ("carrier", raw.carrier_id.encode()), ("equality", raw.equality_id.encode()),
        ("promotions", raw.promotions.to_bytes(8, "big")),
        *((f"nonclaim-{index}", item.encode()) for index, item in enumerate(raw.nonclaims)),
    ))
    logger.debug("_judgment_digest exit")
    return result


def _validate_judgment(raw: object, evidence: PowerInjectionEvidenceRawV1) -> PowerInjectionJudgmentRawV1:
    """Freshly validate exact endpoints, evidence identity and judgment digest."""
    logger.debug("_validate_judgment entry")
    fields = exact_shape(raw, _JUDGMENT_RAW_LAYOUT, "n6-judgment-raw")
    raw = cast(PowerInjectionJudgmentRawV1, raw)
    checked_evidence = _validate_evidence(evidence)
    if fields["evidence"] is not checked_evidence:
        reject("n6-judgment-raw-or-evidence-invalid")
    if raw.kind is not N6Kind.POWER_INJECTION_RELATIVE_TO_EXACT_POMEGA2:
        reject("n6-judgment-kind-invalid")
    exact_digest(raw.request_digest, "n6-judgment-request")
    exact_digest(raw.judgment_digest, "n6-judgment")
    exact_nonnegative_int(raw.promotions, "n6-judgment-promotions", maximum=0)
    nonclaims = exact_text_tuple(raw.nonclaims, "n6-judgment-nonclaims", maximum_items=len(N6_NONCLAIMS))
    for label, value in (("carrier", raw.carrier_id), ("equality", raw.equality_id)):
        exact_text(value, f"n6-judgment-{label}")
    if (raw.map_domain != "Nat"
            or raw.map_definition_id != POWER_MAP_DEFINITION_ID
            or raw.carrier_id != evidence.carrier_id
            or raw.equality_id != evidence.equality_id
            or nonclaims != N6_NONCLAIMS):
        reject("n6-judgment-map-or-nonclaims-invalid")
    if _judgment_digest(raw) != raw.judgment_digest:
        reject("n6-judgment-digest-drift")
    logger.debug("_validate_judgment exit")
    return raw


@dataclass(frozen=True, init=False, slots=True)
class PPEqualityAdapterV1:
    """Owned adapter inhabited only inside the checked E derivation."""

    raw: PPEqualityAdapterRawV1

    def __init__(self, _raw: object) -> None:
        logger.debug("PPEqualityAdapterV1 init entry")
        reject("n6-owned-adapter-constructor-forbidden")


@dataclass(frozen=True, init=False, slots=True)
class PowerInjectionEvidenceV1:
    """Owned evidence inhabited only after fresh formal/dependency replay."""

    raw: PowerInjectionEvidenceRawV1
    adapter: PPEqualityAdapterV1

    def __init__(self, _raw: object) -> None:
        logger.debug("PowerInjectionEvidenceV1 init entry")
        reject("n6-owned-evidence-constructor-forbidden")


@dataclass(frozen=True, init=False, slots=True)
class PowerInjectionJudgmentV1:
    """Owned ESTABLISHED result; callers validate it through validate_e_result."""

    status: N6Status
    raw: PowerInjectionJudgmentRawV1
    evidence: PowerInjectionEvidenceV1

    def __init__(self, _raw: object, _evidence: object = None) -> None:
        logger.debug("PowerInjectionJudgmentV1 init entry")
        reject("n6-owned-judgment-constructor-forbidden")
