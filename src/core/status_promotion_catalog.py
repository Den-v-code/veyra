"""Frozen P2-S1 kind/status matrix, promotion rules, and bounded schemas."""

from __future__ import annotations

import logging

from .status_promotion_digest import digest, frame, nested_rows, text_rows
from .status_promotion_schema_catalog import schema_targets
from .status_promotion_projection_commitment import premise_projection_digest
from .status_promotion_types import (
    EvidenceStatus as S, IndexProjectionRule, JudgmentKind as K, KindStatusDomain,
    PositiveProvenance as P, PremiseProjectionRule, PremiseSignature,
    PromotionRegistry, PromotionRule, StatusProvenancePair,
)

logger = logging.getLogger(__name__)
REGISTRY_VERSION = "p2-s-promotion-registry-v1"
ASSUMPTION_POLICY_ID = "p2-s-acyclic-no-own-conclusion-v1"
FORBIDDEN_SOURCE_TYPES = (
    "bool", "digest-only", "old-certificate", "old-judgment", "finite-sample-table",
)
FORBIDDEN_CONCLUSION_FIELDS = (
    "exists", "global_exists", "metaphysically_exists", "proof_complete",
    "observer_independent", "physical_exists",
)
NONCLAIMS = (
    "ontology-completeness", "codebase-completeness", "retroactive-certification",
    "metaphysical-truth", "automatic-promotion",
)
_SCOPE_KINDS = (
    K.OBSERVABLE, K.GENERABLE, K.COHERENT, K.PERSISTENT,
    K.CONFLUENT, K.REFINEMENT_ROBUST,
)


def _pair(status: S, provenance: P) -> StatusProvenancePair:
    logger.debug("_pair entry")
    result = StatusProvenancePair(status, provenance)
    logger.debug("_pair exit")
    return result


def _domain(kind: K, statuses: tuple[S, ...], pairs: tuple[StatusProvenancePair, ...]):
    logger.debug("_domain entry kind=%s", kind.value)
    value = digest("veyra.p2s.kind-domain.v1", (
        ("kind", kind.value.encode()),
        *text_rows("status", tuple(item.value for item in statuses)),
        *nested_rows("pair", tuple(frame("veyra.p2s.status-pair.v1", (
            ("status", item.status.value.encode()),
            ("provenance", item.provenance.value.encode()),
        )) for item in pairs)),
    ))
    result = KindStatusDomain(kind, statuses, pairs, value)
    logger.debug("_domain exit")
    return result


def _domains() -> tuple[KindStatusDomain, ...]:
    logger.debug("_domains entry")
    scope_statuses = (S.ESTABLISHED_RELATIVE_TO_SCOPE, S.REFUTED, S.OPEN)
    scope_pairs = (
        _pair(S.ESTABLISHED_RELATIVE_TO_SCOPE, P.EXECUTABLE_REPLAY),
        _pair(S.ESTABLISHED_RELATIVE_TO_SCOPE, P.FORMALLY_DERIVED),
    )
    by_kind = {
        K.PRESENTED: ((S.ESTABLISHED, S.OPEN), (_pair(S.ESTABLISHED, P.SUPPLIED_PRESENTATION),)),
        K.ADMISSIBLE: (
            (S.ESTABLISHED_RELATIVE_TO_DOCTRINE, S.REFUTED, S.OPEN),
            (_pair(S.ESTABLISHED_RELATIVE_TO_DOCTRINE, P.DOCTRINE_REPLAY),),
        ),
        **{kind: (scope_statuses, scope_pairs) for kind in _SCOPE_KINDS},
        K.OBSERVER_ROLE: (
            (S.ESTABLISHED_RELATIVE_TO_SCOPE, S.OPEN),
            (_pair(S.ESTABLISHED_RELATIVE_TO_SCOPE, P.DOCTRINE_REPLAY),),
        ),
        K.HISTORICALLY_ACTUALIZED: (
            (S.ESTABLISHED_RELATIVE_TO_HISTORY, S.OPEN),
            (_pair(S.ESTABLISHED_RELATIVE_TO_HISTORY, P.HISTORICAL_REPLAY),),
        ),
        K.SCOPED_OBJECT: (
            (S.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE, S.REFUTED, S.OPEN),
            (_pair(S.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE, P.DOCTRINE_REPLAY),),
        ),
        K.ALL_DEPTH_FAMILY: (
            (S.ESTABLISHED_RELATIVE_TO_LEDGER, S.ASSUMED, S.OPEN),
            (_pair(S.ESTABLISHED_RELATIVE_TO_LEDGER, P.FORMALLY_DERIVED),
             _pair(S.ASSUMED, P.SUPPLIED_HYPOTHESIS),
             _pair(S.ASSUMED, P.ORACLE_DEPENDENT)),
        ),
        K.COMPLETED_CARRIER: (
            (S.ESTABLISHED_RELATIVE_TO_LEDGER, S.REFUTED, S.OPEN),
            (_pair(S.ESTABLISHED_RELATIVE_TO_LEDGER, P.FORMALLY_DERIVED),),
        ),
        K.OBJECTIVELY_STABLE: (
            (S.ESTABLISHED_RELATIVE_TO_NETWORK, S.REFUTED, S.OPEN),
            (_pair(S.ESTABLISHED_RELATIVE_TO_NETWORK, P.EXECUTABLE_REPLAY),
             _pair(S.ESTABLISHED_RELATIVE_TO_NETWORK, P.FORMALLY_DERIVED)),
        ),
        K.PHYSICALLY_INSTANTIATED: (
            (S.ESTABLISHED_RELATIVE_TO_EMPIRICAL_BRIDGE, S.REFUTED, S.OPEN),
            (_pair(S.ESTABLISHED_RELATIVE_TO_EMPIRICAL_BRIDGE, P.EMPIRICAL_BRIDGE),),
        ),
    }
    result = tuple(_domain(kind, *by_kind[kind]) for kind in K)
    logger.debug("_domains exit count=%d", len(result))
    return result


