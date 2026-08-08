"""Content-addressed graph artifacts for trusted R7 proof judgments."""
from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from typing import NoReturn

from .proof_core_artifact_decode import decode_rule
from .proof_core_codec import (
    canonical_json, context_data, context_from_data, digest_data, load_canonical,
    prop_data, prop_from_data, term_data,
)
from .proof_core_kernel import ProofKernelError, infer_proof
from .proof_core_substitution import shift_prop
from .proof_core_types import (
    Assume, EqRefl, EqSym, EqTrans, ForallElim, ForallIntro, ImpElim, ImpIntro,
    NativeLaw, ProofContext, ProofTerm, ResonanceIntro, RuleId,
)

logger = logging.getLogger(__name__)
SCHEMA = "veyra-proof-core-v1"


@dataclass(frozen=True)
class ProofNodeArtifact:
    """One fully content-addressed rule application in a proof graph."""

    node_id: str
    rule: str
    payload: str
    premise_ids: tuple[str, ...]
    context_digest: str
    inferred_conclusion: str


@dataclass(frozen=True)
class ProofArtifact:
    """A canonically bound closed or contextual proof graph."""

    schema: str
    theorem_id: str
    context: str
    statement: str
    root_id: str
    nodes: tuple[ProofNodeArtifact, ...]
    rule_closure: tuple[str, ...]
    native_law_closure: tuple[str, ...]
    proof_digest: str


@dataclass(frozen=True)
class ArtifactCheck:
    """Non-throwing proof-artifact verification result."""

    ok: bool
    errors: tuple[str, ...]


def _reject(reason: str) -> NoReturn:
    logger.error("proof_core_artifact rejected reason=%s", reason)
    raise ValueError(reason)


def _proof_parts(
    context: ProofContext, proof: ProofTerm,
) -> tuple[RuleId, dict[str, object], tuple[tuple[ProofContext, ProofTerm], ...]]:
    logger.debug("_proof_parts entry proof=%r", proof)
    same = context
    if type(proof) is Assume:
        result = RuleId.ASSUME, {"index": proof.index}, ()
    elif type(proof) is ImpIntro:
        child = ProofContext(context.term_types, (proof.premise,) + context.assumptions)
        result = RuleId.IMP_INTRO, {"premise": prop_data(proof.premise)}, ((child, proof.body),)
    elif type(proof) is ImpElim:
        result = RuleId.IMP_ELIM, {}, ((same, proof.function), (same, proof.argument))
    elif type(proof) is ForallIntro:
        assumptions = tuple(shift_prop(item, 1) for item in context.assumptions)
        child = ProofContext((proof.binder_type,) + context.term_types, assumptions)
        result = RuleId.FORALL_INTRO, {"type": proof.binder_type.value}, ((child, proof.body),)
    elif type(proof) is ForallElim:
        result = RuleId.FORALL_ELIM, {"argument": term_data(proof.argument)}, ((same, proof.universal),)
    elif type(proof) is EqRefl:
        result = RuleId.EQ_REFL, {"term": term_data(proof.term)}, ()
    elif type(proof) is EqSym:
        result = RuleId.EQ_SYM, {}, ((same, proof.evidence),)
    elif type(proof) is EqTrans:
        result = RuleId.EQ_TRANS, {}, ((same, proof.left), (same, proof.right))
    elif type(proof) is NativeLaw:
        result = RuleId.NATIVE_LAW, {"law": proof.law_id.value, "args": [term_data(item) for item in proof.args]}, ()
    elif type(proof) is ResonanceIntro:
        payload = {"factor": term_data(proof.factor), "carrier": term_data(proof.carrier), "witness": term_data(proof.witness)}
        result = RuleId.RESONANCE_INTRO, payload, ((same, proof.equality),)
    else:
        _reject(f"unknown-proof-term:{type(proof).__name__}")
    logger.debug("_proof_parts exit rule=%s children=%d", result[0].value, len(result[2]))
    return result


