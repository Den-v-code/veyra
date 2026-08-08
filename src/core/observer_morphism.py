"""Provisional P1-A structural observer morphisms over the closed R11 core."""

from __future__ import annotations

from hashlib import sha256
import logging

from .observer_core_codec import decode_observer
from .observer_core_kernel import crest_observer, tail_observer
from .observer_core_semantics import observe
from .observer_core_types import Input, Pair, Ready
from .positive_ontology import internal_observer
from .positive_ontology_doctrine import observer_doctrine
from .positive_ontology_types import ObserverDoctrine
from .observer_morphism_types import (
    ComparisonDomain, InformationLoss, MorphismStatus, ObserverMorphismJudgment,
    ObserverSourceBinding, ProjectionStep, R11DomainProfile,
    ResponseTranslation,
)
from .observer_morphism_validation import (
    ObserverMorphismValidationError, membership_digest,
    snapshot_p1a_identifier, snapshot_projection, snapshot_source_binding,
    snapshot_translation, snapshot_morphism_doctrine,
)
from .observer_morphism_runtime import (
    _build_translation, _check_comparison_witness, _comparison_is_nonempty,
    _minimum_pulse_depth, _observer_member, _recurrence_at_depth,
)
from .observer_morphism_structure import _projection_factorizes

logger = logging.getLogger(__name__)
P1A_DOCTRINE_VERSION = "p1a-v1"


def p1a_observer_morphism_doctrine() -> ObserverDoctrine:
    """Return the fixed coarse/fine R11 doctrine used by P1-A pressure."""
    logger.debug("p1a_observer_morphism_doctrine entry")
    crest, tail = crest_observer(), tail_observer()
    total = Pair(crest, Input())
    nested = Pair(total, Input())
    result = observer_doctrine(
        "P1A-fixed-observer-morphisms",
        "closed-r11-pair-projection",
        (
            "source-fixed", "membership-not-chronology", "no-object-promotion",
            "family-extension-not-refinement",
        ),
        (
            internal_observer("coarse-crest", crest),
            internal_observer("fine-total", total),
            internal_observer("fine-domain-hole", Pair(crest, tail)),
            internal_observer("fine-nested", nested),
            internal_observer("fine-triply-nested", Pair(nested, Input())),
        ),
        version=P1A_DOCTRINE_VERSION,
    )
    logger.debug("p1a_observer_morphism_doctrine exit")
    return result


def observer_source_binding(
    doctrine: ObserverDoctrine, binding_id: str, observer_ids: tuple[str, ...]
) -> ObserverSourceBinding:
    """Bind exact observer membership and immutability, never chronology."""
    logger.debug("observer_source_binding entry")
    doctrine = snapshot_morphism_doctrine(doctrine)
    binding_id = snapshot_p1a_identifier(binding_id, "binding-id")
    if type(observer_ids) is not tuple or not observer_ids:
        logger.error("observer_source_binding invalid member tuple")
        raise ObserverMorphismValidationError("invalid-source-binding-members")
    if len(observer_ids) > len(doctrine.observers):
        logger.error("observer_source_binding member limit")
        raise ObserverMorphismValidationError("source-binding-member-limit")
    ids = tuple(snapshot_p1a_identifier(item, "observer-id") for item in observer_ids)
    if len(set(ids)) != len(ids):
        logger.error("observer_source_binding duplicate member")
        raise ObserverMorphismValidationError("duplicate-source-binding-member")
    members = {item.observer_id: item for item in doctrine.observers}
    if any(item not in members for item in ids):
        logger.error("observer_source_binding nonmember")
        raise ObserverMorphismValidationError("source-binding-nonmember")
    digests = tuple(sha256(members[item].canonical).hexdigest() for item in ids)
    digest = membership_digest(binding_id, doctrine.fingerprint, ids, digests)
    result = ObserverSourceBinding(binding_id, doctrine.fingerprint, ids, digests, digest)
    logger.debug("observer_source_binding exit members=%d", len(ids))
    return result


def r11_domain_profile(
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    observer_id: str,
) -> R11DomainProfile:
    """Derive the exact minimum Pulse depth of one bound R11 observer."""
    logger.debug("r11_domain_profile entry")
    doctrine = snapshot_morphism_doctrine(doctrine)
    binding = snapshot_source_binding(binding, doctrine)
    observer_id = snapshot_p1a_identifier(observer_id, "observer-id")
    if observer_id not in binding.observer_ids:
        logger.error("r11_domain_profile observer unbound")
        raise ObserverMorphismValidationError("domain-profile-source-unbound")
    member = _observer_member(doctrine, observer_id)
    minimum = _minimum_pulse_depth(decode_observer(member.canonical))
    witness = _recurrence_at_depth(minimum)
    if type(observe(decode_observer(member.canonical), witness)) is not Ready:
        logger.error("r11_domain_profile nonempty witness failed")
        raise ObserverMorphismValidationError("domain-profile-witness-failed")
    result = R11DomainProfile(observer_id, minimum, minimum, True)
    logger.debug("r11_domain_profile exit minimum=%d", minimum)
    return result


