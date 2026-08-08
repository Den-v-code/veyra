"""Run-local provenance for once-constructed R14 grammar catalogs."""
from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import logging

from .observer_synthesis_v2_budget import BudgetLedger, BudgetLedgerSnapshot
from .observer_synthesis_v2_types import (
    ObserverCandidateV2,
    ObserverGrammarEnumerationV2,
)
from .proof_core_codec import digest_data

logger = logging.getLogger(__name__)

_CATALOG_SEAL = object()
_CATALOG_BRAND_SCHEMA = "veyra.observer-synthesis-v2.catalog-brand.r14.2c.v1"


def catalog_digest_v2(candidates: tuple[ObserverCandidateV2, ...]) -> str:
    """Hash one validated canonical sequence without constructing DTOs."""
    logger.debug("catalog_digest_v2 entry candidates=%d", len(candidates))
    digest = sha256(b"veyra.observer-synthesis-v2.catalog.v1\0")
    for candidate in candidates:
        canonical = candidate.canonical
        digest.update(len(canonical).to_bytes(8, "big"))
        digest.update(canonical)
    result = digest.hexdigest()
    logger.debug("catalog_digest_v2 exit digest=%s", result[:12])
    return result


@dataclass(frozen=True, slots=True)
class _CatalogBrandV2:
    """Unserialized construction receipt bound to exact retained identities."""

    seal: object
    binding_digest: str
    strata: tuple[object, ...]
    candidates: tuple[object, ...]
    ledger: BudgetLedger | None
    ledger_snapshot: BudgetLedgerSnapshot | None


def _catalog_brand_data_v2(catalog: ObserverGrammarEnumerationV2) -> dict[str, object]:
    """Capture the immutable catalog roots without constructing candidates."""
    logger.debug("_catalog_brand_data_v2 entry")
    grammar = catalog.grammar
    result: dict[str, object] = {
        "boundary": catalog.boundary,
        "candidate_count": len(catalog.candidates),
        "canonical_bytes": catalog.canonical_bytes,
        "catalog_digest": catalog.catalog_digest,
        "complete": catalog.complete,
        "grammar": {
            "canonical_bytes_limit": grammar.canonical_bytes_limit,
            "candidate_limit": grammar.candidate_limit,
            "grammar_id": grammar.grammar_id,
            "max_cost": grammar.max_cost,
            "max_depth": grammar.max_depth,
            "schema": grammar.schema,
        },
        "max_row_bytes": catalog.max_row_bytes,
        "strata": [
            [row.cost, len(row.candidates), row.canonical_bytes]
            for row in catalog.strata
        ],
    }
    logger.debug("_catalog_brand_data_v2 exit")
    return result


def _brand_catalog_v2(
    catalog: ObserverGrammarEnumerationV2,
    ledger: BudgetLedger | None,
) -> ObserverGrammarEnumerationV2:
    """Internal construction receipt; callers receive no public rebranding API."""
    logger.debug("_brand_catalog_v2 entry")
    if (
        type(catalog) is not ObserverGrammarEnumerationV2
        or (ledger is not None and type(ledger) is not BudgetLedger)
    ):
        logger.error("_brand_catalog_v2 invalid source")
        raise ValueError("invalid-catalog-brand-source")
    snapshot = None if ledger is None else ledger.snapshot()
    brand = _CatalogBrandV2(
        _CATALOG_SEAL,
        digest_data(_catalog_brand_data_v2(catalog), _CATALOG_BRAND_SCHEMA),
        catalog.strata,
        catalog.candidates,
        ledger,
        snapshot,
    )
    result = replace(catalog, provenance=brand)
    logger.debug("_brand_catalog_v2 exit digest=%s", brand.binding_digest[:12])
    return result


def verify_catalog_brand_v2(
    catalog: object,
    construction_ledger: object = None,
) -> bool:
    """Require exact constructor provenance and an unchanged scalar binding."""
    logger.debug("verify_catalog_brand_v2 entry type=%s", type(catalog).__name__)
    if type(catalog) is not ObserverGrammarEnumerationV2:
        logger.debug("verify_catalog_brand_v2 exit valid=False")
        return False
    try:
        brand = catalog.provenance
        valid = (
            type(brand) is _CatalogBrandV2
            and brand.seal is _CATALOG_SEAL
            and type(brand.binding_digest) is str
            and brand.strata is catalog.strata
            and brand.candidates is catalog.candidates
            and brand.ledger is construction_ledger
            and (
                brand.ledger_snapshot is None
                if construction_ledger is None
                else (
                    type(construction_ledger) is BudgetLedger
                    and brand.ledger_snapshot == construction_ledger.snapshot()
                )
            )
            and brand.binding_digest
            == digest_data(_catalog_brand_data_v2(catalog), _CATALOG_BRAND_SCHEMA)
        )
    except (AttributeError, TypeError, ValueError):
        logger.exception("verify_catalog_brand_v2 malformed catalog")
        valid = False
    logger.debug("verify_catalog_brand_v2 exit valid=%s", valid)
    return valid
