"""Ordered replay artifacts for conservative R11 observer proofs."""
from __future__ import annotations

from dataclasses import dataclass, replace
import json
import logging
from typing import NoReturn

from .observer_core_kernel import ObserverProofError, crest_observer, infer_observer_proof, tail_observer
from .observer_core_proof_types import (
    CrestPulseEcho, EmbedR7, EqualityReadyEcho, ObserverProof, ObserverRuleId,
    TailSilenceObstruction,
)
from .observer_core_support import conclusion_data, observer_data, outcome_data, paths_data
from .proof_core_artifact import artifact_json as r7_artifact_json, make_proof_artifact
from .proof_core_codec import canonical_json, context_data, digest_data, load_canonical, term_data
from .proof_core_types import ProofContext

logger = logging.getLogger(__name__)
SCHEMA = "veyra.observer-proof.v2"
NODE_DOMAIN = "veyra-observer-proof-node-v2"
ARTIFACT_DOMAIN = "veyra-observer-proof-artifact-v2"
MAX_ARTIFACT_TEXT_BYTES = 2 * 1024 * 1024
@dataclass(frozen=True)
class ObserverProofNode:
    """One ordered, content-addressed observer rule application."""
    node_id: str
    rule: str
    payload: str
    premise_ids: tuple[str, ...]
    context_digest: str
    inferred_conclusion: str
    inferred_outcome: str
    obstruction_paths: str
    r7_artifact_digest: str


@dataclass(frozen=True)
class ObserverProofArtifact:
    """A complete observer proof, R7 origins, and replay-derived metadata."""
    schema: str
    theorem_id: str
    context: str
    statement: str
    outcome: str
    obstruction_paths: str
    root_id: str
    nodes: tuple[ObserverProofNode, ...]
    rule_closure: tuple[str, ...]
    observer_law_closure: tuple[str, ...]
    support: tuple[str, ...]
    r7_artifact_digests: tuple[str, ...]
    proof_digest: str


@dataclass(frozen=True)
class ObserverArtifactCheck:
    """Non-throwing observer-artifact verification result."""
    ok: bool
    errors: tuple[str, ...]


def _reject(reason: str) -> NoReturn:
    logger.error("observer_core_artifact rejected reason=%s", reason)
    raise ValueError(reason)


def _parts(context: ProofContext, proof: ObserverProof) -> tuple[ObserverRuleId, dict[str, object], tuple[ObserverProof, ...], str]:
    logger.debug("_parts entry proof=%s", type(proof).__name__)
    if type(proof) is EmbedR7:
        r7 = make_proof_artifact("R11-EMBEDDED-R7", context, proof.evidence)
        result = (
            ObserverRuleId.EMBED_R7, {"r7_artifact": load_canonical(r7_artifact_json(r7))}, (), r7.proof_digest,
        )
    elif type(proof) is EqualityReadyEcho:
        result = (ObserverRuleId.EQUALITY_READY_ECHO, {"observer": observer_data(proof.observer)}, (proof.equality,), "")
    elif type(proof) is CrestPulseEcho:
        payload = {
            "observer": observer_data(crest_observer()),
            "left_tail": term_data(proof.left_tail), "right_tail": term_data(proof.right_tail),
        }
        result = (ObserverRuleId.CREST_PULSE_ECHO, payload, (), "")
    elif type(proof) is TailSilenceObstruction:
        result = (ObserverRuleId.TAIL_SILENCE_OBSTRUCTION, {"observer": observer_data(tail_observer())}, (), "")
    else:
        _reject(f"unknown-observer-proof:{type(proof).__name__}")
    logger.debug("_parts exit rule=%s children=%d", result[0].value, len(result[2]))
    return result


def _node_id(node: ObserverProofNode) -> str:
    logger.debug("_node_id entry rule=%s", node.rule)
    result = "ON-" + digest_data(
        [
            node.rule, node.payload, list(node.premise_ids), node.context_digest,
            node.inferred_conclusion, node.inferred_outcome,
            node.obstruction_paths, node.r7_artifact_digest,
        ], NODE_DOMAIN,
    )
    logger.debug("_node_id exit result=%s", result)
    return result


