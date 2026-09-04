"""Declared transitive source-closure checks for bounded P3-OG selection.

The contract is intentionally narrower than full DEF-OG-002.  It proves one
finite graph property: the three pre-selection roots (pool, blind seed, selector
law) have no declared transitive dependency on outcome-bearing information.
"""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest

from .prime_power_observer_genesis_p3og_codec import canonical_bytes, digest
from .prime_power_observer_genesis_p3og_selection_source_closure_types import (
    P3OG_SELECTION_SOURCE_CLOSURE_BOUNDARY,
    P3OGSelectionDependencyNode,
    P3OGSelectionSourceClosure,
    SelectionDependencyKind,
)
from .prime_power_observer_genesis_p3og_source import validate_source
from .prime_power_observer_genesis_p3og_types import P3OGSource

SOURCE_CLOSURE_VERSION = "p3og-selection-source-closure-v1"
POOL_ROOT_ID = "selection-pool-root"
BLIND_SEED_ROOT_ID = "selection-blind-seed-root"
SELECTOR_LAW_ROOT_ID = "selection-selector-law-root"
ROOT_IDS = (POOL_ROOT_ID, BLIND_SEED_ROOT_ID, SELECTOR_LAW_ROOT_ID)
SELECTOR_RULE_ID = "blind-pool-seed-mod-v1"
MAX_DEPENDENCY_NODES = 128
MAX_DEPENDENCY_PARENTS = 8
MAX_NODE_ID_CHARS = 128
_HEX = frozenset("0123456789abcdef")
_FORBIDDEN = frozenset({
    SelectionDependencyKind.DISCRIMINATION_CRITERION,
    SelectionDependencyKind.TARGET,
    SelectionDependencyKind.SELECTED_RESPONSE,
    SelectionDependencyKind.LATER_STATUS,
    SelectionDependencyKind.THEOREM_CONCLUSION,
})


def _require_digest(value: object, code: str) -> str:
    """Require one exact lower-case SHA-256 hex digest."""
    if type(value) is not str or len(value) != 64 or any(char not in _HEX for char in value):
        raise ValueError(code)
    return value


def _pool_digest(source: P3OGSource) -> str:
    """Bind the exact canonical ordered candidate pool."""
    return digest("pool", tuple(seed.seed_digest for seed in source.seeds))


def selector_law_digest() -> str:
    """Bind the exact selector rule used by this declared closure contract."""
    return digest("selection-selector-law", SELECTOR_RULE_ID)


def p3og_selection_dependency_node(
    node_id: str,
    kind: SelectionDependencyKind,
    parent_ids: tuple[str, ...],
    payload_digest: str,
) -> P3OGSelectionDependencyNode:
    """Construct one bounded exact dependency node."""
    if type(node_id) is not str or not node_id or len(node_id) > MAX_NODE_ID_CHARS:
        raise ValueError("p3og-selection-dependency-node-id")
    if type(kind) is not SelectionDependencyKind:
        raise ValueError("p3og-selection-dependency-kind")
    if (
        type(parent_ids) is not tuple
        or len(parent_ids) > MAX_DEPENDENCY_PARENTS
        or len(parent_ids) != len(set(parent_ids))
        or any(
            type(item) is not str or not item or len(item) > MAX_NODE_ID_CHARS
            for item in parent_ids
        )
        or node_id in parent_ids
    ):
        raise ValueError("p3og-selection-dependency-parents")
    payload_digest = _require_digest(payload_digest, "p3og-selection-dependency-payload")
    fields = (node_id, kind, parent_ids, payload_digest)
    return P3OGSelectionDependencyNode(
        *fields,
        digest("selection-dependency-node", *fields),
    )


