"""Exact premise-projection commitment for P2-S elimination rules."""

from __future__ import annotations

import logging

from .status_promotion_common import exact_identifier
from .status_promotion_digest import digest

logger = logging.getLogger(__name__)


def premise_projection_digest(
    projection_id: str, source_rule_id: str, premise_name: str,
) -> str:
    """Bind the public projection name together with its exact source pair."""
    logger.debug("premise_projection_digest entry projection=%s", projection_id)
    projection_id = exact_identifier(projection_id, "projection-id")
    source_rule_id = exact_identifier(source_rule_id, "source-rule-id")
    premise_name = exact_identifier(premise_name, "premise-name")
    result = digest("veyra.p2s.premise-projection-rule.v1", (
        ("projection-id", projection_id.encode()),
        ("rule", source_rule_id.encode()),
        ("premise", premise_name.encode()),
    ))
    logger.debug("premise_projection_digest exit")
    return result
