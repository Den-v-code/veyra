"""Source binding for bounded P3-OG state-extensional autonomous tick laws."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest
import logging

from .prime_power_observer_genesis_p3og_autonomous_tick_codec import (
    autonomous_tick_digest,
)
from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    AutonomousTickRule,
    MaintenanceCreditClass,
    P3OGAutonomousTickSource,
)
from .prime_power_observer_genesis_p3og_codec import canonical_bytes
from .prime_power_observer_genesis_p3og_source import validate_source
from .prime_power_observer_genesis_p3og_types import (
    MaintenanceControlState,
    P3OGSource,
    TransitionKind,
)

logger = logging.getLogger(__name__)
AUTONOMOUS_TICK_SOURCE_VERSION = "p3og-autonomous-tick-source-v1"
AUTONOMOUS_TICK_RULE_ID = "maintenance-credit-feedback-table-v1"
PROJECTION_RULE_ID = "exact-machine-configuration-minus-counter-and-digest-v1"
PROJECTION_EXCLUDED_FIELDS = ("transition_count", "state_digest")
CLOSURE_RULE_ID = "least-exact-configuration-return-after-genuine-departure-v1"
_EXPECTED_KEYS = frozenset(
    (control, credit_class)
    for control in MaintenanceControlState
    for credit_class in MaintenanceCreditClass
)


def autonomous_tick_rule(
    maintenance_control: MaintenanceControlState,
    credit_class: MaintenanceCreditClass,
    transition_kind: TransitionKind,
) -> AutonomousTickRule:
    """Build one exact row of the state-feedback table."""
    if type(maintenance_control) is not MaintenanceControlState:
        raise ValueError("p3og-autonomous-tick-maintenance-control")
    if type(credit_class) is not MaintenanceCreditClass:
        raise ValueError("p3og-autonomous-tick-credit-class")
    if type(transition_kind) is not TransitionKind:
        raise ValueError("p3og-autonomous-tick-transition-kind")
    return AutonomousTickRule(
        maintenance_control,
        credit_class,
        transition_kind,
    )


def _canonical_rules(
    rules: tuple[AutonomousTickRule, ...],
) -> tuple[AutonomousTickRule, ...]:
    """Require one and only one row for every supported live-state partition."""
    if type(rules) is not tuple or len(rules) != len(_EXPECTED_KEYS):
        raise ValueError("p3og-autonomous-tick-rules")
    checked: list[AutonomousTickRule] = []
    for rule in rules:
        if type(rule) is not AutonomousTickRule:
            raise ValueError("p3og-autonomous-tick-rule-type")
        checked.append(
            autonomous_tick_rule(
                rule.maintenance_control,
                rule.credit_class,
                rule.transition_kind,
            ),
        )
    keys = {(rule.maintenance_control, rule.credit_class) for rule in checked}
    if keys != _EXPECTED_KEYS or len(keys) != len(checked):
        raise ValueError("p3og-autonomous-tick-rule-coverage")
    return tuple(
        sorted(
            checked,
            key=lambda rule: (
                rule.maintenance_control.value,
                rule.credit_class.value,
            ),
        ),
    )


def p3og_autonomous_tick_source(
    source: P3OGSource,
    rules: tuple[AutonomousTickRule, ...],
) -> P3OGAutonomousTickSource:
    """Commit a total state-feedback transition law before any run result."""
    logger.debug("p3og.autonomous_tick.source entry")
    source = validate_source(source)
    canonical_rules = _canonical_rules(rules)
    fields = (
        AUTONOMOUS_TICK_SOURCE_VERSION,
        source.source_digest,
        canonical_rules,
        AUTONOMOUS_TICK_RULE_ID,
        PROJECTION_RULE_ID,
        PROJECTION_EXCLUDED_FIELDS,
        CLOSURE_RULE_ID,
    )
    result = P3OGAutonomousTickSource(
        *fields,
        autonomous_tick_digest("autonomous-tick-source", *fields),
    )
    logger.debug(
        "p3og.autonomous_tick.source exit source=%s",
        result.source_digest[:12],
    )
    return result


def validate_autonomous_tick_source(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
) -> tuple[P3OGSource, P3OGAutonomousTickSource]:
    """Freshly reconstruct the exact source-bound autonomous law."""
    logger.debug("p3og.autonomous_tick.validate_source entry")
    source = validate_source(source)
    if type(autonomous_source) is not P3OGAutonomousTickSource:
        raise ValueError("p3og-autonomous-tick-source-type")
    try:
        if autonomous_source.pressure_source_digest != source.source_digest:
            raise ValueError("p3og-autonomous-tick-source-pressure")
        expected = p3og_autonomous_tick_source(source, autonomous_source.rules)
        equal = compare_digest(
            canonical_bytes(autonomous_source),
            canonical_bytes(expected),
        )
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        logger.error("p3og.autonomous_tick.validate_source malformed")
        raise ValueError("p3og-autonomous-tick-source-malformed") from exc
    if not equal:
        raise ValueError("p3og-autonomous-tick-source-drift")
    logger.debug("p3og.autonomous_tick.validate_source exit")
    return source, replace(expected)
