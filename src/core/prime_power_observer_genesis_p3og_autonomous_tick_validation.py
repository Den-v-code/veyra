"""Fresh replay validation for bounded P3-OG autonomous-tick evidence."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest
import logging

from .prime_power_observer_genesis_p3og_autonomous_tick_runtime import (
    _run_p3og_autonomous_first_closure_validated,
)
from .prime_power_observer_genesis_p3og_autonomous_tick_source import (
    validate_autonomous_tick_source,
)
from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    P3OGAutonomousFirstClosureEvidence,
    P3OGAutonomousTickSource,
)
from .prime_power_observer_genesis_p3og_codec import evidence_bytes
from .prime_power_observer_genesis_p3og_types import P3OGSource

logger = logging.getLogger(__name__)


def validate_p3og_autonomous_first_closure_evidence(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    evidence: P3OGAutonomousFirstClosureEvidence,
) -> P3OGAutonomousFirstClosureEvidence:
    """Freshly reconstruct the complete autonomous genealogy and exact verdict."""
    logger.debug("p3og.autonomous_tick.validate_evidence entry")
    source, autonomous_source = validate_autonomous_tick_source(
        source,
        autonomous_source,
    )
    if type(evidence) is not P3OGAutonomousFirstClosureEvidence:
        raise ValueError("p3og-autonomous-first-closure-evidence-type")
    try:
        expected = _run_p3og_autonomous_first_closure_validated(
            source,
            autonomous_source,
        )
        equal = compare_digest(
            evidence_bytes(evidence),
            evidence_bytes(expected),
        )
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        logger.error("p3og.autonomous_tick.validate_evidence malformed")
        raise ValueError("p3og-autonomous-first-closure-evidence-malformed") from exc
    if not equal:
        raise ValueError("p3og-autonomous-first-closure-evidence-drift")
    logger.debug("p3og.autonomous_tick.validate_evidence exit")
    return replace(expected)
