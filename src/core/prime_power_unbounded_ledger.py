"""Exact source-prior dependency ledger for the checked P3-N6 E slice."""

from __future__ import annotations

import logging

from .prime_power_unbounded_common import (
    digest, exact_digest, exact_shape, freeze_layout, reject,
)
from .prime_power_unbounded_sources import E_THEOREM_IDS, theorem_source
from .prime_power_unbounded_types import (
    N6DependencyRowV1,
    N6DependencyUnionV1,
    N6Lane,
    N6LedgerRowKind,
)

logger = logging.getLogger(__name__)

LEDGER_VERSION = "p3n6-e-ledger-v1"
EQUALITY_ADAPTER_THEOREM_ID = "THM_P3N6_005_carrier_equality_adapter"
INJECTION_THEOREM_IDS = (
    "THM_P3N6_003_power_carrier_injective",
    "THM_P3N6_004_power_carrier_eqc_injective",
)
E_AXIOM_CLOSURE = ("propext",)
E_COMPILER_AXIOM_ROWS = (
    (INJECTION_THEOREM_IDS[0], E_AXIOM_CLOSURE),
    (INJECTION_THEOREM_IDS[1], E_AXIOM_CLOSURE),
    (EQUALITY_ADAPTER_THEOREM_ID, ()),
)
_LEDGER_LAYOUT = freeze_layout(N6DependencyUnionV1, (
    "version", "ordered_rows", "theorem_axiom_rows", "ledger_digest",
))
_ROW_LAYOUT = freeze_layout(N6DependencyRowV1, (
    "row_id", "row_kind", "direct_dependencies", "source_digest", "axiom_closure",
))


def _specs() -> tuple[tuple[str, N6LedgerRowKind, tuple[str, ...], str], ...]:
    """Return the sole ordered N6-E dependency graph."""
    logger.debug("_specs entry")
    source = theorem_source(N6Lane.E_POWER_INJECTION)
    base = (
        ("natural-numbers", N6LedgerRowKind.FOUNDATION, (), source.tcb_digest),
        ("propositions-equality", N6LedgerRowKind.FOUNDATION, (), source.tcb_digest),
        ("propext", N6LedgerRowKind.FOUNDATION, (), source.tcb_digest),
        ("lean-kernel", N6LedgerRowKind.TRUSTED_BOUNDARY, (), source.tcb_digest),
        ("pomega2-package", N6LedgerRowKind.DEFINITION, (), source.transitive_imports[-1][1]),
        ("n1-family-source", N6LedgerRowKind.DEFINITION, ("pomega2-package",), source.direct_imports[0][1]),
        ("veyraPowerCarrier", N6LedgerRowKind.DEFINITION, ("natural-numbers", "n1-family-source"), source.artifact_sha256),
        ("veyraCarrierEq", N6LedgerRowKind.DEFINITION, ("propositions-equality", "pomega2-package"), source.artifact_sha256),
        (INJECTION_THEOREM_IDS[0], N6LedgerRowKind.THEOREM, ("veyraPowerCarrier", "lean-kernel", "propext"), source.artifact_sha256),
        (INJECTION_THEOREM_IDS[1], N6LedgerRowKind.THEOREM, (INJECTION_THEOREM_IDS[0], "veyraCarrierEq"), source.artifact_sha256),
        (EQUALITY_ADAPTER_THEOREM_ID, N6LedgerRowKind.THEOREM, ("veyraCarrierEq", "pomega2-package"), source.artifact_sha256),
        ("checked-n6-e-runner", N6LedgerRowKind.TRUSTED_BOUNDARY, (INJECTION_THEOREM_IDS[1], EQUALITY_ADAPTER_THEOREM_ID), source.tcb_digest),
    )
    logger.debug("_specs exit rows=%d", len(base))
    return base


def _row_digest(row_id: str, kind: N6LedgerRowKind, origin: str) -> str:
    """Bind one row to its exact kind and source identity."""
    logger.debug("_row_digest entry row=%s", row_id)
    result = digest("veyra.p3n6.e-ledger-row.v1", (
        ("row", row_id.encode()), ("kind", kind.value.encode()),
        ("origin", origin.encode()),
    ))
    logger.debug("_row_digest exit row=%s", row_id)
    return result