def _snapshot_node(node: P3OGSelectionDependencyNode) -> P3OGSelectionDependencyNode:
    """Freshly reconstruct one node before trusting nested fields."""
    if type(node) is not P3OGSelectionDependencyNode:
        raise ValueError("p3og-selection-dependency-node-type")
    try:
        expected = p3og_selection_dependency_node(
            node.node_id,
            node.kind,
            node.parent_ids,
            node.payload_digest,
        )
        equal = compare_digest(canonical_bytes(node), canonical_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-selection-dependency-node-malformed") from exc
    if not equal:
        raise ValueError("p3og-selection-dependency-node-drift")
    return replace(expected)


def _default_nodes(
    source: P3OGSource,
    blind_seed_digest: str,
) -> tuple[P3OGSelectionDependencyNode, ...]:
    """Build the minimal outcome-free declared closure."""
    return (
        p3og_selection_dependency_node(
            POOL_ROOT_ID,
            SelectionDependencyKind.POOL,
            (),
            _pool_digest(source),
        ),
        p3og_selection_dependency_node(
            BLIND_SEED_ROOT_ID,
            SelectionDependencyKind.BLIND_SEED,
            (),
            blind_seed_digest,
        ),
        p3og_selection_dependency_node(
            SELECTOR_LAW_ROOT_ID,
            SelectionDependencyKind.SELECTOR_LAW,
            (),
            selector_law_digest(),
        ),
    )


def _validate_acyclic(table: dict[str, P3OGSelectionDependencyNode]) -> None:
    """Reject every cycle, including cycles outside the root closure."""
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visiting:
            raise ValueError("p3og-selection-dependency-cycle")
        if name in visited:
            return
        visiting.add(name)
        for parent in table[name].parent_ids:
            visit(parent)
        visiting.remove(name)
        visited.add(name)

    for name in table:
        visit(name)


def _transitive_root_closure(
    table: dict[str, P3OGSelectionDependencyNode],
) -> tuple[str, ...]:
    """Return deterministic graph ancestry of the three selection roots."""
    closure: set[str] = set()
    stack = list(reversed(ROOT_IDS))
    while stack:
        name = stack.pop()
        if name in closure:
            continue
        closure.add(name)
        stack.extend(reversed(table[name].parent_ids))
    return tuple(sorted(closure))


def p3og_selection_source_closure(
    source: P3OGSource,
    blind_seed_digest: str,
    nodes: tuple[P3OGSelectionDependencyNode, ...] | None = None,
) -> P3OGSelectionSourceClosure:
    """Seal the declared root closure and reject outcome-bearing ancestry."""
    source = validate_source(source)
    blind_seed_digest = _require_digest(
        blind_seed_digest,
        "p3og-selection-closure-blind-seed",
    )
    if nodes is None:
        nodes = _default_nodes(source, blind_seed_digest)
    if type(nodes) is not tuple or not 3 <= len(nodes) <= MAX_DEPENDENCY_NODES:
        raise ValueError("p3og-selection-dependency-node-count")

    trusted = tuple(sorted((_snapshot_node(node) for node in nodes), key=lambda node: node.node_id))
    table = {node.node_id: node for node in trusted}
    if len(table) != len(trusted):
        raise ValueError("p3og-selection-dependency-duplicate-node")
    if any(parent not in table for node in trusted for parent in node.parent_ids):
        raise ValueError("p3og-selection-dependency-unknown-parent")

    expected_roots = {
        POOL_ROOT_ID: (SelectionDependencyKind.POOL, _pool_digest(source)),
        BLIND_SEED_ROOT_ID: (SelectionDependencyKind.BLIND_SEED, blind_seed_digest),
        SELECTOR_LAW_ROOT_ID: (SelectionDependencyKind.SELECTOR_LAW, selector_law_digest()),
    }
    for root_id, (kind, payload) in expected_roots.items():
        root = table.get(root_id)
        if root is None or root.kind is not kind or root.payload_digest != payload:
            raise ValueError("p3og-selection-dependency-root-drift")

    _validate_acyclic(table)
    closure_ids = _transitive_root_closure(table)
    forbidden_ids = tuple(
        node_id for node_id in closure_ids if table[node_id].kind in _FORBIDDEN
    )
    if forbidden_ids:
        raise ValueError("p3og-selection-source-closure-forbidden-dependency")

    fields = (
        SOURCE_CLOSURE_VERSION,
        source.source_digest,
        trusted,
        ROOT_IDS,
        closure_ids,
        forbidden_ids,
        P3OG_SELECTION_SOURCE_CLOSURE_BOUNDARY,
    )
    return P3OGSelectionSourceClosure(
        *fields,
        digest("selection-source-closure", *fields),
    )


def validate_p3og_selection_source_closure(
    source: P3OGSource,
    blind_seed_digest: str,
    closure: P3OGSelectionSourceClosure,
) -> P3OGSelectionSourceClosure:
    """Freshly reconstruct one declared closure and reject source/graph drift."""
    if type(closure) is not P3OGSelectionSourceClosure:
        raise ValueError("p3og-selection-source-closure-type")
    try:
        expected = p3og_selection_source_closure(source, blind_seed_digest, closure.nodes)
        equal = compare_digest(canonical_bytes(closure), canonical_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-selection-source-closure-malformed") from exc
    if not equal:
        raise ValueError("p3og-selection-source-closure-drift")
    return replace(expected)
