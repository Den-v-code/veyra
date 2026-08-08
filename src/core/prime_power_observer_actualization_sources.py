"""Exact doctrine, raw packages, bridge, scope, and envelope for P3-N0."""

from __future__ import annotations

import logging

from .observer_network_preflight import network_resource_policy
from .padic_completion_doctrine import padic_tower_doctrine
from .padic_completion_prime import prime_source
from .padic_family_introduction import (
    integer_source, n1_assumption_ledger, n1_introduction_package, n1_policy,
    n1_theorem_source,
)
from .prime_power_observer_actualization_common import (
    N0ValidationError, digest, exact_int, exact_text, indexed, reject,
)
from .prime_power_observer_actualization_attestation import n0_theorem_source
from .prime_power_observer_actualization_bridge import family_finite_bridge
from .prime_power_observer_actualization_ledgers import (
    history_ledger, postbirth_ledger, prebirth_ledger,
)
from .prime_power_observer_actualization_types import (
    DoctrineAdmission, N0Policy, N0Source, N2FPackage,
    PrimePowerObserverDoctrine, RhoObserverScope,
    SuffixSelector,
)
from .prime_power_reduction_network import (
    exact_n1_theorem_source, finite_reduction_source, n2_ledger, n2_policy,
    reduction_network_package, theorem_source,
)

logger = logging.getLogger(__name__)

PRINCIPLE_FAMILY_ID = "OAP-observer-actualization-principle-family-v1"
PRINCIPLE_ID = "A-HAP-sufficient-model-relative-arithmetic-v1"
PREMISES = (
    "strict-past-raw-rho-genealogy", "doctrine-admitted-before-birth",
    "fresh-F0-F1-discrimination", "same-token-postbirth-persistence",
    "later-N2F-selector-causal-efficacy", "first-birth-pretoken-key",
)
HARD_CAPS = (64, 4096, 65, 4096, 64, 256, 128, 8192, 1024, 100_000, 1024,
             64, 2 * 1024 * 1024, 8 * 1024 * 1024, 4 * 1024 * 1024, 300)


def observer_doctrine(admitted: bool = True) -> PrimePowerObserverDoctrine:
    """Elect A-HAP as one sufficient arithmetic-history doctrine."""
    logger.debug("observer_doctrine entry admitted=%r", admitted)
    if type(admitted) is not bool:
        reject("n0-doctrine-admission-bool-required")
    admission = DoctrineAdmission.ADMITTED if admitted else DoctrineAdmission.NOT_ADMITTED
    value = digest("veyra.p3n0.doctrine.v1", (
        ("principle-family", PRINCIPLE_FAMILY_ID.encode()),
        ("principle", PRINCIPLE_ID.encode()), ("admission", admission.value.encode()),
        *indexed("premise", PREMISES),
    ))
    result = PrimePowerObserverDoctrine(
        "p3n0-doctrine-v1", PRINCIPLE_FAMILY_ID, PRINCIPLE_ID, admission, "exact-prime-source",
        "prime-power-residue-tower", "fresh-N1-integer-families", PREMISES, value,
    )
    logger.debug("observer_doctrine exit admission=%s", admission.value)
    return result


def n0_policy(
    max_depth=16, max_integer_bits=4096, max_exponent=18,
    max_modulus_bits=1024, max_events=48, max_parent_edges=160,
    max_access_edges=64, max_evaluations=256, max_families=3,
    max_finite_rows=100_000, max_reductions=6, max_assumptions=8,
    max_ledger_bytes=1024 * 1024, max_captured_bytes=4 * 1024 * 1024,
    max_output_bytes=1024 * 1024, timeout_seconds=120,
) -> N0Policy:
    """Construct caps checked before exponentiation, capture, or graph walks."""
    logger.debug("n0_policy entry")
    values = (max_depth, max_integer_bits, max_exponent, max_modulus_bits,
              max_events, max_parent_edges, max_access_edges, max_evaluations,
              max_families, max_finite_rows, max_reductions,
              max_assumptions, max_ledger_bytes,
              max_captured_bytes, max_output_bytes, timeout_seconds)
    if any(type(v) is not int or not 1 <= v <= cap
           for v, cap in zip(values, HARD_CAPS, strict=True)):
        reject("n0-policy-invalid")
    value = digest("veyra.p3n0.policy.v1", indexed("cap", values))
    result = N0Policy("p3n0-policy-v1", *values, value)
    logger.debug("n0_policy exit")
    return result


def _n1_package(prime, doctrine, z):
    """Construct one complete raw N1 input without a prior result."""
    logger.debug("_n1_package entry z_bits=%d", z.bit_length())
    result = n1_introduction_package(
        prime, integer_source(z), doctrine, n1_theorem_source(),
        n1_assumption_ledger(), n1_policy(),
    )
    logger.debug("_n1_package exit")
    return result


def _n2_wrapper(prime, doctrine, depths, integers, selector):
    """Construct one complete N2-F lane plus its exact sibling P3-T policy."""
    logger.debug("_n2_wrapper entry selector=%s", selector.value)
    finite = finite_reduction_source(prime, doctrine, depths, integers)
    raw = reduction_network_package(
        prime, doctrine, finite, exact_n1_theorem_source(), theorem_source(),
        n2_ledger(), n2_policy(),
    )
    network_policy = network_resource_policy()
    value = digest("veyra.p3n0.n2f-wrapper.v1", (
        ("selector", selector.value.encode()), ("package", raw.package_digest.encode()),
        ("network", finite.p3t_raw_source.network_digest.encode()),
        *indexed("network-cap", network_policy.__dict__.values()),
    ))
    result = N2FPackage(selector, raw, finite.p3t_raw_source, network_policy, value)
    logger.debug("_n2_wrapper exit selector=%s", selector.value)
    return result


