"""Source binding for residue-aware P3-OG semantic tick laws."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest

from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    MaintenanceCreditClass,
    P3OGAutonomousTickSource,
)
from .prime_power_observer_genesis_p3og_codec import canonical_bytes
from .prime_power_observer_genesis_p3og_residue_aware_tick_codec import (
    residue_aware_tick_digest,
)
from .prime_power_observer_genesis_p3og_residue_aware_tick_types import (
    P3OGResidueAwareTickSource,
    ResidueAwareTickRule,
    ResiduePresenceClass,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_runtime import (
    validate_semantic_configuration_contract,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfigurationContract,
)
from .prime_power_observer_genesis_p3og_types import (
    MaintenanceControlState,
    P3OGSource,
    TransitionKind,
)

SOURCE_VERSION = "p3og-residue-aware-tick-source-v2"
RULE_ID = "maintenance-credit-residue-presence-feedback-table-v2"
ABSENT_KERNEL_RULE_ID = "absent-rows-exactly-equal-base-autonomous-v1"
_EXPECTED_KEYS = frozenset(
    (control, credit_class, residue_class)
    for control in MaintenanceControlState
    for credit_class in MaintenanceCreditClass
    for residue_class in ResiduePresenceClass
)


def residue_aware_tick_rule(
    maintenance_control: MaintenanceControlState,
    credit_class: MaintenanceCreditClass,
    residue_class: ResiduePresenceClass,
    transition_kind: TransitionKind,
) -> ResidueAwareTickRule:
    if type(maintenance_control) is not MaintenanceControlState:
        raise ValueError("p3og-residue-aware-tick-maintenance-control")
    if type(credit_class) is not MaintenanceCreditClass:
        raise ValueError("p3og-residue-aware-tick-credit-class")
    if type(residue_class) is not ResiduePresenceClass:
        raise ValueError("p3og-residue-aware-tick-residue-class")
    if type(transition_kind) is not TransitionKind:
        raise ValueError("p3og-residue-aware-tick-transition-kind")
    return ResidueAwareTickRule(
        maintenance_control,
        credit_class,
        residue_class,
        transition_kind,
    )


def _canonical_rules(
    base_autonomous_source: P3OGAutonomousTickSource,
    rules: tuple[ResidueAwareTickRule, ...],
) -> tuple[ResidueAwareTickRule, ...]:
    if type(rules) is not tuple or len(rules) != len(_EXPECTED_KEYS):
        raise ValueError("p3og-residue-aware-tick-rules")
    checked: list[ResidueAwareTickRule] = []
    for rule in rules:
        if type(rule) is not ResidueAwareTickRule:
            raise ValueError("p3og-residue-aware-tick-rule-type")
        checked.append(
            residue_aware_tick_rule(
                rule.maintenance_control,
                rule.credit_class,
                rule.residue_class,
                rule.transition_kind,
            ),
        )
    keys = {
        (rule.maintenance_control, rule.credit_class, rule.residue_class)
        for rule in checked
    }
    if keys != _EXPECTED_KEYS or len(keys) != len(checked):
        raise ValueError("p3og-residue-aware-tick-rule-coverage")

    base = {
        (rule.maintenance_control, rule.credit_class): rule.transition_kind
        for rule in base_autonomous_source.rules
    }
    for rule in checked:
        if (
            rule.residue_class is ResiduePresenceClass.ABSENT
            and base[(rule.maintenance_control, rule.credit_class)]
            is not rule.transition_kind
        ):
            raise ValueError("p3og-residue-aware-tick-absent-kernel-drift")
    return tuple(
        sorted(
            checked,
            key=lambda rule: (
                rule.maintenance_control.value,
                rule.credit_class.value,
                rule.residue_class.value,
            ),
        ),
    )


def p3og_residue_aware_tick_source(
    source: P3OGSource,
    base_autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    rules: tuple[ResidueAwareTickRule, ...],
) -> P3OGResidueAwareTickSource:
    """Commit one residue-aware extension without changing the absent-residue kernel."""
    source, base_autonomous_source, semantic_contract = (
        validate_semantic_configuration_contract(
            source,
            base_autonomous_source,
            semantic_contract,
        )
    )
    canonical_rules = _canonical_rules(base_autonomous_source, rules)
    fields = (
        SOURCE_VERSION,
        source.source_digest,
        base_autonomous_source.source_digest,
        semantic_contract.contract_digest,
        canonical_rules,
        RULE_ID,
        ABSENT_KERNEL_RULE_ID,
    )
    return P3OGResidueAwareTickSource(
        *fields,
        residue_aware_tick_digest("residue-aware-tick-source", *fields),
    )


def validate_residue_aware_tick_source(
    source: P3OGSource,
    base_autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    residue_aware_source: P3OGResidueAwareTickSource,
) -> tuple[
    P3OGSource,
    P3OGAutonomousTickSource,
    P3OGSemanticConfigurationContract,
    P3OGResidueAwareTickSource,
]:
    if type(residue_aware_source) is not P3OGResidueAwareTickSource:
        raise ValueError("p3og-residue-aware-tick-source-type")
    source, base_autonomous_source, semantic_contract = (
        validate_semantic_configuration_contract(
            source,
            base_autonomous_source,
            semantic_contract,
        )
    )
    try:
        expected = p3og_residue_aware_tick_source(
            source,
            base_autonomous_source,
            semantic_contract,
            residue_aware_source.rules,
        )
        equal = compare_digest(
            canonical_bytes(residue_aware_source),
            canonical_bytes(expected),
        )
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-residue-aware-tick-source-malformed") from exc
    if not equal:
        raise ValueError("p3og-residue-aware-tick-source-drift")
    return source, base_autonomous_source, semantic_contract, replace(expected)