def _rows() -> tuple[N6DependencyRowV1, ...]:
    """Compute all transitive axiom closures without caller input."""
    logger.debug("_rows entry")
    closures: dict[str, tuple[str, ...]] = {}
    rows: list[N6DependencyRowV1] = []
    for row_id, kind, dependencies, origin in _specs():
        closure = {row_id} if row_id == "propext" else set()
        for dependency in dependencies:
            if dependency not in closures:
                reject("n6-e-ledger-forward-or-missing-dependency")
            closure.update(closures[dependency])
        closures[row_id] = tuple(sorted(closure))
        rows.append(N6DependencyRowV1(
            row_id, kind, dependencies, _row_digest(row_id, kind, origin),
            closures[row_id],
        ))
    result = tuple(rows)
    logger.debug("_rows exit rows=%d", len(result))
    return result


def _ledger_digest(rows: tuple[N6DependencyRowV1, ...]) -> str:
    """Commit the exact ordered graph and theorem closures."""
    logger.debug("_ledger_digest entry rows=%d", len(rows))
    payload: list[tuple[str, bytes]] = [("version", LEDGER_VERSION.encode())]
    for index, row in enumerate(rows):
        value = "\0".join((
            row.row_id, row.row_kind.value, *row.direct_dependencies,
            row.source_digest, *row.axiom_closure,
        )).encode()
        payload.append((f"row-{index}", value))
    result = digest("veyra.p3n6.e-ledger.v1", tuple(payload))
    logger.debug("_ledger_digest exit")
    return result


def n6e_dependency_ledger() -> N6DependencyUnionV1:
    """Construct the canonical E-lane ledger."""
    logger.debug("n6e_dependency_ledger entry")
    rows = _rows()
    if E_THEOREM_IDS != tuple(name for name, _ in E_COMPILER_AXIOM_ROWS):
        reject("n6-e-ledger-theorem-source-order-drift")
    theorem_rows = E_COMPILER_AXIOM_ROWS
    result = N6DependencyUnionV1(
        LEDGER_VERSION, rows, theorem_rows, _ledger_digest(rows),
    )
    logger.debug("n6e_dependency_ledger exit")
    return result


def snapshot_n6e_ledger(value: N6DependencyUnionV1) -> N6DependencyUnionV1:
    """Reject any caller graph, source, theorem, or closure drift."""
    logger.debug("snapshot_n6e_ledger entry")
    exact_shape(value, _LEDGER_LAYOUT, "n6-e-ledger")
    if type(value.ordered_rows) is not tuple or not 1 <= len(value.ordered_rows) <= 64:
        reject("n6-e-ledger-row-count-invalid")
    if type(value.theorem_axiom_rows) is not tuple:
        reject("n6-e-ledger-axiom-rows-invalid")
    exact_digest(value.ledger_digest, "n6-e-ledger-digest")
    for row in value.ordered_rows:
        exact_shape(row, _ROW_LAYOUT, "n6-e-ledger-row")
        if type(row.row_id) is not str or type(row.row_kind) is not N6LedgerRowKind:
            reject("n6-e-ledger-row-header-invalid")
        if type(row.direct_dependencies) is not tuple or type(row.axiom_closure) is not tuple:
            reject("n6-e-ledger-row-tuples-invalid")
        exact_digest(row.source_digest, "n6-e-ledger-row-source")
    expected = n6e_dependency_ledger()
    if value != expected:
        reject("n6-e-ledger-drift")
    logger.debug("snapshot_n6e_ledger exit")
    return expected


def checked_axiom_closure(
    ledger: N6DependencyUnionV1,
    compiler_rows: tuple[tuple[str, tuple[str, ...]], ...],
) -> tuple[str, ...] | None:
    """Accept only exact ordered compiler/ledger theorem closure agreement."""
    logger.debug("checked_axiom_closure entry rows=%d", len(compiler_rows))
    checked = snapshot_n6e_ledger(ledger)
    if type(compiler_rows) is not tuple or compiler_rows != checked.theorem_axiom_rows:
        logger.error("checked_axiom_closure compiler rows mismatch")
        return None
    result = E_AXIOM_CLOSURE
    logger.debug("checked_axiom_closure exit closure=%r", result)
    return result
