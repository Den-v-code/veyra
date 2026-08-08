"""Twenty-three executed mutation and semantic probes for P3-N2."""

from __future__ import annotations

from dataclasses import replace
import logging

from .observer_network import observer_network_judgment
from .padic_completion import prime_source
from .prime_power_reduction_network_common import PrimePowerReductionValidationError
from .prime_power_reduction_network_runtime import prime_power_reduction_judgment
from .prime_power_reduction_network_sources import finite_reduction_source, reduction_network_package
from .prime_power_reduction_network_types import (
    FiniteRelation, N2ResourceLimit, PrimePowerReductionJudgment, ResultStatus,
)
from .prime_power_reduction_network_validation import validate_prime_power_reduction_result

logger = logging.getLogger(__name__)
ATTACK_LABELS = (
    "reversed-map", "forged-m>n", "foreign-prime", "caller-table",
    "bounded-composition", "omitted-triangle", "intersection-promotion",
    "preservation-to-reflection", "strict-without-separator", "collapsing-separator",
    "finite-to-all-family", "resource-changes-symbolic", "completion-judgment-premise",
    "prior-p3t-judgment", "bounded-paths-only", "carry-confusion", "chosen-lift-inverse",
    "transplanted-source", "digest-not-map-equality", "generic-p3c2-relabel",
    "comparison-proof-dependence", "failure-normalized", "unregistered-p2s-promotion",
)


def _rejected(package) -> bool:
    """Execute a malformed-package replay and require the local typed rejection."""
    logger.debug("_rejected entry")
    try:
        prime_power_reduction_judgment(package)
    except PrimePowerReductionValidationError:
        logger.debug("_rejected exit result=True")
        return True
    logger.debug("_rejected exit result=False")
    return False


def _claim_rejected(package, claim) -> bool:
    """Execute fresh result validation and require hostile-claim rejection."""
    logger.debug("_claim_rejected entry")
    try:
        validate_prime_power_reduction_result(package, claim)
    except PrimePowerReductionValidationError:
        logger.debug("_claim_rejected exit result=True")
        return True
    logger.debug("_claim_rejected exit result=False")
    return False


def _package_with(package, finite):
    """Bind an independently constructed finite source into the exact N2 envelope."""
    logger.debug("_package_with entry")
    result = reduction_network_package(package.prime, package.doctrine, finite,
        package.n1_theorem, package.theorem, package.ledger, package.policy)
    logger.debug("_package_with exit")
    return result


