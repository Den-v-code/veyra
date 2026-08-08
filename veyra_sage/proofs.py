"""Sage-facing proof objects and dependency queries for Veyra."""

from __future__ import annotations

from dataclasses import dataclass
from collections import deque
import logging

from src.core.curriculum_map import CurriculumEdge, curriculum_edges, school_curriculum_nodes
from src.core.theorem_registry import CardLike, TheoremSpec, all_theorem_specs, check_card, dependency_edges, registry_summary

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VeyraProofCheck:
    """Sage-facing result of checking one theorem card."""

    theorem_id: str
    status: str
    relation: str
    obstruction: str
    missing_dependencies: tuple[str, ...]

    def _repr_(self) -> str:
        """Return Sage-style representation."""
        return f"VeyraProofCheck({self.theorem_id}:{self.status})"

    def __repr__(self) -> str:
        """Return Python representation."""
        return self._repr_()

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready dictionary."""
        logger.debug("VeyraProofCheck.as_dict entry theorem=%s", self.theorem_id)
        result = {"theorem_id": self.theorem_id, "status": self.status, "relation": self.relation, "obstruction": self.obstruction, "missing_dependencies": self.missing_dependencies}
        logger.debug("VeyraProofCheck.as_dict exit status=%s", self.status)
        return result


@dataclass(frozen=True)
class VeyraProofObject:
    """Sage-facing theorem spec with a card checker."""

    theorem_id: str
    title: str
    claim: str
    dependencies: tuple[str, ...]
    success_relations: tuple[str, ...]
    obstruction_catalog: tuple[str, ...]
    hook: str

    def _repr_(self) -> str:
        """Return Sage-style representation."""
        return f"VeyraProofObject({self.theorem_id})"

    def __repr__(self) -> str:
        """Return Python representation."""
        return self._repr_()

    def depends_on(self, definition_id: str) -> bool:
        """Return whether this proof object depends on a definition."""
        logger.debug("VeyraProofObject.depends_on entry theorem=%s def=%s", self.theorem_id, definition_id)
        result = definition_id in self.dependencies
        logger.debug("VeyraProofObject.depends_on exit result=%s", result)
        return result

    def check(self, card: CardLike) -> VeyraProofCheck:
        """Check an executable theorem card against this proof spec."""
        logger.debug("VeyraProofObject.check entry theorem=%s", self.theorem_id)
        spec = TheoremSpec(self.theorem_id, self.title, self.claim, self.dependencies, self.success_relations, self.obstruction_catalog, self.hook)
        checked = check_card(spec, card)
        result = VeyraProofCheck(checked.theorem_id, checked.status, checked.relation, checked.obstruction, checked.missing_dependencies)
        logger.debug("VeyraProofObject.check exit status=%s", result.status)
        return result

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready theorem proof object metadata."""
        logger.debug("VeyraProofObject.as_dict entry theorem=%s", self.theorem_id)
        result = {"theorem_id": self.theorem_id, "title": self.title, "claim": self.claim, "dependencies": self.dependencies, "success_relations": self.success_relations, "obstruction_catalog": self.obstruction_catalog, "hook": self.hook}
        logger.debug("VeyraProofObject.as_dict exit keys=%r", sorted(result))
        return result


