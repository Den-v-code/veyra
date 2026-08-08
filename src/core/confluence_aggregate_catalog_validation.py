"""Deep catalog revalidation for P1-C2 raw replay boundaries."""

from __future__ import annotations

import logging

from .confluence_aggregate_request import (
    CATALOG_SCOPE, CATALOG_VERSION, finite_confluence_catalog,
)
from .confluence_aggregate_types import FiniteConfluenceCatalogSource, RequirementKind
from .confluence_preflight import ConfluenceValidationError
from .confluence_types import FiniteDiagramSource
from .confluence_validation import _hex_digest
from .positive_ontology_types import ObserverDoctrine

logger = logging.getLogger(__name__)


def _reject(reason: str) -> None:
    logger.error("aggregate catalog rejected reason=%s", reason)
    raise ConfluenceValidationError(reason)


def snapshot_finite_confluence_catalog(
    value: FiniteConfluenceCatalogSource, doctrine: ObserverDoctrine,
    diagram: FiniteDiagramSource,
) -> FiniteConfluenceCatalogSource:
    """Rebuild all requirements, expected keys, policy, order, and digest."""
    logger.debug("snapshot_finite_confluence_catalog entry")
    if type(value) is not FiniteConfluenceCatalogSource:
        _reject("finite-confluence-catalog-must-be-exact")
    try:
        local, global_, policy = (
            value.local_requirements, value.global_requirements, value.policy,
        )
        supplied_local, supplied_global = (
            value.expected_local_keys, value.expected_global_keys,
        )
        outer = (
            value.doctrine_fingerprint, value.diagram_digest,
            value.catalog_digest, value.version, value.scope,
        )
    except AttributeError:
        _reject("finite-confluence-catalog-missing-fields")
    if type(local) is not tuple or type(global_) is not tuple:
        _reject("finite-confluence-catalog-container-drift")
    if type(supplied_local) is not tuple or type(supplied_global) is not tuple:
        _reject("finite-confluence-catalog-key-container-drift")
    result = finite_confluence_catalog(doctrine, diagram, local, global_, policy)
    captured_local = _keys(supplied_local, RequirementKind.LOCAL, 64)
    captured_global = _keys(supplied_global, RequirementKind.GLOBAL, 128)
    if (
        len(captured_local) != len(result.expected_local_keys)
        or len(captured_global) != len(result.expected_global_keys)
        or captured_local != result.expected_local_keys
        or captured_global != result.expected_global_keys
    ):
        _reject("finite-confluence-catalog-key-drift")
    doctrine_fp, diagram_digest, catalog_digest, version, scope = outer
    if (
        type(doctrine_fp) is not str or type(diagram_digest) is not str
        or type(version) is not str or type(scope) is not str
        or _hex_digest(catalog_digest, "catalog-digest") != result.catalog_digest
        or doctrine_fp != result.doctrine_fingerprint
        or diagram_digest != result.diagram_digest
        or version != CATALOG_VERSION or scope != CATALOG_SCOPE
    ):
        _reject("finite-confluence-catalog-binding-drift")
    logger.debug("snapshot_finite_confluence_catalog exit")
    return result


def _keys(value: tuple, expected_kind: RequirementKind, cap: int) -> tuple:
    logger.debug("aggregate catalog keys entry kind=%s", expected_kind.value)
    if len(value) > cap:
        _reject("finite-confluence-catalog-key-count-limit")
    rows = []
    for item in value:
        if type(item) is not tuple or len(item) != 3:
            _reject("finite-confluence-catalog-key-shape")
        kind, identifier, digest = item
        if type(kind) is not RequirementKind or kind is not expected_kind:
            _reject("finite-confluence-catalog-key-kind")
        if type(identifier) is not str or not identifier:
            _reject("finite-confluence-catalog-key-id")
        rows.append((kind, identifier, _hex_digest(digest, "catalog-key-digest")))
    result = tuple(rows)
    logger.debug("aggregate catalog keys exit kind=%s rows=%d", expected_kind.value, len(result))
    return result