def _build(
    context: ProofContext, proof: ObserverProof, rows: list[ObserverProofNode], active: set[int],
) -> str:
    logger.debug("_build entry proof=%s", type(proof).__name__)
    identity = id(proof)
    if identity in active:
        _reject("circular-observer-proof")
    active.add(identity)
    try:
        rule, payload, children, r7_digest = _parts(context, proof)
        premises = tuple(_build(context, child, rows, active) for child in children)
        judgment = infer_observer_proof(context, proof)
        seed = ObserverProofNode(
            "", rule.value, canonical_json(payload), premises,
            digest_data(context_data(context), "veyra-observer-proof-context-v2"),
            canonical_json(conclusion_data(judgment.conclusion)),
            canonical_json(outcome_data(judgment.outcome)),
            canonical_json(paths_data(judgment.obstruction_paths)), r7_digest,
        )
        node = replace(seed, node_id=_node_id(seed))
        if any(item.node_id == node.node_id for item in rows):
            _reject("duplicate-observer-node")
        rows.append(node)
    finally:
        active.remove(identity)
    logger.debug("_build exit node=%s", node.node_id)
    return node.node_id


def _body(artifact: ObserverProofArtifact) -> dict[str, object]:
    logger.debug("_body entry theorem=%s", artifact.theorem_id)
    nodes = [
        {
            "id": item.node_id, "rule": item.rule, "payload": item.payload,
            "premises": list(item.premise_ids), "context": item.context_digest,
            "conclusion": item.inferred_conclusion, "outcome": item.inferred_outcome,
            "obstructions": item.obstruction_paths, "r7_artifact": item.r7_artifact_digest,
        }
        for item in artifact.nodes
    ]
    result = {
        "schema": artifact.schema, "theorem": artifact.theorem_id,
        "context": artifact.context, "statement": artifact.statement,
        "outcome": artifact.outcome, "obstructions": artifact.obstruction_paths,
        "root": artifact.root_id, "nodes": nodes,
        "rules": list(artifact.rule_closure), "laws": list(artifact.observer_law_closure),
        "support": list(artifact.support), "r7_artifacts": list(artifact.r7_artifact_digests),
    }
    logger.debug("_body exit nodes=%d", len(nodes))
    return result


def make_observer_proof_artifact(theorem_id: str, context: ProofContext, proof: ObserverProof) -> ObserverProofArtifact:
    """Replay and bind an ordered connected observer derivation graph."""
    logger.debug("make_observer_proof_artifact entry theorem=%r", theorem_id)
    if type(theorem_id) is not str or not theorem_id or len(theorem_id) > 256 or len(theorem_id.encode()) > 256:
        _reject("invalid-theorem-id")
    judgment = infer_observer_proof(context, proof)
    rows: list[ObserverProofNode] = []
    root = _build(context, proof, rows, set())
    r7_digests = tuple(item.r7_artifact_digest for item in rows if item.r7_artifact_digest)
    seed = ObserverProofArtifact(
        SCHEMA, theorem_id, canonical_json(context_data(context)),
        canonical_json(conclusion_data(judgment.conclusion)),
        canonical_json(outcome_data(judgment.outcome)),
        canonical_json(paths_data(judgment.obstruction_paths)), root, tuple(rows),
        tuple(item.value for item in judgment.rule_closure),
        tuple(item.value for item in judgment.observer_law_closure),
        tuple(item.value for item in judgment.support), r7_digests, "0" * 64,
    )
    _validate_shape(seed)
    result = replace(seed, proof_digest=digest_data(_body(seed), ARTIFACT_DOMAIN))
    logger.debug("make_observer_proof_artifact exit digest=%s nodes=%d", result.proof_digest, len(result.nodes))
    return result


def observer_artifact_json(artifact: ObserverProofArtifact) -> str:
    """Return the full canonical observer-artifact serialization."""
    logger.debug("observer_artifact_json entry type=%s", type(artifact).__name__)
    _validate_shape(artifact)
    result = canonical_json({**_body(artifact), "digest": artifact.proof_digest})
    logger.debug("observer_artifact_json exit bytes=%d", len(result.encode()))
    return result


def _graph_order(artifact: ObserverProofArtifact) -> tuple[str, ...]:
    logger.debug("_graph_order entry nodes=%d", len(artifact.nodes))
    table = {item.node_id: item for item in artifact.nodes}
    if len(table) != len(artifact.nodes):
        _reject("duplicate-observer-node")
    reached: set[str] = set()
    active: set[str] = set()
    order: list[str] = []

    def visit(node_id: str) -> None:
        logger.debug("_graph_order.visit entry node=%s", node_id)
        if node_id in active:
            _reject("circular-observer-graph")
        if node_id not in table:
            _reject("dangling-observer-premise")
        if node_id in reached:
            _reject("duplicate-observer-derivation")
        node = table[node_id]
        active.add(node_id)
        try:
            rule = ObserverRuleId(node.rule)
            arity = 1 if rule is ObserverRuleId.EQUALITY_READY_ECHO else 0
            if len(node.premise_ids) != arity or len(set(node.premise_ids)) != len(node.premise_ids):
                _reject("observer-rule-bad-arity")
            for premise in node.premise_ids:
                visit(premise)
        finally:
            active.remove(node_id)
        reached.add(node_id)
        order.append(node_id)
        logger.debug("_graph_order.visit exit node=%s", node_id)

    visit(artifact.root_id)
    if reached != set(table):
        _reject("disconnected-observer-graph")
    result = tuple(order)
    logger.debug("_graph_order exit count=%d", len(result))
    return result