class VeyraProofGraph:
    """Facade for theorem dependencies and curriculum paths."""

    def __init__(self) -> None:
        """Load current theorem specs and curriculum graph."""
        logger.debug("VeyraProofGraph.__init__ entry")
        self._specs = all_theorem_specs()
        self._nodes = school_curriculum_nodes()
        self._edges = curriculum_edges()
        logger.debug("VeyraProofGraph.__init__ exit specs=%d nodes=%d edges=%d", len(self._specs), len(self._nodes), len(self._edges))

    def _repr_(self) -> str:
        """Return Sage-style representation."""
        return f"VeyraProofGraph(specs={len(self._specs)}, curriculum_edges={len(self._edges)})"

    def __repr__(self) -> str:
        """Return Python representation."""
        return self._repr_()

    def summary(self) -> dict[str, int]:
        """Return compact proof graph summary."""
        logger.debug("VeyraProofGraph.summary entry")
        reg = registry_summary(self._specs)
        result = {"theorem_specs": reg.total, "definition_edges": reg.dependency_edges, "sage_ready": reg.sage_ready, "curriculum_nodes": len(self._nodes), "curriculum_edges": len(self._edges), "domains": len(self.domain_index())}
        logger.debug("VeyraProofGraph.summary exit result=%r", result)
        return result

    def proof_object(self, theorem_id: str) -> VeyraProofObject:
        """Return one proof object by theorem ID."""
        logger.debug("VeyraProofGraph.proof_object entry theorem=%s", theorem_id)
        spec = self._specs[theorem_id]
        result = VeyraProofObject(spec.theorem_id, spec.title, spec.claim, spec.dependencies, spec.success_relations, spec.obstruction_catalog, spec.sage_hook)
        logger.debug("VeyraProofGraph.proof_object exit hook=%s", result.hook)
        return result

    def proof_objects(self, domain: str | None = None) -> tuple[VeyraProofObject, ...]:
        """Return proof objects, optionally filtered by Sage-hook domain."""
        logger.debug("VeyraProofGraph.proof_objects entry domain=%s", domain)
        ids = sorted(self._specs)
        objects = tuple(self.proof_object(item) for item in ids)
        result = tuple(obj for obj in objects if domain is None or obj.hook.split(".", 1)[0] == domain)
        logger.debug("VeyraProofGraph.proof_objects exit count=%d", len(result))
        return result

    def definition_dependencies(self, theorem_id: str) -> tuple[str, ...]:
        """Return definition dependencies for one theorem."""
        logger.debug("VeyraProofGraph.definition_dependencies entry theorem=%s", theorem_id)
        result = self._specs[theorem_id].dependencies
        logger.debug("VeyraProofGraph.definition_dependencies exit count=%d", len(result))
        return result

    def theorems_using(self, definition_id: str) -> tuple[str, ...]:
        """Return theorem IDs depending on a definition."""
        logger.debug("VeyraProofGraph.theorems_using entry def=%s", definition_id)
        result = tuple(sorted(theorem for theorem, dep in dependency_edges(self._specs) if dep == definition_id))
        logger.debug("VeyraProofGraph.theorems_using exit count=%d", len(result))
        return result

    def domain_index(self) -> dict[str, tuple[str, ...]]:
        """Return Sage-hook domain to theorem IDs index."""
        logger.debug("VeyraProofGraph.domain_index entry")
        domains = sorted({spec.sage_hook.split(".", 1)[0] for spec in self._specs.values()})
        result = {domain: tuple(sorted(spec.theorem_id for spec in self._specs.values() if spec.sage_hook.split(".", 1)[0] == domain)) for domain in domains}
        logger.debug("VeyraProofGraph.domain_index exit domains=%d", len(result))
        return result

    def curriculum_successors(self, concept_id: str) -> tuple[str, ...]:
        """Return outgoing curriculum targets."""
        logger.debug("VeyraProofGraph.curriculum_successors entry concept=%s", concept_id)
        result = tuple(edge.target for edge in self._edges if edge.source == concept_id)
        logger.debug("VeyraProofGraph.curriculum_successors exit count=%d", len(result))
        return result

    def curriculum_predecessors(self, concept_id: str) -> tuple[str, ...]:
        """Return incoming curriculum sources."""
        logger.debug("VeyraProofGraph.curriculum_predecessors entry concept=%s", concept_id)
        result = tuple(edge.source for edge in self._edges if edge.target == concept_id)
        logger.debug("VeyraProofGraph.curriculum_predecessors exit count=%d", len(result))
        return result

    def curriculum_path(self, source: str, target: str) -> tuple[str, ...]:
        """Return shortest curriculum path, or empty tuple if absent."""
        logger.debug("VeyraProofGraph.curriculum_path entry source=%s target=%s", source, target)
        queue: deque[tuple[str, tuple[str, ...]]] = deque([(source, (source,))])
        seen = {source}
        while queue:
            node, path = queue.popleft()
            if node == target:
                logger.debug("VeyraProofGraph.curriculum_path exit length=%d", len(path))
                return path
            for nxt in self.curriculum_successors(node):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, path + (nxt,)))
        logger.debug("VeyraProofGraph.curriculum_path exit missing")
        return ()

    def curriculum_edges(self) -> tuple[CurriculumEdge, ...]:
        """Return raw curriculum edges for downstream labs."""
        logger.debug("VeyraProofGraph.curriculum_edges entry")
        return self._edges
