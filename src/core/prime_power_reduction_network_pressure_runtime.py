"""Typed negative and evidence-absence lanes for P3-N2."""

from __future__ import annotations

import logging

from .observer_network_validation import snapshot_network_source
from .padic_completion import padic_tower_doctrine, prime_source
from .prime_power_reduction_network_common import (
    digest, exact_digest, exact_shape, exact_text, reject,
)
from .prime_power_reduction_network_runtime import (
    _snapshot_package, prime_power_reduction_judgment,
)
from .prime_power_reduction_network_sources import finite_reduction_source
from .prime_power_reduction_network_types import (
    DepthNode, FamilyCoordinate, FiniteFamilySource, FiniteReductionSource,
    N2FormalFailure, N2Open, N2PressureCandidate, N2PressureKind, N2Refutation,
    N2ResourceLimit, PrimePowerReductionJudgment, ReductionArrowSource,
    ReductionRow, ResultStatus,
)

logger = logging.getLogger(__name__)
PRESSURE_VERSION = "p3n2-pressure-v1"
OPEN_REASON = "missing-admissible-symbolic-theorem-source"
def _exact_root(value: int, exponent: int) -> int:
    """Recover an exact positive integer root without floating point."""
    logger.debug("_exact_root entry bits=%d exponent=%d", value.bit_length(), exponent)
    low, high = 1, 1 << ((value.bit_length() + exponent - 1) // exponent)
    while low <= high:
        middle = (low + high) // 2
        power = pow(middle, exponent)
        if power == value:
            logger.debug("_exact_root exit root=%d", middle)
            return middle
        if power < value:
            low = middle + 1
        else:
            high = middle - 1
    reject("n2-finite-first-modulus-not-exact-prime-power")
def _snapshot_admissible_finite(value) -> tuple[object, object, FiniteReductionSource]:
    """Freshly rebuild a finite arithmetic source without symbolic evidence."""
    logger.debug("_snapshot_admissible_finite entry")
    raw = exact_shape(value, FiniteReductionSource, "n2-open-finite")
    exact_text(raw["version"], "n2-open-version")
    exact_text(raw["p3t_version"], "n2-open-p3t-version")
    for name in ("prime_digest", "doctrine_digest", "source_digest"):
        exact_digest(raw[name], f"n2-open-{name}")
    depths, families, arrows = raw["depths"], raw["families"], raw["arrows"]
    if (type(depths) is not tuple or not 1 <= len(depths) <= 32
            or type(families) is not tuple or not 1 <= len(families) <= 1024
            or type(arrows) is not tuple or len(arrows) > 1024):
        reject("n2-open-finite-envelope-invalid")
    if (any(type(x) is not DepthNode for x in depths)
            or any(type(x) is not FiniteFamilySource for x in families)
            or any(type(x) is not ReductionArrowSource for x in arrows)):
        reject("n2-open-finite-member-type-invalid")
    family_rows = tuple(object.__getattribute__(x, "coordinates") for x in families)
    arrow_rows = tuple(object.__getattribute__(x, "rows") for x in arrows)
    if any(type(x) is not tuple for x in (*family_rows, *arrow_rows)):
        reject("n2-open-finite-nested-container-invalid")
    nested = sum(map(len, family_rows)) + sum(map(len, arrow_rows))
    if nested > 100_000:
        reject("n2-open-finite-row-hard-limit")
    for node in depths:
        item = exact_shape(node, DepthNode, "n2-open-depth")
        if (type(item["depth"]) is not int or not 0 <= item["depth"] <= 64
                or type(item["modulus"]) is not int or item["modulus"] < 2
                or item["modulus"].bit_length() > 4096):
            reject("n2-open-depth-value-invalid")
        exact_digest(item["node_digest"], "n2-open-node-digest")
    for family in families:
        item = exact_shape(family, FiniteFamilySource, "n2-open-family")
        exact_text(item["family_id"], "n2-open-family-id")
        if (type(item["integer"]) is not int or item["integer"].bit_length() > 4096
                or type(item["coordinates"]) is not tuple
                or any(type(x) is not FamilyCoordinate for x in item["coordinates"])):
            reject("n2-open-family-value-invalid")
        exact_digest(item["family_digest"], "n2-open-family-digest")
        for coordinate in item["coordinates"]:
            row = exact_shape(coordinate, FamilyCoordinate, "n2-open-coordinate")
            if type(row["depth"]) is not int or type(row["residue"]) is not int:
                reject("n2-open-coordinate-value-invalid")
            exact_digest(row["coordinate_digest"], "n2-open-coordinate-digest")
    for arrow in arrows:
        item = exact_shape(arrow, ReductionArrowSource, "n2-open-arrow")
        if (type(item["fine_depth"]) is not int or type(item["coarse_depth"]) is not int
                or type(item["rows"]) is not tuple
                or any(type(x) is not ReductionRow for x in item["rows"])):
            reject("n2-open-arrow-value-invalid")
        exact_digest(item["arrow_digest"], "n2-open-arrow-digest")
        for reduction in item["rows"]:
            row = exact_shape(reduction, ReductionRow, "n2-open-reduction-row")
            if type(row["source_residue"]) is not int or type(row["target_residue"]) is not int:
                reject("n2-open-reduction-row-value-invalid")
            exact_digest(row["row_digest"], "n2-open-reduction-row-digest")
    first = depths[0]
    p = prime_source(_exact_root(first.modulus, first.depth + 1))
    doctrine = padic_tower_doctrine()
    safe_network = snapshot_network_source(raw["p3t_raw_source"])
    expected = finite_reduction_source(
        p, doctrine, tuple(x.depth for x in depths), tuple(x.integer for x in families),
    )
    if (raw["prime_digest"] != p.source_digest
            or raw["doctrine_digest"] != doctrine.doctrine_digest
            or safe_network != expected.p3t_raw_source or value != expected):
        reject("n2-open-finite-source-drift")
    logger.debug("_snapshot_admissible_finite exit source=%s", expected.source_digest)
    return p, doctrine, expected
def _candidate_digest(kind, finite_digest, family_id, path, source, claimed) -> str:
    """Commit one exact finite counterclaim."""
    logger.debug("_candidate_digest entry kind=%s", kind.value)
    result = digest("veyra.p3n2.pressure-candidate.v1", (
        ("version", PRESSURE_VERSION.encode()), ("kind", kind.value.encode()),
        ("finite", finite_digest.encode()), ("family", str(family_id).encode()),
        *((f"depth-{i}", str(depth).encode()) for i, depth in enumerate(path)),
        ("source", str(source).encode()), ("claimed", str(claimed).encode()),
    ))
    logger.debug("_candidate_digest exit")
    return result
def square_pressure_candidate(raw_finite, family_id: str, fine_depth: int,
                              coarse_depth: int, claimed_target_residue: int):
    """Construct a typed square counterclaim from one admissible finite family."""
    logger.debug("square_pressure_candidate entry")
    _, _, finite = _snapshot_admissible_finite(raw_finite)
    if type(family_id) is not str:
        reject("n2-square-family-id-invalid")
    family = next((x for x in finite.families if x.family_id == family_id), None)
    if family is None:
        reject("n2-square-family-not-declared")
    coordinates = {x.depth: x.residue for x in family.coordinates}
    if (type(fine_depth) is not int or type(coarse_depth) is not int
            or coarse_depth > fine_depth or fine_depth not in coordinates
            or coarse_depth not in coordinates or type(claimed_target_residue) is not int):
        reject("n2-square-endpoints-invalid")
    target_modulus = next(x.modulus for x in finite.depths if x.depth == coarse_depth)
    if not 0 <= claimed_target_residue < target_modulus:
        reject("n2-square-claimed-residue-out-of-range")
    source = coordinates[fine_depth]
    path = (fine_depth, coarse_depth)
    value = _candidate_digest(N2PressureKind.WRONG_SQUARE, finite.source_digest,
                              family_id, path, source, claimed_target_residue)
    result = N2PressureCandidate(PRESSURE_VERSION, N2PressureKind.WRONG_SQUARE,
        finite.source_digest, family_id, path, source, claimed_target_residue, value)
    logger.debug("square_pressure_candidate exit")
    return result
def path_pressure_candidate(raw_finite, path_depths: tuple[int, ...],
                            source_residue: int, claimed_target_residue: int):
    """Construct a typed composable-path counterclaim on the declared tower."""
    logger.debug("path_pressure_candidate entry")
    _, _, finite = _snapshot_admissible_finite(raw_finite)
    declared = {x.depth for x in finite.depths}
    if (type(path_depths) is not tuple or not 2 <= len(path_depths) <= 32
            or any(type(x) is not int or x not in declared for x in path_depths)
            or any(b > a for a, b in zip(path_depths, path_depths[1:]))
            or type(source_residue) is not int or type(claimed_target_residue) is not int):
        reject("n2-path-candidate-invalid")
    source_modulus = next(x.modulus for x in finite.depths if x.depth == path_depths[0])
    target_modulus = next(x.modulus for x in finite.depths if x.depth == path_depths[-1])
    if (not 0 <= source_residue < source_modulus
            or not 0 <= claimed_target_residue < target_modulus):
        reject("n2-path-residue-out-of-range")
    value = _candidate_digest(N2PressureKind.WRONG_PATH, finite.source_digest,
                              None, path_depths, source_residue, claimed_target_residue)
    result = N2PressureCandidate(PRESSURE_VERSION, N2PressureKind.WRONG_PATH,
        finite.source_digest, None, path_depths, source_residue,
        claimed_target_residue, value)
    logger.debug("path_pressure_candidate exit")
    return result
def _snapshot_candidate(package, value, required_kind) -> N2PressureCandidate:
    """Authenticate a candidate only after the package resource lane has run."""
    logger.debug("_snapshot_candidate entry kind=%s", required_kind.value)
    raw = exact_shape(value, N2PressureCandidate, "n2-pressure-candidate")
    if (raw["version"] != PRESSURE_VERSION or type(raw["kind"]) is not N2PressureKind
            or raw["kind"] is not required_kind
            or raw["finite_source_digest"] != package.finite.source_digest):
        reject("n2-pressure-candidate-binding-invalid")
    path = raw["path_depths"]
    declared = {x.depth for x in package.finite.depths}
    if (type(path) is not tuple or not 2 <= len(path) <= 32
            or any(type(x) is not int or x not in declared for x in path)
            or any(b > a for a, b in zip(path, path[1:]))
            or type(raw["source_residue"]) is not int
            or type(raw["claimed_target_residue"]) is not int):
        reject("n2-pressure-candidate-shape-invalid")
    if required_kind is N2PressureKind.WRONG_SQUARE:
        if type(raw["family_id"]) is not str or len(path) != 2:
            reject("n2-square-candidate-shape-invalid")
        exact_text(raw["family_id"], "n2-square-candidate-family")
    elif raw["family_id"] is not None:
        reject("n2-path-family-id-must-be-none")
    target_modulus = next(x.modulus for x in package.finite.depths if x.depth == path[-1])
    source_modulus = next(x.modulus for x in package.finite.depths if x.depth == path[0])
    if (not 0 <= raw["source_residue"] < source_modulus
            or not 0 <= raw["claimed_target_residue"] < target_modulus):
        reject("n2-pressure-residue-out-of-range")
    expected_digest = _candidate_digest(required_kind, raw["finite_source_digest"],
        raw["family_id"], path, raw["source_residue"], raw["claimed_target_residue"])
    exact_digest(raw["candidate_digest"], "n2-pressure-candidate-digest")
    if raw["candidate_digest"] != expected_digest:
        reject("n2-pressure-candidate-digest-mismatch")
    logger.debug("_snapshot_candidate exit")
    return N2PressureCandidate(**raw)
def _refute(raw_package, raw_candidate, required_kind):
    """Give policy refusal precedence, then derive one arithmetic mismatch."""
    logger.debug("_refute entry kind=%s",
                 "dispatch" if required_kind is None else required_kind.value)
    baseline = prime_power_reduction_judgment(raw_package)
    if type(baseline) in (N2ResourceLimit, N2FormalFailure):
        logger.debug("_refute exit operational=%s", type(baseline).__name__)
        return baseline
    if type(baseline) is not PrimePowerReductionJudgment:
        reject("n2-pressure-base-result-invalid")
    package = _snapshot_package(raw_package)
    if required_kind is None:
        kind = exact_shape(raw_candidate, N2PressureCandidate,
                           "n2-pressure-candidate-dispatch")["kind"]
        if type(kind) is not N2PressureKind:
            reject("n2-pressure-candidate-kind-invalid")
        required_kind = kind
    candidate = _snapshot_candidate(package, raw_candidate, required_kind)
    path = candidate.path_depths
    current = candidate.source_residue
    witness_rows = []
    if required_kind is N2PressureKind.WRONG_SQUARE:
        family = next((x for x in package.finite.families
                       if x.family_id == candidate.family_id), None)
        if family is None:
            reject("n2-square-family-not-declared")
        coordinates = {x.depth: x for x in family.coordinates}
        target_modulus = next(
            x.modulus for x in package.finite.depths if x.depth == path[-1]
        )
        if (candidate.source_residue != coordinates[path[0]].residue
                or candidate.source_residue % target_modulus
                != coordinates[path[-1]].residue):
            reject("n2-square-candidate-not-admissible")
        witness_rows.extend((family.family_digest, coordinates[path[0]].coordinate_digest,
                             coordinates[path[-1]].coordinate_digest))
    by_endpoints = {(x.fine_depth, x.coarse_depth): x for x in package.finite.arrows}
    for fine, coarse in zip(path, path[1:]):
        arrow = by_endpoints.get((fine, coarse))
        if arrow is None:
            reject("n2-pressure-path-arrow-missing")
        row = arrow.rows[current]
        if row.source_residue != current:
            reject("n2-pressure-path-row-index-mismatch")
        current = row.target_residue
        witness_rows.extend((arrow.arrow_digest, row.row_digest))
    if current == candidate.claimed_target_residue:
        reject("n2-pressure-candidate-does-not-witness-mismatch")
    witness = digest("veyra.p3n2.pressure-witness.v1", tuple(
        (f"row-{i}", value.encode()) for i, value in enumerate(witness_rows)))
    value = digest("veyra.p3n2.refutation.v1", (
        ("package", package.package_digest.encode()),
        ("candidate", candidate.candidate_digest.encode()),
        ("witness", witness.encode()), ("expected", str(current).encode()),
        ("claimed", str(candidate.claimed_target_residue).encode()),
    ))
    result = N2Refutation(ResultStatus.REFUTED, required_kind, candidate.family_id,
        path, candidate.source_residue, current, candidate.claimed_target_residue,
        package.finite.source_digest, package.package_digest, candidate.candidate_digest,
        witness, value)
    logger.debug("_refute exit expected=%d claimed=%d", current,
                 candidate.claimed_target_residue)
    return result
def refute_pressure_candidate(raw_package, raw_candidate):
    """Dispatch either exact pressure kind after policy refusal precedence."""
    logger.debug("refute_pressure_candidate entry")
    result = _refute(raw_package, raw_candidate, None)
    logger.debug("refute_pressure_candidate exit type=%s", type(result).__name__)
    return result
def refute_wrong_square_candidate(raw_package, raw_candidate):
    """Refute a valid wrong family/reduction square, preserving resource refusal."""
    logger.debug("refute_wrong_square_candidate entry")
    result = _refute(raw_package, raw_candidate, N2PressureKind.WRONG_SQUARE)
    logger.debug("refute_wrong_square_candidate exit type=%s", type(result).__name__)
    return result
def refute_wrong_path_candidate(raw_package, raw_candidate):
    """Refute a valid wrong composable-path value, preserving resource refusal."""
    logger.debug("refute_wrong_path_candidate entry")
    result = _refute(raw_package, raw_candidate, N2PressureKind.WRONG_PATH)
    logger.debug("refute_wrong_path_candidate exit type=%s", type(result).__name__)
    return result


def report_missing_symbolic_evidence(raw_finite) -> N2Open:
    """Classify one freshly rebuilt finite source with absent theorem evidence OPEN."""
    logger.debug("report_missing_symbolic_evidence entry")
    p, doctrine, finite = _snapshot_admissible_finite(raw_finite)
    value = digest("veyra.p3n2.open.v2", (
        ("prime", p.source_digest.encode()), ("doctrine", doctrine.doctrine_digest.encode()),
        ("source", finite.source_digest.encode()),
        ("p3t", finite.p3t_raw_source.network_digest.encode()), ("reason", OPEN_REASON.encode()),
    ))
    result = N2Open(ResultStatus.OPEN, OPEN_REASON, p.source_digest,
        doctrine.doctrine_digest, finite.source_digest,
        finite.p3t_raw_source.network_digest, value)
    logger.debug("report_missing_symbolic_evidence exit")
    return result