def _node_id(
    rule: str, payload: str, premises: tuple[str, ...],
    context_digest: str, conclusion: str,
) -> str:
    logger.debug("_node_id entry rule=%s premises=%d", rule, len(premises))
    result = "PN-" + digest_data(
        [rule, payload, list(premises), context_digest, conclusion],
        "veyra-proof-node-v1",
    )
    logger.debug("_node_id exit result=%s", result)
    return result


def _build_node(
    context: ProofContext, proof: ProofTerm, rows: dict[str, ProofNodeArtifact],
    active: set[int],
) -> str:
    logger.debug("_build_node entry proof=%r", proof)
    identity = id(proof)
    if identity in active:
        _reject("circular-proof-term")
    active.add(identity)
    try:
        rule, payload_data, children = _proof_parts(context, proof)
        premises = tuple(_build_node(child_context, child, rows, active) for child_context, child in children)
        conclusion = canonical_json(prop_data(infer_proof(context, proof).conclusion))
        payload = canonical_json(payload_data)
        context_digest = digest_data(context_data(context), "veyra-proof-context-v1")
        node_id = _node_id(rule.value, payload, premises, context_digest, conclusion)
        node = ProofNodeArtifact(node_id, rule.value, payload, premises, context_digest, conclusion)
        if node_id in rows and rows[node_id] != node:
            _reject("proof-node-collision")
        rows[node_id] = node
    finally:
        active.remove(identity)
    logger.debug("_build_node exit node=%s", node_id)
    return node_id


def _artifact_body(artifact: ProofArtifact) -> dict[str, object]:
    logger.debug("_artifact_body entry theorem=%s", artifact.theorem_id)
    nodes = [
        {"id": node.node_id, "rule": node.rule, "payload": node.payload,
         "premises": list(node.premise_ids), "context": node.context_digest,
         "conclusion": node.inferred_conclusion}
        for node in artifact.nodes
    ]
    result = {
        "schema": artifact.schema, "theorem": artifact.theorem_id,
        "context": artifact.context, "statement": artifact.statement,
        "root": artifact.root_id, "nodes": nodes,
        "rules": list(artifact.rule_closure), "laws": list(artifact.native_law_closure),
    }
    logger.debug("_artifact_body exit nodes=%d", len(nodes))
    return result


def make_proof_artifact(
    theorem_id: str, context: ProofContext, proof: ProofTerm,
) -> ProofArtifact:
    """Check a proof and bind its complete connected graph canonically."""
    logger.debug("make_proof_artifact entry theorem=%r", theorem_id)
    if type(theorem_id) is not str or not theorem_id:
        _reject("invalid-theorem-id")
    judgment = infer_proof(context, proof)
    rows: dict[str, ProofNodeArtifact] = {}
    root = _build_node(context, proof, rows, set())
    seed = ProofArtifact(
        SCHEMA, theorem_id, canonical_json(context_data(context)),
        canonical_json(prop_data(judgment.conclusion)), root,
        tuple(sorted(rows.values(), key=lambda item: item.node_id)),
        tuple(item.value for item in judgment.rule_closure),
        tuple(item.value for item in judgment.native_law_closure), "",
    )
    result = ProofArtifact(
        seed.schema, seed.theorem_id, seed.context, seed.statement, seed.root_id,
        seed.nodes, seed.rule_closure, seed.native_law_closure,
        digest_data(_artifact_body(seed), "veyra-proof-artifact-v1"),
    )
    logger.debug("make_proof_artifact exit digest=%s nodes=%d", result.proof_digest, len(result.nodes))
    return result


def artifact_json(artifact: ProofArtifact) -> str:
    """Return the complete canonical artifact serialization."""
    logger.debug("artifact_json entry theorem=%s", artifact.theorem_id)
    result = canonical_json({**_artifact_body(artifact), "digest": artifact.proof_digest})
    logger.debug("artifact_json exit bytes=%d", len(result.encode()))
    return result


