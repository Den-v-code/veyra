"""Joint-square and occurrence binding for P1-C4 refinement survival."""

from __future__ import annotations

import logging

from .confluence import direct_echo_transport
from .confluence_plan import snapshot_fork_join_plan
from .scoped_formation_codec import ScopedFormationValidationError
from .scoped_formation_observers import require_observer_on_path
from .scoped_formation_types import FormationRefinementRequirement, SurvivalMode
from .translated_confluence_bridge import snapshot_response_bridge
from .translated_confluence_transport import snapshot_translated_spec
from .translated_confluence_types import TranslationDirection

logger = logging.getLogger(__name__)


def validate_refinement_binding(requirement: FormationRefinementRequirement, p0_doctrine, diagram) -> None:
    """Require one exact P0/P1-A bridge or one jointly bound C3 square."""
    logger.debug("validate_refinement_binding entry id=%s", requirement.requirement_id)
    if requirement.survival_mode is SurvivalMode.DIRECT:
        bridge = snapshot_response_bridge(
            p0_doctrine, diagram, requirement.a2_doctrine,
            requirement.a2_observer_source, requirement.a2_stage_source,
            requirement.direct_bridge,
        )
        pairs = tuple(
            x for x in bridge.observer_rows
            if x.diagram_observer_id == requirement.direct_observer_id
            and x.p1a_observer_id == requirement.coarse_observer_id
        )
        if len(pairs) != 1:
            logger.error("direct refinement bridge pair is not exact id=%s", requirement.requirement_id)
            raise ScopedFormationValidationError("direct-refinement-bridge-pair-mismatch")
        for path_id in requirement.path_ids:
            require_observer_on_path(
                p0_doctrine, diagram, path_id,
                requirement.direct_observer_id, "direct-survival",
            )
    else:
        bridge = snapshot_response_bridge(
            p0_doctrine, diagram, requirement.a2_doctrine,
            requirement.a2_observer_source, requirement.a2_stage_source,
            requirement.translated_bridge,
        )
        spec = requirement.translated_spec
        placeholder = direct_echo_transport(
            p0_doctrine,
            (spec.diagram_fine_observer_id, spec.diagram_coarse_observer_id),
        )
        plan = snapshot_fork_join_plan(
            requirement.translated_plan, diagram, placeholder, p0_doctrine,
        )
        checked = snapshot_translated_spec(
            p0_doctrine, diagram, plan, requirement.a2_doctrine,
            requirement.a2_observer_source, requirement.a2_stage_source,
            bridge, spec,
        )
        exact = (
            checked.p1a_fine_observer_id == requirement.fine_observer_id
            and checked.p1a_coarse_observer_id == requirement.coarse_observer_id
            and checked.morphism == requirement.morphism
            and checked.relation_scope == requirement.relation_scope
            and checked.relation_policy == requirement.relation_policy
            and checked.required_class is requirement.required_class
            and checked.required_preservation is requirement.required_preservation
            and checked.required_domain_equality is requirement.required_domain_equality
            and checked.required_loss is requirement.required_loss
            and checked.bridge_digest == bridge.bridge_digest
            and checked.plan_digest == plan.plan_digest
        )
        if not exact:
            logger.error("translated refinement joint square mismatch id=%s", requirement.requirement_id)
            raise ScopedFormationValidationError("translated-refinement-joint-square-mismatch")
        fine_slots = {0, 2} if checked.direction is TranslationDirection.LEFT_FINE_TO_RIGHT_COARSE else {1, 3}
        for index, path_id in enumerate(requirement.path_ids):
            observer_id = (
                checked.diagram_fine_observer_id if index in fine_slots
                else checked.diagram_coarse_observer_id
            )
            require_observer_on_path(
                p0_doctrine, diagram, path_id, observer_id,
                "translated-survival",
            )
    logger.debug("validate_refinement_binding exit id=%s", requirement.requirement_id)
