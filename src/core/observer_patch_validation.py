"""Canonical structural validation for finite observer-patch atlas values."""
from __future__ import annotations

from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ObserverPatch:
    """A named finite patch of observer-visible nods."""

    name: str
    nodes: tuple[str, ...]


@dataclass(frozen=True)
class ObserverPatchAtlas:
    """A finite universe covered by named observer patches."""

    universe: tuple[str, ...]
    patches: tuple[ObserverPatch, ...]


@dataclass(frozen=True)
class LocalObserverSection:
    """A partition, hence an echo-equivalence, on one patch."""

    patch_name: str
    blocks: tuple[tuple[str, ...], ...]


def validate_patch_shape(patch: object) -> ObserverPatch:
    """Return an exact canonical patch or fail closed."""
    logger.debug("validate_patch_shape entry type=%s", type(patch).__name__)
    valid = type(patch) is ObserverPatch
    if valid:
        valid = type(patch.name) is str and bool(patch.name)
        valid = valid and type(patch.nodes) is tuple and bool(patch.nodes)
        valid = valid and all(type(node) is str and bool(node) for node in patch.nodes)
        valid = valid and len(set(patch.nodes)) == len(patch.nodes)
    if not valid:
        logger.error("validate_patch_shape invalid patch=%r", patch)
        raise ValueError("patch requires an exact type, nonempty name, and unique nonempty string nods")
    logger.debug("validate_patch_shape exit name=%s nodes=%d", patch.name, len(patch.nodes))
    return patch


def validate_atlas_shape(atlas: object) -> ObserverPatchAtlas:
    """Return an exact canonical, nonempty, exact-cover atlas or fail closed."""
    logger.debug("validate_atlas_shape entry type=%s", type(atlas).__name__)
    valid = type(atlas) is ObserverPatchAtlas
    if valid:
        valid = type(atlas.universe) is tuple and bool(atlas.universe)
        valid = valid and all(type(node) is str and bool(node) for node in atlas.universe)
        valid = valid and len(set(atlas.universe)) == len(atlas.universe)
        valid = valid and type(atlas.patches) is tuple and bool(atlas.patches)
    if not valid:
        logger.error("validate_atlas_shape invalid shell atlas=%r", atlas)
        raise ValueError("atlas requires an exact type and unique nonempty string universe")
    patches = tuple(validate_patch_shape(patch) for patch in atlas.patches)
    names = tuple(patch.name for patch in patches)
    universe = set(atlas.universe)
    covered = {node for patch in patches for node in patch.nodes}
    valid_cover = len(set(names)) == len(names)
    valid_cover = valid_cover and all(set(patch.nodes) <= universe for patch in patches)
    valid_cover = valid_cover and covered == universe
    if not valid_cover:
        logger.error(
            "validate_atlas_shape invalid cover names=%r universe=%r covered=%r",
            names, atlas.universe, covered,
        )
        raise ValueError("atlas patches must be uniquely named and form an exact finite cover")
    logger.debug("validate_atlas_shape exit universe=%d patches=%d", len(atlas.universe), len(patches))
    return atlas


def validate_section_shape(section: object) -> LocalObserverSection:
    """Return an exact canonical standalone local partition or fail closed."""
    logger.debug("validate_section_shape entry type=%s", type(section).__name__)
    valid = type(section) is LocalObserverSection
    if valid:
        valid = type(section.patch_name) is str and bool(section.patch_name)
        valid = valid and type(section.blocks) is tuple and bool(section.blocks)
        valid = valid and all(type(block) is tuple and bool(block) for block in section.blocks)
    flat: tuple[object, ...] = ()
    if valid:
        flat = tuple(node for block in section.blocks for node in block)
        valid = all(type(node) is str and bool(node) for node in flat)
        valid = valid and len(set(flat)) == len(flat)
    if not valid:
        logger.error("validate_section_shape invalid section=%r", section)
        raise ValueError("local section requires exact nonempty partition blocks of unique string nods")
    logger.debug("validate_section_shape exit patch=%s nodes=%d", section.patch_name, len(flat))
    return section