def _premise(name: str, kind: str, fields: tuple[str, ...], indices: tuple[str, ...]):
    logger.debug("_premise entry name=%s", name)
    result = PremiseSignature(name, kind, fields, indices)
    logger.debug("_premise exit")
    return result


_RULE_ROWS = (
    ("exact-snapshot-v1", K.PRESENTED, S.ESTABLISHED, P.SUPPLIED_PRESENTATION, ("scope",),
     (("representation", "bounded-representation", ("canonical",), ("scope",)),)),
    ("doctrine-admission-v1", K.ADMISSIBLE, S.ESTABLISHED_RELATIVE_TO_DOCTRINE,
     P.DOCTRINE_REPLAY, ("doctrine", "scope"),
     (("presentation", "presentation-artifact", ("canonical",), ("scope",)),
      ("doctrine", "doctrine-replay", ("admission",), ("doctrine",)))),
    ("observer-execution-v1", K.OBSERVABLE, S.ESTABLISHED_RELATIVE_TO_SCOPE,
     P.EXECUTABLE_REPLAY, ("doctrine", "scope", "observer"),
     (("coupling", "admitted-coupling", ("response",), ("doctrine", "observer")),
      ("input", "exact-input", ("input",), ("scope",)))),
    ("p1-b-finite-generation-v1", K.GENERABLE, S.ESTABLISHED_RELATIVE_TO_SCOPE,
     P.EXECUTABLE_REPLAY, ("doctrine", "scope", "stage"),
     (("seed", "seed-source", ("seed",), ("doctrine",)),
      ("program", "closed-program", ("replay",), ("scope", "stage")))),
    ("compatibility-replay-v1", K.COHERENT, S.ESTABLISHED_RELATIVE_TO_SCOPE,
     P.EXECUTABLE_REPLAY, ("doctrine", "scope"),
     (("relations", "exact-relations", ("relation-laws",), ("doctrine", "scope")),
      ("restrictions", "exact-restrictions", ("restriction-laws",), ("scope",)))),
    ("continuation-replay-v1", K.PERSISTENT, S.ESTABLISHED_RELATIVE_TO_SCOPE,
     P.EXECUTABLE_REPLAY, ("doctrine", "scope", "history"),
     (("trace", "trace-artifact", ("trace",), ("history",)),
      ("continuation", "named-continuation", ("persistence",), ("scope",)))),
    ("oep-observer-role-v1", K.OBSERVER_ROLE, S.ESTABLISHED_RELATIVE_TO_SCOPE,
     P.DOCTRINE_REPLAY, ("doctrine", "scope", "observer"),
     tuple((name, f"oep-{name}", (name,), ("scope", "observer")) for name in
           ("genealogy", "recurrence", "discrimination", "persistence", "efficacy"))),
    ("hap-historical-actualization-v1", K.HISTORICALLY_ACTUALIZED,
     S.ESTABLISHED_RELATIVE_TO_HISTORY, P.HISTORICAL_REPLAY,
     ("doctrine", "scope", "history", "observer"),
     (("oep", "observer-role-artifact", ("role",), ("doctrine", "scope", "observer")),
      ("history", "birth-history", ("prior-history", "causal-pressure"), ("history",)))),
    ("c2-c3-confluence-v1", K.CONFLUENT, S.ESTABLISHED_RELATIVE_TO_SCOPE,
     P.EXECUTABLE_REPLAY, ("doctrine", "scope", "history"),
     (("diagrams", "demanded-path-diagrams", ("coverage", "commutation"),
       ("doctrine", "scope", "history")),)),
    ("a2-refinement-survival-v1", K.REFINEMENT_ROBUST, S.ESTABLISHED_RELATIVE_TO_SCOPE,
     P.EXECUTABLE_REPLAY, ("doctrine", "scope", "refinement"),
     (("refinement", "genuine-refinement", ("strictness", "survival"),
       ("doctrine", "scope", "refinement")),)),
    ("sfp-scoped-formation-v1", K.SCOPED_OBJECT, S.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE,
     P.DOCTRINE_REPLAY, ("doctrine", "scope", "history"),
     tuple((name, f"sfp-{name}", (name,), ("doctrine", "scope")) for name in
           ("construction", "support", "g4", "persistence", "confluence", "refinement"))),
    ("afip-formally-derived-v1", K.ALL_DEPTH_FAMILY, S.ESTABLISHED_RELATIVE_TO_LEDGER,
     P.FORMALLY_DERIVED, ("doctrine", "ledger", "family"),
     (("totality", "formal-totality-source", ("theorem", "formal-source"), ("ledger",)),
      ("restriction", "formal-restriction-laws", ("theorem",), ("family",)),
      ("ledger", "assumption-ledger", ("closure",), ("ledger",)))),
    ("afip-supplied-hypothesis-v1", K.ALL_DEPTH_FAMILY, S.ASSUMED,
     P.SUPPLIED_HYPOTHESIS, ("doctrine", "ledger", "family"),
     (("hypothesis", "supplied-family-hypothesis", ("totality", "compatibility"),
       ("ledger", "family")),)),
    ("afip-oracle-hypothesis-v1", K.ALL_DEPTH_FAMILY, S.ASSUMED,
     P.ORACLE_DEPENDENT, ("doctrine", "ledger", "family"),
     (("oracle", "total-oracle-hypothesis", ("totality", "purity", "stability", "trust"),
       ("ledger", "family")),)),
    ("pomega-carrier-completion-v1", K.COMPLETED_CARRIER,
     S.ESTABLISHED_RELATIVE_TO_LEDGER, P.FORMALLY_DERIVED,
     ("doctrine", "ledger", "carrier"),
     (("carrier", "carrier-formation", ("constructor",), ("carrier",)),
      ("realization", "universal-realization", ("theorem",), ("ledger", "carrier")),
      ("separation", "joint-separation", ("theorem",), ("carrier",)),
      ("nonvacuity", "family-class-witness", ("witness",), ("ledger",)))),
    ("network-invariance-v1", K.OBJECTIVELY_STABLE, S.ESTABLISHED_RELATIVE_TO_NETWORK,
     P.EXECUTABLE_REPLAY, ("doctrine", "scope", "network", "history"),
     (("translations", "network-translations", ("preservation", "reflection", "domain"),
       ("network",)), ("confluence", "network-confluence", ("all-demanded",), ("history",)),
      ("refinements", "network-refinements", ("survival", "no-conflict"), ("scope",)))),
    ("empirical-bridge-v1", K.PHYSICALLY_INSTANTIATED,
     S.ESTABLISHED_RELATIVE_TO_EMPIRICAL_BRIDGE, P.EMPIRICAL_BRIDGE,
     ("doctrine", "scope", "measurement"),
     (("measurement", "external-measurement", ("measurement", "provenance"),
       ("measurement",)), ("bridge", "empirical-doctrine", ("identification",),
       ("doctrine", "scope")))),
)


