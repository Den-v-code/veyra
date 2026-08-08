"""Catalog of checked optimizer local-law artifacts for VAM."""
from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

CHECKED_ARTIFACT = "proofs/lean/VeyraOptimizer.lean"
CHECKED_LOCAL_LAWS = (
    (
        "observer-alias",
        "observer-alias.lookup-invariant",
        CHECKED_ARTIFACT,
        "Veyra.observerAlias_lookup_invariant",
        "checked local lookup law only; optimizer pass remains obligation-backed",
    ),
    (
        "compress-alias",
        "compress-alias.same-pair-local-law",
        CHECKED_ARTIFACT,
        "Veyra.compressAlias_samePair_local_law",
        "checked local same source/observer alias law only; optimizer pass remains obligation-backed",
    ),
    (
        "compress-idempotent",
        "compress-idempotent.same-observer-local-law",
        CHECKED_ARTIFACT,
        "Veyra.compressIdempotent_sameObserver_local_law",
        "checked local same-observer compress idempotence law only; optimizer pass remains obligation-backed",
    ),
    (
        "compress-idempotent",
        "compress-idempotent.visible-use-observer-local-law",
        CHECKED_ARTIFACT,
        "Veyra.compressIdempotent_visibleUseObserver_local_law",
        "checked local visible-use observer preservation law only; optimizer pass remains obligation-backed",
    ),
    (
        "compress-idempotent",
        "compress-idempotent.different-observer-reject-local-law",
        CHECKED_ARTIFACT,
        "Veyra.compressIdempotent_differentObserver_reject_local_law",
        "checked local different-observer rejection law only; optimizer pass remains obligation-backed",
    ),
    (
        "compress-idempotent",
        "compress-idempotent.obstruction-boundary-reject-local-law",
        CHECKED_ARTIFACT,
        "Veyra.compressIdempotent_obstructionBoundary_reject_local_law",
        "checked local obstruction-boundary rejection law only; optimizer pass remains obligation-backed",
    ),
    (
        "dead-shadow",
        "dead-shadow.unused-lookup-local-law",
        CHECKED_ARTIFACT,
        "Veyra.deadShadow_unusedLookup_local_law",
        "checked local unused-shadow lookup/drop law only; optimizer pass remains obligation-backed",
    ),
)
REQUIRED_LEAN_SYMBOLS = tuple(row[3] for row in CHECKED_LOCAL_LAWS)


def checked_laws_for_pass(pass_name: str) -> tuple[tuple[str, str, str, str, str], ...]:
    """Return all checked local-law catalog rows for one optimizer pass."""
    logger.debug("optimizer_proof_catalog_checked_laws_for_pass entry pass=%s", pass_name)
    result = tuple(row for row in CHECKED_LOCAL_LAWS if row[0] == pass_name)
    logger.debug("optimizer_proof_catalog_checked_laws_for_pass exit rows=%d", len(result))
    return result


def checked_law_for_pass(pass_name: str) -> tuple[str, str, str, str, str] | None:
    """Return the first checked local-law catalog row for compatibility callers."""
    logger.debug("optimizer_proof_catalog_checked_law_for_pass entry pass=%s", pass_name)
    rows = checked_laws_for_pass(pass_name)
    result = rows[0] if rows else None
    logger.debug("optimizer_proof_catalog_checked_law_for_pass exit found=%s", result is not None)
    return result


def law_ids_for_pass(pass_name: str) -> tuple[str, ...]:
    """Return checked local-law ids for a pass or raise for uncataloged passes."""
    logger.debug("optimizer_proof_catalog_law_ids_for_pass entry pass=%s", pass_name)
    rows = checked_laws_for_pass(pass_name)
    if not rows:
        logger.debug("optimizer_proof_catalog_law_ids_for_pass fail pass=%s", pass_name)
        raise KeyError(pass_name)
    result = tuple(row[1] for row in rows)
    logger.debug("optimizer_proof_catalog_law_ids_for_pass exit rows=%d", len(result))
    return result


def law_id_for_pass(pass_name: str) -> str:
    """Return the first checked local-law id for a pass."""
    logger.debug("optimizer_proof_catalog_law_id_for_pass entry pass=%s", pass_name)
    result = law_ids_for_pass(pass_name)[0]
    logger.debug("optimizer_proof_catalog_law_id_for_pass exit law=%s", result)
    return result


def missing_required_lean_symbols(text: str) -> tuple[str, ...]:
    """Return catalog symbols not bound by theorem declarations in a Lean artifact."""
    logger.debug("optimizer_proof_catalog_missing_symbols entry bytes=%d", len(text))
    missing = []
    for symbol in REQUIRED_LEAN_SYMBOLS:
        symbol_name = symbol.rsplit(".", 1)[1]
        if re.search(rf"\btheorem\s+{re.escape(symbol_name)}\b", text) is None:
            missing.append(symbol)
    result = tuple(missing)
    logger.debug("optimizer_proof_catalog_missing_symbols exit missing=%d", len(result))
    return result
