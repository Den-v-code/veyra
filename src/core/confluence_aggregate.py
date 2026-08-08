"""Public P1-C2 declared finite confluence aggregation API."""

from __future__ import annotations

import logging

from .confluence_aggregate_history import declared_history, identity_history
from .confluence_aggregate_request import (
    confluence_aggregate_policy, finite_confluence_catalog,
    global_path_pair_requirement, local_critical_fork_requirement,
)
from .confluence_aggregate_result_validation import validate_finite_confluence_result
from .confluence_aggregate_runtime import finite_confluence_aggregate
from .confluence_aggregate_types import (
    AggregateCoverageStatus, AggregateFailedBound, AggregateResultStatus,
    C2_NONCLAIMS, ConfluenceAggregatePolicy, ConfluenceAggregateResourceLimit,
    ConfluenceRequirementRow, DeclaredHistory, FiniteConfluenceAggregate,
    FiniteConfluenceCatalogSource, FiniteConfluenceResult,
    GlobalDeclaredFiniteStatus, GlobalHistory2CellArtifact,
    GlobalPathPairRequirement, IdentityHistory, LocalCriticalForkRequirement,
    LocalFiniteStatus, RequirementKind,
)

logger = logging.getLogger(__name__)


def confluence_aggregate_scope_boundary() -> tuple[str, ...]:
    """Expose exact permanent nonclaims without promoting the finite catalog."""
    logger.debug("confluence_aggregate_scope_boundary entry")
    result = C2_NONCLAIMS
    logger.debug("confluence_aggregate_scope_boundary exit rows=%d", len(result))
    return result


__all__ = [
    "AggregateCoverageStatus", "AggregateFailedBound", "AggregateResultStatus",
    "C2_NONCLAIMS", "ConfluenceAggregatePolicy", "ConfluenceAggregateResourceLimit",
    "ConfluenceRequirementRow", "DeclaredHistory", "FiniteConfluenceAggregate",
    "FiniteConfluenceCatalogSource", "FiniteConfluenceResult",
    "GlobalDeclaredFiniteStatus", "GlobalHistory2CellArtifact",
    "GlobalPathPairRequirement", "IdentityHistory", "LocalCriticalForkRequirement",
    "LocalFiniteStatus", "RequirementKind", "confluence_aggregate_policy",
    "confluence_aggregate_scope_boundary", "declared_history",
    "finite_confluence_aggregate", "finite_confluence_catalog",
    "global_path_pair_requirement", "identity_history",
    "local_critical_fork_requirement", "validate_finite_confluence_result",
]