def _scope(depth, family_ids, strict, open_lane):
    """Precommit the union of both counterfactual packages and selectors."""
    logger.debug("_scope entry depth=%d", depth)
    depths = (depth, depth + 1)
    packages = (strict.wrapper_digest, open_lane.wrapper_digest)
    selectors = (SuffixSelector.STRICT_SUFFIX, SuffixSelector.OPEN_SUFFIX)
    value = digest("veyra.p3n0.scope.v1", (
        *indexed("family", family_ids), *indexed("package", packages),
        *indexed("selector", (x.value for x in selectors)), *indexed("depth", depths),
        ("arrow", f"{depth + 1}->{depth}".encode()),
    ))
    result = RhoObserverScope(family_ids, packages, selectors, depths,
                              (depth + 1, depth), value)
    logger.debug("_scope exit")
    return result


def exact_n0_source(p=2, n=0, lineage_id="n0-lineage-alpha", *, policy=None,
                    admitted=True) -> N0Source:
    """Build the exact three-N1/two-N2-F raw experiment after hard scalar checks."""
    logger.debug("exact_n0_source entry p=%r n=%r", p, n)
    p = exact_int(p, "prime", minimum=2, maximum=65521)
    n = exact_int(n, "depth", maximum=64)
    lineage_id = exact_text(lineage_id, "lineage")
    if type(admitted) is not bool:
        reject("n0-source-admission-bool-required")
    policy = n0_policy() if policy is None else policy
    if type(policy) is not N0Policy:
        reject("n0-policy-exact-type-required")
    caps = tuple(getattr(policy, name) for name in (
        "max_depth", "max_integer_bits", "max_exponent", "max_modulus_bits",
        "max_events", "max_parent_edges", "max_access_edges", "max_evaluations",
        "max_families", "max_finite_rows", "max_reductions",
        "max_assumptions", "max_ledger_bytes",
        "max_captured_bytes", "max_output_bytes", "timeout_seconds",
    ))
    if policy != n0_policy(*caps):
        reject("n0-policy-drift")
    if n > policy.max_depth or n + 2 > policy.max_exponent:
        reject("n0-source-depth-policy-refusal-use-runtime")
    if (n + 2) * p.bit_length() > policy.max_modulus_bits:
        reject("n0-source-modulus-policy-refusal-use-runtime")
    if (n + 1) * p.bit_length() > policy.max_integer_bits:
        reject("n0-source-integer-policy-refusal-use-runtime")
    static_required = (
        (26, policy.max_events), (26, policy.max_parent_edges),
        (18, policy.max_access_edges), (16, policy.max_evaluations),
        (3, policy.max_families), (6, policy.max_reductions),
        (len(PREMISES), policy.max_assumptions), (16 * 1024, policy.max_ledger_bytes),
    )
    if any(required > allowed for required, allowed in static_required):
        reject("n0-source-static-policy-refusal-use-runtime")
    fine, coarse = 1, 1
    for _ in range(n + 2):
        fine = min(policy.max_finite_rows + 1, fine * p)
    for _ in range(n + 1):
        coarse = min(policy.max_finite_rows + 1, coarse * p)
    if min(policy.max_finite_rows + 1, 2 * (coarse + 2 * fine)) > policy.max_finite_rows:
        reject("n0-source-finite-row-policy-refusal-use-runtime")
    try:
        prime, tower = prime_source(p), padic_tower_doctrine()
        separator = p ** (n + 1)
        if separator.bit_length() > policy.max_integer_bits:
            reject("n0-source-integer-policy-refusal-use-runtime")
        depths = (n, n + 1)
        n1s = tuple(_n1_package(prime, tower, z) for z in (0, 1, separator))
        strict = _n2_wrapper(prime, tower, depths, (0, separator), SuffixSelector.STRICT_SUFFIX)
        open_lane = _n2_wrapper(prime, tower, depths, (0,), SuffixSelector.OPEN_SUFFIX)
        bridge = family_finite_bridge(n1s, strict, open_lane, depths)
    except N0ValidationError:
        raise
    except Exception as exc:
        logger.exception("exact_n0_source foreign raw builder rejection")
        reject(f"n0-raw-builder-rejected-{type(exc).__name__}")
    family_ids = ("integer:0", "integer:1", f"integer:{separator}")
    scope = _scope(n, family_ids, strict, open_lane)
    doctrine = observer_doctrine(admitted)
    theorem = n0_theorem_source()
    ledgers = (prebirth_ledger(admitted), postbirth_ledger(admitted),
               history_ledger(admitted))
    value = digest("veyra.p3n0.source.v1", (
        ("p", str(p).encode()), ("n", str(n).encode()), ("lineage", lineage_id.encode()),
        ("doctrine", doctrine.doctrine_digest.encode()), ("policy", policy.policy_digest.encode()),
        ("n0-theorem", theorem.source_digest.encode()),
        *indexed("n1", (x.package_digest for x in n1s)),
        ("bridge", bridge.bridge_digest.encode()), ("strict", strict.wrapper_digest.encode()),
        ("open", open_lane.wrapper_digest.encode()), ("scope", scope.scope_digest.encode()),
        *indexed("ledger", (x.ledger_digest for x in ledgers)),
    ))
    result = N0Source(p, n, lineage_id, doctrine, policy, theorem, n1s, bridge, strict,
                      open_lane, scope, *ledgers, value)
    logger.debug("exact_n0_source exit")
    return result
