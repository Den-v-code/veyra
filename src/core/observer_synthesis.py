"""Bounded, typed and holdout-safe observer synthesis."""
from __future__ import annotations

from hashlib import sha256
import json
import logging

from .observer_synthesis_types import (
    CandidateEvaluation, Canonical, FittedObserver, HoldoutReport, NamedBaseline,
    ObserverCase, ObserverCaseEvidence, ObserverGrammar, ObserverPrimitive,
    ObserverResponse, ObserverSynthesisResult, ObserverTerm, SynthesisConfig,
    SynthesisObstruction,
)
from .observer_synthesis_protocol import (
    case_payload_digests, digest_value, evaluation_digest,
)

logger = logging.getLogger(__name__)
def canonical_term(term: ObserverTerm) -> str:
    """Return deterministic JSON for an observer AST."""
    logger.debug("canonical_term entry op=%s", term.op)
    node = {"children": [json.loads(canonical_term(child)) for child in term.children],
            "kind": term.output_kind, "op": term.op, "primitive": term.primitive}
    result = json.dumps(node, sort_keys=True, separators=(",", ":"))
    logger.debug("canonical_term exit bytes=%d", len(result))
    return result


def observer_fingerprint(term: ObserverTerm) -> str:
    """Hash the canonical observer AST."""
    logger.debug("observer_fingerprint entry op=%s", term.op)
    result = sha256(canonical_term(term).encode()).hexdigest()
    logger.debug("observer_fingerprint exit digest=%s", result[:12])
    return result


def observer_term_cost(term: ObserverTerm, registry: dict[str, ObserverPrimitive]) -> int:
    """Return audited grammar cost, rejecting invalid terms."""
    logger.debug("observer_term_cost entry op=%s", term.op)
    if term.op == "input":
        result = 0
    elif term.op == "apply" and len(term.children) == 1 and term.primitive in registry:
        primitive = registry[term.primitive]
        if primitive.cost <= 0 or term.children[0].output_kind != primitive.input_kind or term.output_kind != primitive.output_kind:
            raise ValueError("invalid-composition")
        result = primitive.cost + observer_term_cost(term.children[0], registry)
    elif term.op == "pair" and len(term.children) == 2 and term.output_kind == "pair":
        result = 1 + sum(observer_term_cost(child, registry) for child in term.children)
    else:
        raise ValueError("invalid-composition")
    logger.debug("observer_term_cost exit result=%d", result)
    return result


def enumerate_observer_terms(grammar: ObserverGrammar) -> tuple[ObserverTerm, ...]:
    """Enumerate the finite typed grammar in deterministic cost order."""
    logger.debug("enumerate_observer_terms entry grammar=%s", grammar.grammar_id)
    registry = _registry(grammar)
    seed = ObserverTerm("input", grammar.input_kind)
    known = {canonical_term(seed): seed}
    changed = True
    while changed:
        changed = False
        current = tuple(known.values())
        proposals: list[ObserverTerm] = []
        for child in current:
            proposals.extend(ObserverTerm("apply", p.output_kind, p.name, (child,)) for p in registry.values() if p.input_kind == child.output_kind)
        for left in current:
            for right in current:
                if canonical_term(left) <= canonical_term(right):
                    proposals.append(ObserverTerm("pair", "pair", children=(left, right)))
        for term in proposals:
            try:
                cost = observer_term_cost(term, registry)
            except ValueError:
                continue
            if cost > grammar.max_cost or _term_depth(term) > grammar.max_depth:
                continue
            key = canonical_term(term)
            if key not in known:
                known[key] = term; changed = True
    result = tuple(sorted((term for term in known.values() if term.output_kind in grammar.accepted_output_kinds), key=lambda t: (observer_term_cost(t, registry), _term_depth(t), canonical_term(t))))
    logger.debug("enumerate_observer_terms exit count=%d", len(result))
    return result


def evaluate_observer(term: ObserverTerm, value: object, registry: dict[str, ObserverPrimitive]) -> ObserverResponse:
    """Evaluate one observer without treating failure as separation."""
    logger.debug("evaluate_observer entry fingerprint=%s", observer_fingerprint(term)[:12])
    try:
        raw, trace = _evaluate(term, value, registry)
        canonical = _canonical_value(raw)
        result = ObserverResponse("ready", canonical, trace=trace)
    except Exception as exc:  # Evaluators are extension points; all failures become data.
        logger.error("evaluate_observer blocked error=%s", type(exc).__name__)
        result = ObserverResponse("blocked", obstruction=f"evaluation-error:{type(exc).__name__}")
    logger.debug("evaluate_observer exit status=%s", result.status)
    return result