def _decode_node(
    node_id: str, table: dict[str, ProofNodeArtifact], active: set[str], reached: set[str],
) -> ProofTerm:
    logger.debug("_decode_node entry node=%s", node_id)
    if node_id in active:
        _reject("circular-proof-graph")
    if node_id not in table:
        _reject("dangling-proof-premise")
    node = table[node_id]
    active.add(node_id)
    reached.add(node_id)
    try:
        payload = load_canonical(node.payload)
        prop_from_data(load_canonical(node.inferred_conclusion))
        children = tuple(_decode_node(item, table, active, reached) for item in node.premise_ids)
        if node.node_id != _node_id(node.rule, node.payload, node.premise_ids, node.context_digest, node.inferred_conclusion):
            _reject("forged-node-id")
        rule = RuleId(node.rule)
        arity = {RuleId.ASSUME: 0, RuleId.IMP_INTRO: 1, RuleId.IMP_ELIM: 2, RuleId.FORALL_INTRO: 1,
                 RuleId.FORALL_ELIM: 1, RuleId.EQ_REFL: 0, RuleId.EQ_SYM: 1, RuleId.EQ_TRANS: 2,
                 RuleId.NATIVE_LAW: 0, RuleId.RESONANCE_INTRO: 1}[rule]
        if len(children) != arity:
            _reject("proof-rule-bad-arity")
        result = decode_rule(rule, payload, children)
    finally:
        active.remove(node_id)
    logger.debug("_decode_node exit node=%s", node_id)
    return result


def verify_proof_artifact(artifact: ProofArtifact) -> ArtifactCheck:
    """Replay a canonical graph and reject any integrity or judgment drift."""
    logger.debug("verify_proof_artifact entry theorem=%r", getattr(artifact, "theorem_id", None))
    errors: list[str] = []
    try:
        _validate_shape(artifact)
        table = {item.node_id: item for item in artifact.nodes}
        if len(table) != len(artifact.nodes):
            _reject("duplicate-proof-node")
        reached: set[str] = set()
        proof = _decode_node(artifact.root_id, table, set(), reached)
        if reached != set(table):
            _reject("disconnected-proof-graph")
        context = context_from_data(load_canonical(artifact.context))
        prop_from_data(load_canonical(artifact.statement))
        if artifact != make_proof_artifact(artifact.theorem_id, context, proof):
            _reject("artifact-replay-mismatch")
        if artifact.proof_digest != digest_data(_artifact_body(artifact), "veyra-proof-artifact-v1"):
            _reject("forged-proof-digest")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, ProofKernelError, RecursionError) as exc:
        logger.error("verify_proof_artifact blocked error=%s", exc)
        errors.append(str(exc))
    result = ArtifactCheck(not errors, tuple(errors))
    logger.debug("verify_proof_artifact exit ok=%s errors=%r", result.ok, result.errors)
    return result


def _validate_shape(artifact: ProofArtifact) -> None:
    logger.debug("_validate_shape entry type=%s", type(artifact).__name__)
    if type(artifact) is not ProofArtifact or artifact.schema != SCHEMA:
        _reject("invalid-artifact-schema")
    if type(artifact.theorem_id) is not str or not artifact.theorem_id:
        _reject("invalid-theorem-id")
    if type(artifact.nodes) is not tuple or any(type(item) is not ProofNodeArtifact for item in artifact.nodes):
        _reject("invalid-proof-nodes")
    if type(artifact.rule_closure) is not tuple or type(artifact.native_law_closure) is not tuple:
        _reject("invalid-proof-closures")
    if any(type(item) is not str for item in (artifact.context, artifact.statement, artifact.root_id, artifact.proof_digest)):
        _reject("invalid-artifact-field")
    for node in artifact.nodes:
        if any(type(item) is not str for item in (node.node_id, node.rule, node.payload, node.context_digest, node.inferred_conclusion)):
            _reject("invalid-node-field")
        if type(node.premise_ids) is not tuple or any(type(item) is not str for item in node.premise_ids):
            _reject("invalid-premise-ids")
    logger.debug("_validate_shape exit valid")
