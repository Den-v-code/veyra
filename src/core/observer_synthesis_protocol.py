"""Immutable protocol identities and payload leakage guards for synthesis."""
from __future__ import annotations

from dataclasses import fields, is_dataclass
from functools import partial
from hashlib import sha256
import logging
import operator
from types import BuiltinFunctionType, CodeType

from .observer_synthesis_types import (
    NamedBaseline, ObserverCase, ObserverGrammar, ObserverTerm, SynthesisConfig,
)

logger = logging.getLogger(__name__)
_REDUCIBLE_CALLABLES = (type(operator.itemgetter(0)), type(operator.attrgetter("x")), type(operator.methodcaller("x")))


def callable_identity(function: object, semantic_id: str = "") -> str:
    """Bind a primitive name to declared identity and executable implementation."""
    logger.debug("callable_identity entry type=%s semantic_id=%s", type(function).__name__, semantic_id)
    if not semantic_id:
        logger.error("callable_identity unbound missing semantic id")
        raise ValueError("unbound-semantics:missing-semantic-id")
    if isinstance(function, partial):
        body = ("partial", callable_identity(function.func, semantic_id), _freeze(function.args), _freeze(function.keywords))
        result = digest_value((semantic_id, body)); logger.debug("callable_identity exit partial=%s", result[:12]); return result
    if isinstance(function, _REDUCIBLE_CALLABLES):
        body = (type(function).__module__, type(function).__qualname__, _freeze(function.__reduce__()[1]))
        result = digest_value((semantic_id, body)); logger.debug("callable_identity exit reducible=%s", result[:12]); return result
    code = getattr(function, "__code__", None)
    if code is None and not isinstance(function, BuiltinFunctionType):
        logger.error("callable_identity unbound callable type=%s", type(function).__name__)
        raise ValueError("unbound-semantics:callable")
    closure = getattr(function, "__closure__", None) or ()
    body = (
        semantic_id,
        getattr(function, "__module__", type(function).__module__),
        getattr(function, "__qualname__", type(function).__qualname__),
        _freeze(code),
        _freeze(getattr(function, "__defaults__", None)),
        _freeze(getattr(function, "__kwdefaults__", None)),
        tuple(_freeze(cell.cell_contents) for cell in closure),
        _freeze(getattr(function, "__dict__", None)),
        _dependency_shape(function),
    )
    result = digest_value(body)
    logger.debug("callable_identity exit digest=%s", result[:12])
    return result


def evaluation_digest(
    grammar: ObserverGrammar,
    baselines: tuple[NamedBaseline, ...],
    config: SynthesisConfig,
) -> str:
    """Hash all semantics allowed to affect fit or holdout evaluation."""
    logger.debug("evaluation_digest entry grammar=%s baselines=%d", grammar.grammar_id, len(baselines))
    primitives = tuple(
        (item.name, item.input_kind, item.output_kind, item.cost,
         callable_identity(item.evaluator, item.semantic_id))
        for item in grammar.primitives
    )
    baseline_rows = tuple(
        (item.name, item.observer_class, _term_shape(item.term), item.boundary)
        for item in baselines
    )
    shape = (
        grammar.grammar_id, grammar.input_kind, grammar.accepted_output_kinds,
        primitives, grammar.max_depth, grammar.max_cost, baseline_rows,
        _freeze(config),
    )
    result = digest_value(shape)
    logger.debug("evaluation_digest exit digest=%s", result[:12])
    return result


def case_payload_digest(case: ObserverCase) -> str:
    """Hash case content independently of case/group IDs and pair order."""
    logger.debug("case_payload_digest entry id=%s", case.case_id)
    if case.payload_key:
        result = digest_value(("trusted-payload-key", case.payload_key))
        logger.debug("case_payload_digest exit keyed=%s", result[:12]); return result
    pair = tuple(sorted((_freeze(case.left), _freeze(case.right)), key=repr))
    result = digest_value(pair)
    logger.debug("case_payload_digest exit digest=%s", result[:12])
    return result


def case_payload_digests(cases: tuple[ObserverCase, ...]) -> tuple[str, ...]:
    """Return stable payload identities for a declared split."""
    logger.debug("case_payload_digests entry count=%d", len(cases))
    result = tuple(case_payload_digest(case) for case in cases)
    logger.debug("case_payload_digests exit count=%d", len(result))
    return result