def score_observer(term: ObserverTerm, cases: tuple[ObserverCase, ...], grammar: ObserverGrammar, config: SynthesisConfig) -> CandidateEvaluation:
    """Score a candidate on one declared split."""
    logger.debug("score_observer entry cases=%d", len(cases))
    registry = _registry(grammar); evidence = tuple(_case_evidence(term, case, registry, config) for case in cases)
    passed = sum(row.passed for row in evidence); total = len(evidence); fit = passed / total if total else 0.0
    obstructed = sum(row.left_status == "blocked" or row.right_status == "blocked" for row in evidence)
    complexity = observer_term_cost(term, registry)
    result = CandidateEvaluation(term, observer_fingerprint(term), passed, total, fit, obstructed / total if total else 0.0, complexity, fit - config.complexity_penalty * complexity / grammar.max_cost, evidence)
    logger.debug("score_observer exit fit=%.3f cost=%d", fit, complexity)
    return result


def fit_observer(grammar: ObserverGrammar, train_cases: tuple[ObserverCase, ...], baselines: tuple[NamedBaseline, ...] = (), config: SynthesisConfig = SynthesisConfig()) -> FittedObserver:
    """Fit on train only; the API deliberately cannot inspect holdout."""
    logger.debug("fit_observer entry grammar=%s cases=%d", grammar.grammar_id, len(train_cases))
    runtime_ids = tuple(id(item.evaluator) for item in grammar.primitives)
    try:
        evaluation = evaluation_digest(grammar, baselines, config)
        payloads = case_payload_digests(train_cases)
        protocol = digest_value((evaluation, _split_digest(train_cases, payloads)))
        duplicate = _duplicate_split(train_cases, payloads)
    except (TypeError, ValueError) as exc:
        detail = str(exc) if "unbound-semantics" in str(exc) else f"unbound-semantics:{type(exc).__name__}"
        result = FittedObserver(grammar.grammar_id, digest_value((grammar.grammar_id, detail)), "", runtime_ids, (), None, (), "blocked", _case_ids(train_cases), _group_ids(train_cases), (SynthesisObstruction("unbound-semantics", detail),))
        logger.error("fit_observer blocked detail=%s", detail); return result
    if duplicate:
        result = FittedObserver(grammar.grammar_id, protocol, evaluation, runtime_ids, payloads, None, (), "blocked", _case_ids(train_cases), _group_ids(train_cases), (SynthesisObstruction("split-leakage", duplicate),))
        logger.error("fit_observer blocked detail=%s", duplicate); return result
    scores = tuple(score_observer(term, train_cases, grammar, config) for term in enumerate_observer_terms(grammar))
    eligible = tuple(row for row in scores if row.fit >= config.min_train_fit)
    ranked = tuple(sorted(eligible, key=lambda row: (-row.objective, -row.fit, row.obstruction_rate, row.complexity, row.fingerprint)))
    winner = ranked[0] if ranked else None
    status = "ready" if winner else "blocked"
    obs = () if winner else (SynthesisObstruction("not-found", "no observer within declared grammar/budget met train threshold"),)
    result = FittedObserver(grammar.grammar_id, protocol, evaluation, runtime_ids, payloads, winner, ranked[1:], status, _case_ids(train_cases), _group_ids(train_cases), obs)
    logger.debug("fit_observer exit status=%s eligible=%d", status, len(ranked)); return result


