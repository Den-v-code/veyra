"""P2-S3 adjacent and category-error cast counterpressure matrix."""

from __future__ import annotations

import logging

from .status_promotion_digest import digest, text_rows
from .status_promotion_types import (
    CastAttack, CastAttackMatrixReport, CastAttackOutcome, CastAttackRow,
    JudgmentKind as K, MetaOntologicalStatus, PromotionRegistry,
)
from .status_promotion_validation import validate_registry

logger = logging.getLogger(__name__)

_ATTACK_ROWS = (
    ("presented-to-object", K.PRESENTED, K.SCOPED_OBJECT, "missing-sfp"),
    ("observation-to-role", K.OBSERVABLE, K.OBSERVER_ROLE, "response-is-not-role"),
    ("role-to-history", K.OBSERVER_ROLE, K.HISTORICALLY_ACTUALIZED, "missing-history"),
    ("role-to-physical", K.OBSERVER_ROLE, K.PHYSICALLY_INSTANTIATED, "missing-bridge"),
    ("generation-to-confluence", K.GENERABLE, K.CONFLUENT, "missing-paths"),
    ("cell-to-all-confluence", K.COHERENT, K.CONFLUENT, "one-cell-not-all-paths"),
    ("sample-to-robustness", K.PERSISTENT, K.REFINEMENT_ROBUST, "sample-not-network"),
    ("finite-to-all-depth", K.GENERABLE, K.ALL_DEPTH_FAMILY, "finite-not-totality"),
    ("family-to-carrier", K.ALL_DEPTH_FAMILY, K.COMPLETED_CARRIER, "missing-cip"),
    ("silence-to-refutation", K.OBSERVABLE, K.ADMISSIBLE, "silence-is-not-refutation"),
    ("higher-cast-down", K.SCOPED_OBJECT, K.GENERABLE, "missing-premise-projection"),
    ("qa-to-metaphysics", K.PRESENTED, K.PHYSICALLY_INSTANTIATED, "qa-is-not-ontology"),
)


def adjacent_cast_attack_matrix(registry: PromotionRegistry) -> CastAttackMatrixReport:
    """Prove the fixed twelve bare-status casts have no registry constructor."""
    logger.debug("adjacent_cast_attack_matrix entry")
    validate_registry(registry)
    rows = tuple(_attack_row(registry, *spec) for spec in _ATTACK_ROWS)
    value = digest("veyra.p2s.cast-attack-report.v1", (
        ("registry", registry.registry_digest.encode()),
        *text_rows("row", tuple(item.row_digest for item in rows)),
        ("ontology", MetaOntologicalStatus.NOT_CLAIMED.value.encode()),
    ))
    result = CastAttackMatrixReport(registry.registry_digest, rows, value)
    logger.debug("adjacent_cast_attack_matrix exit rows=%d", len(rows))
    return result


def _attack_row(
    registry: PromotionRegistry, attack_id: str, weaker: K, stronger: K, reason: str,
) -> CastAttackRow:
    logger.debug("_attack_row entry attack=%s", attack_id)
    attack_digest = digest("veyra.p2s.cast-attack.v1", (
        ("id", attack_id.encode()), ("weaker", weaker.value.encode()),
        ("stronger", stronger.value.encode()), ("reason", reason.encode()),
    ))
    attack = CastAttack(attack_id, weaker, stronger, reason, attack_digest)
    forbidden_kind = f"bare-{weaker.value}-status"
    count = sum(
        1 for rule in registry.rules
        if rule.output_kind is stronger
        and len(rule.premise_signatures) == 1
        and rule.premise_signatures[0].artifact_kind == forbidden_kind
    )
    if count != 0:
        raise AssertionError("bare-status-cast-entered-registry")
    row_digest = digest("veyra.p2s.cast-attack-row.v1", (
        ("attack", attack_digest.encode()),
        ("outcome", CastAttackOutcome.REJECTED.value.encode()),
        ("matching", count.to_bytes(8, "big")),
    ))
    result = CastAttackRow(attack, CastAttackOutcome.REJECTED, count, row_digest)
    logger.debug("_attack_row exit attack=%s", attack_id)
    return result
