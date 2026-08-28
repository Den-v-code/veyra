"""Selection-free typed maintenance ablation over the finite P3-OG Q_sem carrier."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest

from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    P3OGAutonomousTickSource,
)
from .prime_power_observer_genesis_p3og_codec import canonical_bytes
from .prime_power_observer_genesis_p3og_semantic_ablation_codec import (
    semantic_ablation_digest,
)
from .prime_power_observer_genesis_p3og_semantic_ablation_types import (
    P3OGSemanticAblationContract,
    SemanticAblationReceipt,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_codec import (
    semantic_configuration_digest,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_runtime import (
    semantic_read,
    validate_semantic_configuration,
    validate_semantic_configuration_contract,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfiguration,
    P3OGSemanticConfigurationContract,
)
from .prime_power_observer_genesis_p3og_source import validate_seed
from .prime_power_observer_genesis_p3og_types import (
    BoundaryState,
    MaintenanceControlState,
    P3OGSource,
    PrimitiveModeSeed,
)

CONTRACT_VERSION = "p3og-semantic-ablation-contract-v1"
COMPONENT_ID = "maintenance-control-v1"
ABLATION_RULE_ID = "disable-maintenance-control-preserve-other-q-sem-fields-v1"
UNCHANGED_FIELDS = (
    "run_id",
    "seed_digest",
    "boundary",
    "phase",
    "retained_residue",
    "maintenance_credit",
)


def p3og_semantic_ablation_contract(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
) -> P3OGSemanticAblationContract:
    """Commit the one allowed Q_sem maintenance ablation before selection."""
    source, autonomous_source, semantic_contract = (
        validate_semantic_configuration_contract(
            source,
            autonomous_source,
            semantic_contract,
        )
    )
    fields = (
        CONTRACT_VERSION,
        source.source_digest,
        autonomous_source.source_digest,
        semantic_contract.contract_digest,
        COMPONENT_ID,
        ABLATION_RULE_ID,
        UNCHANGED_FIELDS,
    )
    return P3OGSemanticAblationContract(
        *fields,
        semantic_ablation_digest("semantic-ablation-contract", *fields),
    )


def validate_semantic_ablation_contract(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    ablation_contract: P3OGSemanticAblationContract,
) -> tuple[
    P3OGSource,
    P3OGAutonomousTickSource,
    P3OGSemanticConfigurationContract,
    P3OGSemanticAblationContract,
]:
    if type(ablation_contract) is not P3OGSemanticAblationContract:
        raise ValueError("p3og-semantic-ablation-contract-type")
    try:
        expected = p3og_semantic_ablation_contract(
            source,
            autonomous_source,
            semantic_contract,
        )
        equal = compare_digest(
            canonical_bytes(ablation_contract),
            canonical_bytes(expected),
        )
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-semantic-ablation-contract-malformed") from exc
    if not equal:
        raise ValueError("p3og-semantic-ablation-contract-drift")
    source, autonomous_source, semantic_contract = (
        validate_semantic_configuration_contract(
            source,
            autonomous_source,
            semantic_contract,
        )
    )
    return source, autonomous_source, semantic_contract, replace(expected)


def _unchanged_values(configuration: P3OGSemanticConfiguration) -> tuple[object, ...]:
    return (
        configuration.run_id,
        configuration.seed_digest,
        configuration.boundary,
        configuration.phase,
        configuration.retained_residue,
        configuration.maintenance_credit,
    )


def semantic_ablate_maintenance(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    ablation_contract: P3OGSemanticAblationContract,
    seed: PrimitiveModeSeed,
    configuration: P3OGSemanticConfiguration,
) -> tuple[P3OGSemanticConfiguration, SemanticAblationReceipt]:
    """Disable exactly the named maintenance component in one live active Q_sem."""
    source, _, _, ablation_contract = validate_semantic_ablation_contract(
        source,
        autonomous_source,
        semantic_contract,
        ablation_contract,
    )
    source, seed = validate_seed(source, seed)
    source, seed, configuration = validate_semantic_configuration(
        source,
        seed,
        configuration,
    )
    if configuration.boundary is not BoundaryState.ALIVE:
        raise ValueError("p3og-semantic-ablation-requires-live-boundary")
    if configuration.maintenance_control is not MaintenanceControlState.ACTIVE:
        raise ValueError("p3og-semantic-ablation-requires-active-component")

    before_read = semantic_read(source, seed, configuration)
    after_fields = (
        configuration.run_id,
        configuration.seed_digest,
        configuration.boundary,
        MaintenanceControlState.DISABLED,
        configuration.phase,
        configuration.retained_residue,
        configuration.maintenance_credit,
    )
    after = P3OGSemanticConfiguration(
        *after_fields,
        semantic_configuration_digest("semantic-configuration", *after_fields),
    )
    _, _, after = validate_semantic_configuration(source, seed, after)
    after_read = semantic_read(source, seed, after)
    if before_read != after_read:
        raise ValueError("p3og-semantic-ablation-direct-read-overwrite")

    before_unchanged = _unchanged_values(configuration)
    after_unchanged = _unchanged_values(after)
    if before_unchanged != after_unchanged:
        raise ValueError("p3og-semantic-ablation-unrelated-state-drift")
    unchanged_digest = semantic_ablation_digest(
        "semantic-ablation-unchanged-fields",
        ablation_contract.unchanged_fields,
        before_unchanged,
    )
    receipt_fields = (
        ablation_contract.component_id,
        configuration.configuration_digest,
        after.configuration_digest,
        unchanged_digest,
        before_read,
        after_read,
    )
    receipt = SemanticAblationReceipt(
        *receipt_fields,
        semantic_ablation_digest("semantic-ablation-receipt", *receipt_fields),
    )
    return after, receipt


def validate_semantic_ablation_result(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    ablation_contract: P3OGSemanticAblationContract,
    seed: PrimitiveModeSeed,
    before: P3OGSemanticConfiguration,
    after: P3OGSemanticConfiguration,
    receipt: SemanticAblationReceipt,
) -> tuple[P3OGSemanticConfiguration, SemanticAblationReceipt]:
    """Freshly replay one ablation and reject any result/receipt drift."""
    if type(after) is not P3OGSemanticConfiguration:
        raise ValueError("p3og-semantic-ablation-after-type")
    if type(receipt) is not SemanticAblationReceipt:
        raise ValueError("p3og-semantic-ablation-receipt-type")
    try:
        expected_after, expected_receipt = semantic_ablate_maintenance(
            source,
            autonomous_source,
            semantic_contract,
            ablation_contract,
            seed,
            before,
        )
        equal = compare_digest(
            canonical_bytes((after, receipt)),
            canonical_bytes((expected_after, expected_receipt)),
        )
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-semantic-ablation-result-malformed") from exc
    if not equal:
        raise ValueError("p3og-semantic-ablation-result-drift")
    return replace(expected_after), replace(expected_receipt)
