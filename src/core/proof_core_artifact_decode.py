"""Rule-payload decoder for canonical R7 proof graph nodes."""
from __future__ import annotations

import logging
from typing import NoReturn

from .proof_core_codec import exact_keys, prop_from_data, term_from_data
from .proof_core_types import (
    Assume, CoreType, EqRefl, EqSym, EqTrans, ForallElim, ForallIntro, ImpElim,
    ImpIntro, NativeLaw, NativeLawId, ProofTerm, ResonanceIntro, RuleId,
)

logger = logging.getLogger(__name__)


def _reject(reason: str) -> NoReturn:
    logger.error("proof_core_artifact_decode rejected reason=%s", reason)
    raise ValueError(reason)


def decode_rule(
    rule: RuleId, payload: object, children: tuple[ProofTerm, ...],
) -> ProofTerm:
    """Decode one already-arity-checked proof-rule payload."""
    logger.debug("decode_rule entry rule=%s", rule.value)
    if rule is RuleId.ASSUME:
        row = exact_keys(payload, {"index"})
        result: ProofTerm = Assume(row["index"])
    elif rule is RuleId.IMP_INTRO:
        row = exact_keys(payload, {"premise"})
        result = ImpIntro(prop_from_data(row["premise"]), children[0])
    elif rule is RuleId.IMP_ELIM:
        exact_keys(payload, set())
        result = ImpElim(*children)
    elif rule is RuleId.FORALL_INTRO:
        row = exact_keys(payload, {"type"})
        result = ForallIntro(CoreType(row["type"]), children[0])
    elif rule is RuleId.FORALL_ELIM:
        row = exact_keys(payload, {"argument"})
        result = ForallElim(children[0], term_from_data(row["argument"]))
    elif rule is RuleId.EQ_REFL:
        row = exact_keys(payload, {"term"})
        result = EqRefl(term_from_data(row["term"]))
    elif rule is RuleId.EQ_SYM:
        exact_keys(payload, set())
        result = EqSym(children[0])
    elif rule is RuleId.EQ_TRANS:
        exact_keys(payload, set())
        result = EqTrans(*children)
    elif rule is RuleId.NATIVE_LAW:
        row = exact_keys(payload, {"law", "args"})
        if type(row["args"]) is not list:
            _reject("native-law-args-shape")
        result = NativeLaw(
            NativeLawId(row["law"]),
            tuple(term_from_data(item) for item in row["args"]),
        )
    elif rule is RuleId.RESONANCE_INTRO:
        row = exact_keys(payload, {"factor", "carrier", "witness"})
        result = ResonanceIntro(
            term_from_data(row["factor"]), term_from_data(row["carrier"]),
            term_from_data(row["witness"]), children[0],
        )
    else:
        _reject("unknown-proof-rule")
    logger.debug("decode_rule exit result=%r", result)
    return result
