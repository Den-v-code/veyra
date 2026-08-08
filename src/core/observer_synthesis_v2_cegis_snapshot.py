"""Deep trusted catalog snapshots for the bounded R14.3b CEGIS path."""

from __future__ import annotations

import logging

from .observer_core_codec import ObserverCodecError, decode_observer
from .observer_core_semantics import infer_observer_kind
from .observer_synthesis_v2_budget import BudgetLedger
from .observer_synthesis_v2_catalog_provenance import _brand_catalog_v2
from .observer_synthesis_v2_grammar import (
    BOUNDARY,
    DEFAULT_GRAMMAR,
    EXPECTED_DEFAULT_CANDIDATES,
    EXPECTED_DEFAULT_CANONICAL_BYTES,
    EXPECTED_DEFAULT_CATALOG_DIGEST,
    EXPECTED_DEFAULT_MAX_ROW_BYTES,
    EXPECTED_DEFAULT_STRATA,
)
from .observer_synthesis_v2_types import (
    ObserverCandidateV2,
    ObserverGrammarEnumerationV2,
    ObserverGrammarStratumV2,
    ObserverGrammarV2,
)
from .observer_synthesis_v2_validation import verify_observer_grammar_enumeration_v2

logger = logging.getLogger(__name__)


class TrustedCegisCatalogSnapshotError(ValueError):
    """A validated source drifted while its trusted snapshot was rebuilt."""


def _trusted_cegis_catalog_snapshot_v2(
    catalog: ObserverGrammarEnumerationV2,
    construction_ledger: object = None,
) -> ObserverGrammarEnumerationV2:
    """Rebuild validated bytes into a separately branded trusted catalog."""
    logger.debug("trusted_cegis_catalog_snapshot_v2 entry")
    try:
        if construction_ledger is not None and type(construction_ledger) is not BudgetLedger:
            raise TypeError("invalid-construction-ledger")
        grammar = catalog.grammar
        source_strata = catalog.strata
        source_candidates = catalog.candidates
        catalog_scalars = (
            catalog.canonical_bytes,
            catalog.max_row_bytes,
            catalog.catalog_digest,
            catalog.complete,
            catalog.boundary,
        )
        if (
            type(grammar) is not ObserverGrammarV2
            or type(source_strata) is not tuple
            or type(source_candidates) is not tuple
            or any(type(value) is not int for value in catalog_scalars[:2])
            or type(catalog_scalars[2]) is not str
            or type(catalog_scalars[3]) is not bool
            or type(catalog_scalars[4]) is not str
        ):
            raise TrustedCegisCatalogSnapshotError("catalog-snapshot-drift")
        logger.debug(
            "trusted_cegis_catalog_snapshot_v2 state candidates=%d",
            len(source_candidates),
        )
        grammar_scalars = (
            grammar.schema,
            grammar.grammar_id,
            grammar.max_cost,
            grammar.max_depth,
            grammar.candidate_limit,
            grammar.canonical_bytes_limit,
        )
        if (
            any(type(value) is not str for value in grammar_scalars[:2])
            or any(type(value) is not int for value in grammar_scalars[2:])
        ):
            raise TrustedCegisCatalogSnapshotError("catalog-snapshot-drift")
        trusted_grammar = ObserverGrammarV2(
            *grammar_scalars,
        )
        trusted_candidates: list[ObserverCandidateV2] = []
        for row in source_candidates:
            if type(row) is not ObserverCandidateV2:
                raise TrustedCegisCatalogSnapshotError("catalog-snapshot-drift")
            row_scalars = (row.canonical, row.cost, row.depth, row.digest)
            if (
                type(row_scalars[0]) is not bytes
                or type(row_scalars[1]) is not int
                or type(row_scalars[2]) is not int
                or type(row_scalars[3]) is not str
            ):
                raise TrustedCegisCatalogSnapshotError("catalog-snapshot-drift")
            canonical = memoryview(row_scalars[0]).tobytes()
            observer = decode_observer(canonical)
            trusted_candidates.append(
                ObserverCandidateV2(
                    observer,
                    infer_observer_kind(observer),
                    row_scalars[1],
                    row_scalars[2],
                    canonical,
                    row_scalars[3],
                )
            )
        candidates = tuple(trusted_candidates)
        cursor = 0
        strata: list[ObserverGrammarStratumV2] = []
        for row in source_strata:
            if type(row) is not ObserverGrammarStratumV2:
                raise TrustedCegisCatalogSnapshotError("catalog-snapshot-drift")
            row_scalars = (row.cost, row.candidates, row.canonical_bytes)
            if (
                type(row_scalars[0]) is not int
                or type(row_scalars[1]) is not tuple
                or type(row_scalars[2]) is not int
            ):
                raise TrustedCegisCatalogSnapshotError("catalog-snapshot-drift")
            stop = cursor + len(row_scalars[1])
            strata.append(
                ObserverGrammarStratumV2(
                    row_scalars[0],
                    candidates[cursor:stop],
                    row_scalars[2],
                )
            )
            cursor = stop
        trusted = ObserverGrammarEnumerationV2(
            trusted_grammar,
            tuple(strata),
            candidates,
            *catalog_scalars,
        )
        result = _brand_catalog_v2(trusted, construction_ledger)
        exact_default = (
            trusted_grammar == DEFAULT_GRAMMAR
            and len(candidates) == EXPECTED_DEFAULT_CANDIDATES
            and tuple(len(row.candidates) for row in strata) == EXPECTED_DEFAULT_STRATA
            and catalog_scalars[0] == EXPECTED_DEFAULT_CANONICAL_BYTES
            and catalog_scalars[1] == EXPECTED_DEFAULT_MAX_ROW_BYTES
            and catalog_scalars[2] == EXPECTED_DEFAULT_CATALOG_DIGEST
            and catalog_scalars[3] is True
            and catalog_scalars[4] == BOUNDARY
        )
        if not exact_default or not verify_observer_grammar_enumeration_v2(
            result,
            construction_ledger,
        ):
            raise TrustedCegisCatalogSnapshotError("catalog-snapshot-drift")
    except ObserverCodecError as exc:
        logger.error(
            "trusted_cegis_catalog_snapshot_v2 exit=drift error=%s",
            type(exc).__name__,
        )
        raise TrustedCegisCatalogSnapshotError("catalog-snapshot-drift") from exc
    except TrustedCegisCatalogSnapshotError:
        logger.error("trusted_cegis_catalog_snapshot_v2 exit=drift")
        raise
    except Exception:
        logger.exception("trusted_cegis_catalog_snapshot_v2 exit=error")
        raise
    logger.debug(
        "trusted_cegis_catalog_snapshot_v2 exit candidates=%d",
        len(result.candidates),
    )
    return result