def _rule(row: tuple) -> PromotionRule:
    logger.debug("_rule entry rule=%s", row[0])
    rule_id, kind, status, provenance, indices, premise_rows = row
    premises = tuple(_premise(*premise_row) for premise_row in premise_rows)
    statement = digest("veyra.p2s.rule-statement.v1", (
        ("rule-id", rule_id.encode()),
        ("statement", f"named-introduction:{rule_id}".encode()),
    ))
    premise_frames = tuple(frame("veyra.p2s.premise-signature.v1", (
        ("name", item.premise_name.encode()),
        ("artifact-kind", item.artifact_kind.encode()),
        *text_rows("evidence", item.required_evidence_fields),
        *text_rows("index", item.required_indices),
    )) for item in premises)
    value = digest("veyra.p2s.promotion-rule.v1", (
        ("rule-id", rule_id.encode()), ("statement", statement.encode()),
        *nested_rows("premise", premise_frames),
        ("output-kind", kind.value.encode()), ("output-status", status.value.encode()),
        ("output-provenance", provenance.value.encode()),
        *text_rows("output-index", indices),
        *text_rows("forbidden-source", FORBIDDEN_SOURCE_TYPES),
        *text_rows("forbidden-conclusion", FORBIDDEN_CONCLUSION_FIELDS),
        ("assumption-policy", ASSUMPTION_POLICY_ID.encode()),
        *text_rows("nonclaim", NONCLAIMS),
    ))
    result = PromotionRule(
        rule_id, statement, premises, kind, status, provenance, indices,
        FORBIDDEN_SOURCE_TYPES, FORBIDDEN_CONCLUSION_FIELDS,
        ASSUMPTION_POLICY_ID, NONCLAIMS, value,
    )
    logger.debug("_rule exit rule=%s", rule_id)
    return result