def observer_morphism_judgment(
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    morphism_id: str,
    fine_observer_id: str,
    coarse_observer_id: str,
    projection: tuple[ProjectionStep, ...],
) -> ObserverMorphismJudgment:
    """Check factorization on C and then the stronger domain inclusion."""
    logger.debug("observer_morphism_judgment entry")
    doctrine = snapshot_morphism_doctrine(doctrine)
    binding = snapshot_source_binding(binding, doctrine)
    morphism_id = snapshot_p1a_identifier(morphism_id, "morphism-id")
    fine_id = snapshot_p1a_identifier(fine_observer_id, "fine-observer-id")
    coarse_id = snapshot_p1a_identifier(coarse_observer_id, "coarse-observer-id")
    projection = snapshot_projection(projection)
    if fine_id not in binding.observer_ids or coarse_id not in binding.observer_ids:
        logger.error("observer_morphism_judgment source unbound")
        raise ObserverMorphismValidationError("morphism-source-unbound")
    fine_member, coarse_member = _observer_member(doctrine, fine_id), _observer_member(doctrine, coarse_id)
    fine_domain = r11_domain_profile(doctrine, binding, fine_id)
    coarse_domain = r11_domain_profile(doctrine, binding, coarse_id)
    comparison_depth = max(fine_domain.minimum_pulse_depth, coarse_domain.minimum_pulse_depth)
    comparison_nonempty = _comparison_is_nonempty(
        fine_member, coarse_member, comparison_depth
    )
    comparison = ComparisonDomain(
        fine_domain.minimum_pulse_depth, coarse_domain.minimum_pulse_depth,
        comparison_depth, comparison_nonempty,
    )
    structural_factorizes = _projection_factorizes(
        doctrine, fine_id, coarse_id, projection
    )
    factorizes = False
    translation: ResponseTranslation | None = None
    witness_checked = False
    if structural_factorizes and comparison.confirmed_nonempty:
        translation = _build_translation(
            morphism_id, doctrine, binding, fine_member, coarse_member, projection
        )
        witness_checked = _check_comparison_witness(
            doctrine, binding, translation, comparison_depth
        )
        factorizes = witness_checked
    domain_inclusion = (
        coarse_domain.minimum_pulse_depth >= fine_domain.minimum_pulse_depth
    )
    if factorizes and domain_inclusion:
        status, obstruction = MorphismStatus.STRONG, ""
    elif factorizes:
        status, obstruction = MorphismStatus.INFORMATION_ONLY, "fine-domain-hole"
    elif not structural_factorizes:
        status = MorphismStatus.INCOMPARABLE
        obstruction = "declared-projection-does-not-factorize"
    elif not comparison.confirmed_nonempty:
        status = MorphismStatus.INCOMPARABLE
        obstruction = "comparison-domain-unconfirmed"
    else:
        status = MorphismStatus.INCOMPARABLE
        obstruction = "comparison-witness-failed"
    if not factorizes:
        information_loss = InformationLoss.UNAVAILABLE
    elif projection:
        information_loss = InformationLoss.DROPS_PAIR_COMPONENTS
    else:
        information_loss = InformationLoss.LOSSLESS_IDENTITY
    result = ObserverMorphismJudgment(
        morphism_id, doctrine.fingerprint, binding.membership_digest,
        fine_id, coarse_id, fine_domain, coarse_domain, comparison, translation,
        factorizes, domain_inclusion, witness_checked, information_loss,
        status, obstruction,
    )
    logger.debug("observer_morphism_judgment exit status=%s", status.value)
    return result


def identity_observer_morphism(
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    morphism_id: str,
    observer_id: str,
) -> ObserverMorphismJudgment:
    """Construct the empty-projection identity with inherited bindings."""
    logger.debug("identity_observer_morphism entry")
    result = observer_morphism_judgment(
        doctrine, binding, morphism_id, observer_id, observer_id, ()
    )
    logger.debug("identity_observer_morphism exit status=%s", result.status.value)
    return result


def compose_observer_morphisms(
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    morphism_id: str,
    fine_to_middle: ResponseTranslation,
    middle_to_coarse: ResponseTranslation,
) -> ObserverMorphismJudgment:
    """Compose exact bound projections without weakening doctrine/domain sources."""
    logger.debug("compose_observer_morphisms entry")
    doctrine = snapshot_morphism_doctrine(doctrine)
    binding = snapshot_source_binding(binding, doctrine)
    first = snapshot_translation(fine_to_middle, doctrine, binding)
    second = snapshot_translation(middle_to_coarse, doctrine, binding)
    if first.coarse_observer_id != second.fine_observer_id:
        logger.error("compose_observer_morphisms middle mismatch")
        raise ObserverMorphismValidationError("morphism-composition-middle-mismatch")
    result = observer_morphism_judgment(
        doctrine, binding, morphism_id, first.fine_observer_id,
        second.coarse_observer_id, first.projection + second.projection,
    )
    logger.debug("compose_observer_morphisms exit status=%s", result.status.value)
    return result