def validate_observer(fitted: FittedObserver, grammar: ObserverGrammar, holdout_cases: tuple[ObserverCase, ...], baselines: tuple[NamedBaseline, ...] = (), config: SynthesisConfig = SynthesisConfig()) -> HoldoutReport:
    """Validate the fixed train winner without holdout reranking."""
    logger.debug("validate_observer entry holdout=%d", len(holdout_cases))
    runtime_ids = tuple(id(item.evaluator) for item in grammar.primitives)
    try:
        evaluation = evaluation_digest(grammar, baselines, config)
        holdout_payloads = case_payload_digests(holdout_cases)
        holdout_digest = _split_digest(holdout_cases, holdout_payloads)
    except (TypeError, ValueError) as exc:
        detail = str(exc) if "unbound-semantics" in str(exc) else f"unbound-semantics:{type(exc).__name__}"
        result = HoldoutReport(fitted.protocol_digest, digest_value((_case_ids(holdout_cases), detail)), None, (), "blocked", (), (SynthesisObstruction("unbound-semantics", detail),))
        logger.error("validate_observer blocked detail=%s", detail); return result
    if fitted.grammar_id != grammar.grammar_id or fitted.evaluation_digest != evaluation or fitted.runtime_evaluator_ids != runtime_ids:
        detail = "fit/holdout grammar, primitive semantics, baseline, or config changed"
        result = HoldoutReport(fitted.protocol_digest, holdout_digest, None, (), "blocked", (), (SynthesisObstruction("protocol-mismatch", detail),))
        logger.error("validate_observer blocked detail=%s", detail); return result
    payload_overlap = set(fitted.train_payload_digests) & set(holdout_payloads)
    overlap = set(fitted.train_case_ids) & set(_case_ids(holdout_cases)) or set(fitted.train_group_ids) & set(_group_ids(holdout_cases)) or payload_overlap
    duplicate = _duplicate_split(holdout_cases, holdout_payloads)
    if overlap or duplicate or fitted.winner is None:
        detail = duplicate or (f"overlap={sorted(overlap)}" if overlap else "no fitted winner")
        obs = (SynthesisObstruction("split-leakage" if overlap or duplicate else "not-fitted", detail),)
        result = HoldoutReport(fitted.protocol_digest, holdout_digest, None, (), "blocked", (), obs)
        logger.error("validate_observer blocked detail=%s", detail); return result
    winner = score_observer(fitted.winner.term, holdout_cases, grammar, config)
    baseline_rows = tuple(score_observer(item.term, holdout_cases, grammar, config) for item in baselines)
    status = "validated" if winner.fit >= config.min_holdout_fit else "blocked"
    obs = () if status == "validated" else (SynthesisObstruction("holdout-failure", f"fit={winner.fit}"),)
    result = HoldoutReport(fitted.protocol_digest, holdout_digest, winner, baseline_rows, status, winner.evidence, obs)
    logger.debug("validate_observer exit status=%s fit=%.3f", status, winner.fit); return result


def synthesize_observer(grammar: ObserverGrammar, train_cases: tuple[ObserverCase, ...], holdout_cases: tuple[ObserverCase, ...], baselines: tuple[NamedBaseline, ...] = (), config: SynthesisConfig = SynthesisConfig()) -> ObserverSynthesisResult:
    """Fit then validate, preserving the pre-holdout winner."""
    logger.debug("synthesize_observer entry grammar=%s", grammar.grammar_id)
    fitted = fit_observer(grammar, train_cases, baselines, config)
    holdout = validate_observer(fitted, grammar, holdout_cases, baselines, config)
    status = "validated" if fitted.status == "ready" and holdout.status == "validated" else "blocked"
    boundary = "bounded declared grammar and locked train/holdout only; absence is not impossibility"
    result = ObserverSynthesisResult(fitted, holdout, status, boundary)
    logger.debug("synthesize_observer exit status=%s", status); return result


def _registry(grammar: ObserverGrammar) -> dict[str, ObserverPrimitive]:
    logger.debug("_registry entry primitives=%d", len(grammar.primitives))
    result = {item.name: item for item in grammar.primitives}
    if len(result) != len(grammar.primitives) or any(item.cost <= 0 or not item.semantic_id for item in grammar.primitives):
        logger.error("_registry invalid grammar=%s", grammar.grammar_id); raise ValueError("invalid-grammar")
    logger.debug("_registry exit count=%d", len(result)); return result


