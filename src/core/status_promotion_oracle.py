"""Independent literal-oracle audit for frozen P2-S generator output."""

from __future__ import annotations

from enum import Enum
from hashlib import sha256
import json
import logging

from .status_promotion_common import reject
from .status_promotion_oracle_data import (
    ORACLE_ASSUMPTION_POLICY_ID, ORACLE_DOMAIN_ROWS,
    ORACLE_FORBIDDEN_CONCLUSION_FIELDS, ORACLE_FORBIDDEN_SOURCE_TYPES,
    ORACLE_INDEX_PROJECTION, ORACLE_PREMISE_PROJECTION_TRIPLES,
    ORACLE_RULE_ROWS, ORACLE_STATEMENT_DIGESTS,
)
from .status_promotion_types import PromotionRegistry
from .status_promotion_validation import validate_registry

logger = logging.getLogger(__name__)
LITERAL_ORACLE_DIGEST = "2cbe0f2f1f1025696b947c73e32196f230e7748c77c030543d2292a34585875a"


def _plain(value):
    logger.debug("_plain entry type=%s", type(value).__name__)
    if isinstance(value, Enum):
        result = value.value
    elif type(value) is tuple:
        result = [_plain(item) for item in value]
    elif type(value) is str:
        result = value
    else:
        raise TypeError("literal-oracle-unexpected-type")
    logger.debug("_plain exit")
    return result


def compute_literal_oracle_digest() -> str:
    """Commit the separately written literal tables with stdlib canonical JSON."""
    logger.debug("compute_literal_oracle_digest entry")
    payload = {
        "domains": _plain(ORACLE_DOMAIN_ROWS),
        "rules": _plain(ORACLE_RULE_ROWS),
        "statement_digests": _plain(ORACLE_STATEMENT_DIGESTS),
        "forbidden_source_types": _plain(ORACLE_FORBIDDEN_SOURCE_TYPES),
        "forbidden_conclusion_fields": _plain(ORACLE_FORBIDDEN_CONCLUSION_FIELDS),
        "assumption_policy_id": ORACLE_ASSUMPTION_POLICY_ID,
        "premise_projections": _plain(ORACLE_PREMISE_PROJECTION_TRIPLES),
        "index_projection": _plain(ORACLE_INDEX_PROJECTION),
    }
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    result = sha256(encoded).hexdigest()
    logger.debug("compute_literal_oracle_digest exit digest=%s", result[:12])
    return result


def audit_registry_against_literal_oracle(registry: PromotionRegistry) -> str:
    """Reject any generated registry cell that differs from literal review data."""
    logger.debug("audit_registry_against_literal_oracle entry")
    validate_registry(registry)
    if compute_literal_oracle_digest() != LITERAL_ORACLE_DIGEST:
        reject("literal-oracle-digest-drift")
    if len(ORACLE_DOMAIN_ROWS) != 15 or len(ORACLE_RULE_ROWS) != 17:
        reject("literal-oracle-cardinality-drift")
    domains = tuple(
        (
            item.kind, item.allowed_statuses,
            tuple((pair.status, pair.provenance) for pair in item.positive_pairs),
        )
        for item in registry.domains
    )
    if domains != ORACLE_DOMAIN_ROWS:
        reject("registry-domain-oracle-mismatch")
    statement_ids = tuple(item[0] for item in ORACLE_STATEMENT_DIGESTS)
    if statement_ids != tuple(item[0] for item in ORACLE_RULE_ROWS):
        reject("literal-oracle-statement-order-drift")
    statement_digests = dict(ORACLE_STATEMENT_DIGESTS)
    expected_rules = tuple((
        row[0], statement_digests[row[0]], row[1], row[2], row[3], row[4], row[5],
        ORACLE_FORBIDDEN_SOURCE_TYPES, ORACLE_FORBIDDEN_CONCLUSION_FIELDS,
        ORACLE_ASSUMPTION_POLICY_ID, row[6],
    ) for row in ORACLE_RULE_ROWS)
    rules = tuple(
        (
            item.rule_id, item.statement_digest,
            tuple((
                premise.premise_name, premise.artifact_kind,
                premise.required_evidence_fields, premise.required_indices,
            ) for premise in item.premise_signatures),
            item.output_kind, item.output_status, item.output_provenance,
            item.output_indices, item.forbidden_source_types,
            item.forbidden_conclusion_fields, item.assumption_policy_id,
            item.permanent_nonclaims,
        )
        for item in registry.rules
    )
    if rules != expected_rules:
        reject("registry-rule-oracle-mismatch")
    triples = tuple(
        (item.projection_id, item.source_rule_id, item.premise_name)
        for item in registry.premise_projections
    )
    if (
        len(triples) != 40 or len(set(triples)) != 40
        or len({item[0] for item in triples}) != 40
        or triples != ORACLE_PREMISE_PROJECTION_TRIPLES
    ):
        reject("registry-premise-projection-oracle-mismatch")
    if len(registry.index_projections) != 1:
        reject("registry-index-projection-count-mismatch")
    item = registry.index_projections[0]
    actual_index = (
        item.projection_id, item.kind, item.input_indices,
        item.hidden_index, item.retained_indices,
    )
    if actual_index != ORACLE_INDEX_PROJECTION:
        reject("registry-index-projection-oracle-mismatch")
    logger.debug("audit_registry_against_literal_oracle exit")
    return LITERAL_ORACLE_DIGEST