def digest_value(value: object) -> str:
    """Hash a deterministic frozen representation."""
    logger.debug("digest_value entry type=%s", type(value).__name__)
    result = sha256(repr(_freeze(value)).encode()).hexdigest()
    logger.debug("digest_value exit digest=%s", result[:12])
    return result


def _term_shape(term: ObserverTerm) -> tuple[object, ...]:
    logger.debug("_term_shape entry op=%s", term.op)
    result = (term.op, term.output_kind, term.primitive, tuple(_term_shape(child) for child in term.children))
    logger.debug("_term_shape exit op=%s", term.op)
    return result


def _dependency_shape(function: object) -> tuple[object, ...]:
    logger.debug("_dependency_shape entry type=%s", type(function).__name__)
    code = getattr(function, "__code__", None); namespace = getattr(function, "__globals__", {})
    rows = []
    for name in (() if code is None else code.co_names):
        value = namespace.get(name)
        if callable(value): rows.append((name, _callable_core(value)))
        elif value is None or isinstance(value, (str, int, float, bool, bytes, tuple, frozenset)):
            rows.append((name, _freeze(value)))
    result = tuple(rows)
    logger.debug("_dependency_shape exit count=%d", len(result)); return result


def _callable_core(function: object) -> tuple[object, ...]:
    logger.debug("_callable_core entry type=%s", type(function).__name__)
    code = getattr(function, "__code__", None)
    if code is None and not isinstance(function, BuiltinFunctionType):
        result = (type(function).__module__, type(function).__qualname__)
    else:
        result = (getattr(function, "__module__", ""), getattr(function, "__qualname__", ""),
                  _freeze(code), _freeze(getattr(function, "__defaults__", None)),
                  _freeze(getattr(function, "__kwdefaults__", None)))
    logger.debug("_callable_core exit type=%s", type(function).__name__); return result


def _freeze(value: object) -> object:
    logger.debug("_freeze entry type=%s", type(value).__name__)
    if value is None:
        result: object = ("none",)
    elif isinstance(value, bool):
        result = ("bool", value)
    elif isinstance(value, int):
        result = ("int", value)
    elif isinstance(value, float):
        result = ("float", value.hex())
    elif isinstance(value, complex):
        result = ("complex", value.real.hex(), value.imag.hex())
    elif isinstance(value, str):
        result = ("str", value)
    elif isinstance(value, bytes):
        result = ("bytes", value.hex())
    elif value is Ellipsis:
        result = ("ellipsis",)
    elif isinstance(value, CodeType):
        result = ("code", value.co_code.hex(), tuple(_freeze(item) for item in value.co_consts),
                  value.co_names, value.co_varnames, value.co_argcount,
                  value.co_posonlyargcount, value.co_kwonlyargcount, value.co_flags,
                  value.co_freevars, value.co_cellvars)
    elif isinstance(value, tuple):
        result = ("tuple", tuple(_freeze(item) for item in value))
    elif isinstance(value, list):
        result = ("list", tuple(_freeze(item) for item in value))
    elif isinstance(value, dict):
        rows = tuple((_freeze(key), _freeze(item)) for key, item in value.items())
        result = ("dict", tuple(sorted(rows, key=repr)))
    elif isinstance(value, set):
        result = ("set", tuple(sorted((_freeze(item) for item in value), key=repr)))
    elif isinstance(value, frozenset):
        result = ("frozenset", tuple(sorted((_freeze(item) for item in value), key=repr)))
    elif is_dataclass(value) and not isinstance(value, type):
        result = (type(value).__module__, type(value).__qualname__,
                  tuple((item.name, _freeze(getattr(value, item.name))) for item in fields(value)))
    elif callable(value):
        logger.error("_freeze unbound callable type=%s", type(value).__name__)
        raise ValueError("unbound-semantics:callable-value")
    else:
        logger.error("_freeze unbound value type=%s", type(value).__name__)
        raise ValueError("unbound-semantics:payload")
    logger.debug("_freeze exit type=%s", type(value).__name__)
    return result