def required_n2_attacks(package, result, refusal) -> tuple[tuple[str, bool], ...]:
    """Execute every mandatory attack rather than checking descriptive flags."""
    logger.debug("required_n2_attacks entry")
    if type(result) is not PrimePowerReductionJudgment:
        return tuple((label, False) for label in ATTACK_LABELS)
    arrows = package.finite.arrows
    source_arrow = arrows[1]
    reversed_arrow = replace(source_arrow, fine_depth=source_arrow.coarse_depth,
                             coarse_depth=source_arrow.fine_depth)
    reversed_source = replace(package.finite, arrows=(arrows[0], reversed_arrow, *arrows[2:]))
    reversed_rejected = _rejected(replace(package, finite=reversed_source))
    impossible_arrow = replace(source_arrow, coarse_depth=source_arrow.fine_depth + 1)
    impossible_source = replace(package.finite,
        arrows=(arrows[0], impossible_arrow, *arrows[2:]))
    impossible_rejected = _rejected(replace(package, finite=impossible_source))

    foreign = prime_source(3)
    foreign_finite = finite_reduction_source(foreign, package.doctrine,
        tuple(x.depth for x in package.finite.depths))
    foreign_bound = (foreign_finite.p3t_raw_source.network_digest
                     != package.finite.p3t_raw_source.network_digest)
    foreign_transplant = _rejected(replace(package, prime=foreign))

    bad_row = replace(source_arrow.rows[0], target_residue=1)
    bad_arrow = replace(source_arrow, rows=(bad_row, *source_arrow.rows[1:]))
    table_source = replace(package.finite, arrows=(arrows[0], bad_arrow, *arrows[2:]))
    table_rejected = _rejected(replace(package, finite=table_source))
    direct = arrows[3]
    bad_direct = replace(direct, rows=(replace(direct.rows[0], target_residue=1),
                                      *direct.rows[1:]))
    composition_source = replace(package.finite,
        arrows=(*arrows[:3], bad_direct, *arrows[4:]))
    composition_rejected = _rejected(replace(package, finite=composition_source))

    p3t = package.finite.p3t_raw_source
    no_triangle = replace(p3t, triangles=())
    omitted_rejected = _rejected(replace(package,
        finite=replace(package.finite, p3t_raw_source=no_triangle)))
    partial_triangle = replace(p3t.triangles[0], indirect_edge_ids=("reduce-2-to-1",))
    partial_source = replace(p3t, triangles=(partial_triangle,))
    partial_rejected = _rejected(replace(package,
        finite=replace(package.finite, p3t_raw_source=partial_source)))

    reflected = replace(result.finite_arrows[1], preservation=False)
    reflection_rejected = _claim_rejected(package, replace(result,
        finite_arrows=(result.finite_arrows[0], reflected, *result.finite_arrows[2:])))
    depths = tuple(x.depth for x in package.finite.depths)
    sparse = _package_with(package, finite_reduction_source(package.prime,
        package.doctrine, depths, (0,)))
    sparse_result = prime_power_reduction_judgment(sparse)
    collapse_integer = package.prime.p ** (depths[-1] + 1)
    collapsing = _package_with(package, finite_reduction_source(package.prime,
        package.doctrine, depths, (0, collapse_integer)))
    collapsing_result = prime_power_reduction_judgment(collapsing)
    sparse_open = [x for x in sparse_result.finite_arrows if x.fine_depth > x.coarse_depth]
    collapse_open = [x for x in collapsing_result.finite_arrows if x.fine_depth > x.coarse_depth]
    fake_strict = replace(sparse_result.finite_arrows[1],
        relation=FiniteRelation.STRICT_REFINEMENT_ON_EXACT_FINITE_SCOPE,
        separator_family_ids=("family-0", "family-0"))
    promotion_rejected = _claim_rejected(sparse, replace(sparse_result,
        finite_arrows=(sparse_result.finite_arrows[0], fake_strict,
                       *sparse_result.finite_arrows[2:])))

    prior = observer_network_judgment(p3t)
    prior_rejected = _rejected(replace(package,
        finite=replace(package.finite, p3t_raw_source=prior)))
    coordinate = package.finite.families[0].coordinates[-1]
    bad_coordinate = replace(coordinate, residue=coordinate.residue + 1)
    bad_family = replace(package.finite.families[0],
        coordinates=(*package.finite.families[0].coordinates[:-1], bad_coordinate))
    carry_rejected = _rejected(replace(package, finite=replace(package.finite,
        families=(bad_family, *package.finite.families[1:]))))
    transplant = replace(package.theorem, artifact_sha256="0" * 64)
    transplant_rejected = _rejected(replace(package, theorem=transplant))
    bad_translation = replace(p3t.translations[0], translation_digest="0" * 64)
    map_digest_rejected = _rejected(replace(package, finite=replace(package.finite,
        p3t_raw_source=replace(p3t, translations=(bad_translation, *p3t.translations[1:])))))

    path_direct = tuple(x.target_residue for x in arrows[3].rows)
    first = {x.source_residue: x.target_residue for x in arrows[4].rows}
    second = {x.source_residue: x.target_residue for x in arrows[1].rows}
    path_composed = tuple(second[first[x]] for x in range(len(path_direct)))
    wrong_path_detected = path_direct == path_composed and tuple(
        (x + 1) % package.prime.p for x in path_composed) != path_direct
    inverse_claim_rejected = _claim_rejected(package, replace(result,
        nonclaims=tuple(x for x in result.nonclaims if x != "coarse-to-fine-inverse")))
    p3c2_rejected = _claim_rejected(package, replace(result, p3c2_status_consumed=True))
    proof_rejected = _claim_rejected(package, replace(result,
        theorem_ids=(result.theorem_ids[1], result.theorem_ids[0], *result.theorem_ids[2:])))
    failure_separated = (type(refusal) is N2ResourceLimit
        and refusal.status is ResultStatus.RESOURCE_LIMIT and table_rejected)
    promotion_count_rejected = _claim_rejected(package, replace(result, promotions=1))
    checks = (
        reversed_rejected, impossible_rejected, foreign_bound and foreign_transplant,
        table_rejected, composition_rejected, omitted_rejected, partial_rejected,
        reflection_rejected,
        bool(sparse_open) and all(x.relation is FiniteRelation.OPEN for x in sparse_open),
        bool(collapse_open) and all(x.relation is FiniteRelation.OPEN for x in collapse_open),
        promotion_rejected, type(refusal) is N2ResourceLimit and result.promotions == 0,
        _rejected(replace(package, n1_theorem=package.theorem)), prior_rejected,
        wrong_path_detected, carry_rejected, inverse_claim_rejected, transplant_rejected,
        map_digest_rejected, p3c2_rejected, proof_rejected, failure_separated,
        promotion_count_rejected,
    )
    rows = tuple(zip(ATTACK_LABELS, checks, strict=True))
    logger.debug("required_n2_attacks exit passed=%d", sum(ok for _, ok in rows))
    return rows
