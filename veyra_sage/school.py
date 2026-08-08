"""Sage-facing school-core facade for Veyra theorem/curriculum registries."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from src.core.curriculum_map import curriculum_summary, missing_curriculum_concepts, sage_export_rows, school_curriculum_nodes
from src.core.depth_packs import curriculum_sage_export_rows, theorem_sage_export_rows
from src.core.theorem_registry import all_theorem_specs, registry_summary

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VeyraTheoremSpec:
    """Sage-facing immutable theorem spec wrapper."""

    theorem_id: str
    title: str
    dependencies: tuple[str, ...]
    hook: str

    def _repr_(self) -> str:
        """Return Sage-style representation."""
        return f"VeyraTheoremSpec({self.theorem_id})"

    def __repr__(self) -> str:
        """Return Python representation."""
        return self._repr_()


@dataclass(frozen=True)
class VeyraCurriculumNode:
    """Sage-facing immutable curriculum node wrapper."""

    concept_id: str
    domain: str
    grade_band: str
    theorem_ids: tuple[str, ...]
    status: str

    def _repr_(self) -> str:
        """Return Sage-style representation."""
        return f"VeyraCurriculumNode({self.concept_id}:{self.status})"

    def __repr__(self) -> str:
        """Return Python representation."""
        return self._repr_()


@dataclass(frozen=True)
class VeyraExportRow:
    """Sage-facing JSON-ready export row wrapper."""

    row_type: str
    name: str
    domain: str
    hook: str
    payload: tuple[tuple[str, str], ...]

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready dictionary."""
        logger.debug("VeyraExportRow.as_dict entry name=%s", self.name)
        result = {"row_type": self.row_type, "name": self.name, "domain": self.domain, "hook": self.hook, "payload": dict(self.payload)}
        logger.debug("VeyraExportRow.as_dict exit keys=%r", sorted(result))
        return result


class VeyraSchoolCore:
    """Facade exposing theorem specs, curriculum nodes, and Sage export rows."""

    def __init__(self) -> None:
        """Create school-core facade from current registries."""
        logger.debug("VeyraSchoolCore.__init__ entry")
        self._specs = all_theorem_specs()
        self._nodes = school_curriculum_nodes()
        logger.debug("VeyraSchoolCore.__init__ exit specs=%d nodes=%d", len(self._specs), len(self._nodes))

    def _repr_(self) -> str:
        """Return Sage-style representation."""
        return f"VeyraSchoolCore(specs={len(self._specs)}, nodes={len(self._nodes)})"

    def __repr__(self) -> str:
        """Return Python representation."""
        return self._repr_()

    def theorem_specs(self) -> tuple[VeyraTheoremSpec, ...]:
        """Return theorem spec wrappers."""
        logger.debug("VeyraSchoolCore.theorem_specs entry")
        result = tuple(VeyraTheoremSpec(item.theorem_id, item.title, item.dependencies, item.sage_hook) for item in sorted(self._specs.values(), key=lambda x: x.theorem_id))
        logger.debug("VeyraSchoolCore.theorem_specs exit count=%d", len(result))
        return result

    def curriculum_nodes(self) -> tuple[VeyraCurriculumNode, ...]:
        """Return curriculum node wrappers."""
        logger.debug("VeyraSchoolCore.curriculum_nodes entry")
        result = tuple(VeyraCurriculumNode(item.concept_id, item.domain, item.grade_band, item.theorem_ids, item.status) for item in self._nodes)
        logger.debug("VeyraSchoolCore.curriculum_nodes exit count=%d", len(result))
        return result

    def theorem_spec(self, theorem_id: str) -> VeyraTheoremSpec:
        """Return one theorem spec wrapper by ID."""
        logger.debug("VeyraSchoolCore.theorem_spec entry theorem_id=%s", theorem_id)
        item = self._specs[theorem_id]
        result = VeyraTheoremSpec(item.theorem_id, item.title, item.dependencies, item.sage_hook)
        logger.debug("VeyraSchoolCore.theorem_spec exit hook=%s", result.hook)
        return result

    def curriculum_node(self, concept_id: str) -> VeyraCurriculumNode:
        """Return one curriculum node wrapper by ID."""
        logger.debug("VeyraSchoolCore.curriculum_node entry concept_id=%s", concept_id)
        table = {item.concept_id: item for item in self._nodes}
        item = table[concept_id]
        result = VeyraCurriculumNode(item.concept_id, item.domain, item.grade_band, item.theorem_ids, item.status)
        logger.debug("VeyraSchoolCore.curriculum_node exit status=%s", result.status)
        return result

    def summary(self) -> dict[str, int]:
        """Return combined registry/curriculum summary."""
        logger.debug("VeyraSchoolCore.summary entry")
        reg = registry_summary(self._specs)
        cur = curriculum_summary(self._nodes, self._specs)
        result = {"theorem_specs": reg.total, "dependency_edges": reg.dependency_edges, "sage_ready": reg.sage_ready, "curriculum_nodes": cur.concepts, "curriculum_missing": cur.missing, "sage_rows": cur.sage_rows}
        logger.debug("VeyraSchoolCore.summary exit result=%r", result)
        return result

    def missing(self) -> tuple[str, ...]:
        """Return missing curriculum concept IDs."""
        logger.debug("VeyraSchoolCore.missing entry")
        result = tuple(item.concept_id for item in missing_curriculum_concepts(self._nodes, self._specs))
        logger.debug("VeyraSchoolCore.missing exit count=%d", len(result))
        return result

    def export_rows(self) -> tuple[VeyraExportRow, ...]:
        """Return theorem and curriculum Sage export rows."""
        logger.debug("VeyraSchoolCore.export_rows entry")
        theorem_rows = theorem_sage_export_rows(self._specs)
        curriculum_rows = curriculum_sage_export_rows(sage_export_rows(self._nodes, self._specs))
        result = tuple(VeyraExportRow(row.row_type, row.name, row.domain, row.hook, row.payload) for row in theorem_rows + curriculum_rows)
        logger.debug("VeyraSchoolCore.export_rows exit count=%d", len(result))
        return result

    def export_dicts(self) -> tuple[dict[str, object], ...]:
        """Return JSON-ready export dictionaries."""
        logger.debug("VeyraSchoolCore.export_dicts entry")
        result = tuple(row.as_dict() for row in self.export_rows())
        logger.debug("VeyraSchoolCore.export_dicts exit count=%d", len(result))
        return result