def _premise_projections(rules: tuple[PromotionRule, ...]):
    logger.debug("_premise_projections entry rules=%d", len(rules))
    result = tuple(
        PremiseProjectionRule(
            projection_id, rule.rule_id, premise.premise_name,
            premise_projection_digest(projection_id, rule.rule_id, premise.premise_name),
        )
        for rule in rules for premise in rule.premise_signatures
        for projection_id in (f"p2-project-{rule.rule_id}-{premise.premise_name}-v1",)
    )
    logger.debug("_premise_projections exit rows=%d", len(result))
    return result


def _index_projections() -> tuple[IndexProjectionRule, ...]:
    logger.debug("_index_projections entry")
    projection_id = "p2-exists-generable-stage-v1"
    input_indices = ("doctrine", "scope", "stage")
    retained = ("doctrine", "scope")
    value = digest("veyra.p2s.index-projection-rule.v1", (
        ("projection-id", projection_id.encode()), ("kind", K.GENERABLE.value.encode()),
        *text_rows("input", input_indices), ("hidden", b"stage"),
        *text_rows("retained", retained),
    ))
    result = (IndexProjectionRule(
        projection_id, K.GENERABLE, input_indices, "stage", retained, value,
    ),)
    logger.debug("_index_projections exit")
    return result


def promotion_registry() -> PromotionRegistry:
    """Build the frozen versioned P2-S registry and its exact commitment."""
    logger.debug("promotion_registry entry")
    domains = _domains()
    rules = tuple(_rule(row) for row in _RULE_ROWS)
    premise_projections = _premise_projections(rules)
    index_projections = _index_projections()
    schemas = schema_targets(FORBIDDEN_CONCLUSION_FIELDS)
    value = digest("veyra.p2s.registry.v1", (
        ("version", REGISTRY_VERSION.encode()),
        *text_rows("domain", tuple(item.domain_digest for item in domains)),
        *text_rows("rule", tuple(item.rule_digest for item in rules)),
        *text_rows("premise-projection", tuple(
            item.projection_digest for item in premise_projections)),
        *text_rows("index-projection", tuple(
            item.projection_digest for item in index_projections)),
        *text_rows("schema", tuple(item.schema_digest for item in schemas)),
    ))
    result = PromotionRegistry(
        REGISTRY_VERSION, domains, rules, premise_projections,
        index_projections, schemas, value,
    )
    logger.debug("promotion_registry exit digest=%s", value[:12])
    return result