def _evaluate(term: ObserverTerm, value: object, registry: dict[str, ObserverPrimitive]) -> tuple[object, tuple[str, ...]]:
    logger.debug("_evaluate entry op=%s", term.op)
    if term.op == "input": result = (value, ("input",))
    elif term.op == "apply":
        child, trace = _evaluate(term.children[0], value, registry); primitive = registry[term.primitive]
        if term.children[0].output_kind != primitive.input_kind: raise ValueError("invalid-composition")
        result = (primitive.evaluator(child), trace + (primitive.name,))
    elif term.op == "pair":
        left, lt = _evaluate(term.children[0], value, registry); right, rt = _evaluate(term.children[1], value, registry)
        result = ((left, right), lt + rt + ("pair",))
    else: raise ValueError("invalid-composition")
    logger.debug("_evaluate exit op=%s", term.op); return result


def _case_evidence(term: ObserverTerm, case: ObserverCase, registry: dict[str, ObserverPrimitive], config: SynthesisConfig) -> ObserverCaseEvidence:
    logger.debug("_case_evidence entry id=%s", case.case_id)
    lefts = tuple(evaluate_observer(term, case.left, registry) for _ in range(max(2, config.determinism_checks)))
    rights = tuple(evaluate_observer(term, case.right, registry) for _ in range(max(2, config.determinism_checks)))
    if len(set(lefts)) != 1 or len(set(rights)) != 1:
        result = ObserverCaseEvidence(case.case_id, False, "blocked", "blocked", None, None, "nondeterministic-evaluator")
        logger.error("_case_evidence nondeterministic id=%s", case.case_id); return result
    left, right = lefts[0], rights[0]
    if case.expected == "echo": passed = left.status == right.status == "ready" and left.value == right.value
    elif case.expected == "separate": passed = left.status == right.status == "ready" and left.value != right.value
    elif case.expected == "blocked-left": passed = left.status == "blocked" and (not case.expected_obstruction or case.expected_obstruction in left.obstruction)
    elif case.expected == "blocked-right": passed = right.status == "blocked" and (not case.expected_obstruction or case.expected_obstruction in right.obstruction)
    else: passed = False
    reason = "matched" if passed else ("unexpected-obstruction" if left.status == "blocked" or right.status == "blocked" else "blind-collision")
    result = ObserverCaseEvidence(case.case_id, passed, left.status, right.status, left.value, right.value, reason)
    logger.debug("_case_evidence exit passed=%s", passed); return result


def _canonical_value(value: object) -> Canonical:
    logger.debug("_canonical_value entry type=%s", type(value).__name__)
    if value is None or isinstance(value, (str, int, float, bool)): result: Canonical = value
    elif isinstance(value, tuple): result = tuple(_canonical_value(item) for item in value)
    else: raise TypeError("noncanonical-result")
    logger.debug("_canonical_value exit"); return result


def _term_depth(term: ObserverTerm) -> int:
    logger.debug("_term_depth entry op=%s", term.op)
    result = 0 if not term.children else 1 + max(_term_depth(child) for child in term.children)
    logger.debug("_term_depth exit result=%d", result); return result


def _case_ids(cases: tuple[ObserverCase, ...]) -> tuple[str, ...]:
    logger.debug("_case_ids entry count=%d", len(cases)); result = tuple(item.case_id for item in cases); logger.debug("_case_ids exit"); return result


def _group_ids(cases: tuple[ObserverCase, ...]) -> tuple[str, ...]:
    logger.debug("_group_ids entry count=%d", len(cases)); result = tuple(item.group_id for item in cases); logger.debug("_group_ids exit"); return result


def _split_digest(cases: tuple[ObserverCase, ...], payloads: tuple[str, ...]) -> str:
    logger.debug("_split_digest entry count=%d", len(cases))
    metadata = tuple((item.case_id, item.group_id, item.expected, item.expected_obstruction) for item in cases)
    result = digest_value((metadata, payloads)); logger.debug("_split_digest exit digest=%s", result[:12]); return result


def _duplicate_split(cases: tuple[ObserverCase, ...], payloads: tuple[str, ...] | None = None) -> str:
    logger.debug("_duplicate_split entry count=%d", len(cases))
    ids, groups = _case_ids(cases), _group_ids(cases)
    payloads = case_payload_digests(cases) if payloads is None else payloads
    result = "duplicate-case-id" if len(set(ids)) != len(ids) else ("duplicate-group-id" if len(set(groups)) != len(groups) else ("duplicate-payload" if len(set(payloads)) != len(payloads) else ""))
    logger.debug("_duplicate_split exit result=%s", result); return result