def _validate_shape(artifact: ObserverProofArtifact) -> None:
    logger.debug("_validate_shape entry type=%s", type(artifact).__name__)
    if type(artifact) is not ObserverProofArtifact:
        _reject("invalid-observer-artifact-schema")
    if type(artifact.schema) is not str or artifact.schema != SCHEMA:
        _reject("invalid-observer-artifact-schema")
    if type(artifact.theorem_id) is not str or not artifact.theorem_id or len(artifact.theorem_id) > 256 or len(artifact.theorem_id.encode()) > 256:
        _reject("invalid-theorem-id")
    if type(artifact.nodes) is not tuple or len(artifact.nodes) > 256 or any(type(item) is not ObserverProofNode for item in artifact.nodes):
        _reject("invalid-observer-nodes")
    closures = (
        artifact.rule_closure, artifact.observer_law_closure, artifact.support, artifact.r7_artifact_digests,
    )
    if any(type(items) is not tuple or len(items) > 256 or any(type(item) is not str for item in items) for items in closures):
        _reject("invalid-observer-closures")
    top_fields = (
        artifact.schema, artifact.theorem_id, artifact.context, artifact.statement, artifact.outcome,
        artifact.obstruction_paths, artifact.root_id, artifact.proof_digest,
    )
    if any(type(item) is not str for item in top_fields):
        _reject("invalid-observer-artifact-field")
    node_fields: list[str] = []
    for node in artifact.nodes:
        fields = (
            node.node_id, node.rule, node.payload, node.context_digest,
            node.inferred_conclusion, node.inferred_outcome,
            node.obstruction_paths, node.r7_artifact_digest,
        )
        if any(type(item) is not str for item in fields):
            _reject("invalid-observer-node-field")
        if type(node.premise_ids) is not tuple or len(node.premise_ids) > 1 or any(type(item) is not str for item in node.premise_ids):
            _reject("invalid-observer-premises")
        node_fields.extend(fields + node.premise_ids)
    all_fields = top_fields + tuple(item for items in closures for item in items) + tuple(node_fields)
    text_bytes = 0
    for item in all_fields:
        if len(item) > MAX_ARTIFACT_TEXT_BYTES:
            _reject("observer-artifact-text-limit")
        text_bytes += len(item.encode("utf-8"))
        if text_bytes > MAX_ARTIFACT_TEXT_BYTES:
            _reject("observer-artifact-text-limit")
    logger.debug("_validate_shape aggregate_text_bytes=%d limit=%d", text_bytes, MAX_ARTIFACT_TEXT_BYTES)
    logger.debug("_validate_shape exit valid")


def verify_observer_proof_artifact(
    artifact: ObserverProofArtifact, context: ProofContext, proof: ObserverProof,
) -> ObserverArtifactCheck:
    """Replay trusted origins and reject all graph, order, or digest drift."""
    logger.debug("verify_observer_proof_artifact entry type=%s", type(artifact).__name__)
    errors: list[str] = []
    try:
        _validate_shape(artifact)
        logger.debug("verify_observer_proof_artifact validated theorem=%r", artifact.theorem_id)
        order = _graph_order(artifact)
        if order != tuple(item.node_id for item in artifact.nodes):
            _reject("reordered-observer-nodes")
        for node in artifact.nodes:
            if node.node_id != _node_id(replace(node, node_id="")):
                _reject("forged-observer-node-id")
        if artifact.proof_digest != digest_data(_body(artifact), ARTIFACT_DOMAIN):
            _reject("forged-observer-proof-digest")
        expected = make_observer_proof_artifact(artifact.theorem_id, context, proof)
        if artifact != expected:
            _reject("observer-artifact-replay-mismatch")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, ObserverProofError, RecursionError) as exc:
        logger.error("verify_observer_proof_artifact blocked error=%s", exc)
        errors.append(str(exc))
    result = ObserverArtifactCheck(not errors, tuple(errors))
    logger.debug("verify_observer_proof_artifact exit ok=%s errors=%r", result.ok, result.errors)
    return result
