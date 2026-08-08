"""Executable pre/postcondition witnesses for checked VAM optimizer local laws."""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import logging
from typing import Iterable, Mapping, Protocol, Sequence, cast

from .assembly import parse_vmasm
from .equivalence import summarize_equivalence
from .optimizer import optimize

logger = logging.getLogger(__name__)

BOUNDARY = "optimizer-prepost-witness"
CLAIM = "executable-prepost-witness-not-proof"
OVERCLAIM_TERMS = (
    "whole-pass proof",
    "whole-optimizer correctness",
    "global equivalence",
    "global correctness",
    "full correctness",
    "complete verification",
    "speed claim",
    "native performance",
)


@dataclass(frozen=True)
class OptimizerPrePostWitness:
    """One bounded executable witness for a checked optimizer local law."""

    pass_name: str
    local_law: str
    program_name: str
    precondition_status: str
    postcondition_status: str
    accepted: bool
    equivalence_status: str
    optimized_delta: int
    optimizer_detail: str
    boundary: str = BOUNDARY
    claim: str = CLAIM


@dataclass(frozen=True)
class _WitnessSpec:
    pass_name: str
    local_law: str
    program_name: str
    source: str
    expected_accepted: bool = True


class _DataclassInstance(Protocol):
    __dataclass_fields__: dict[str, object]


_SPECS: tuple[_WitnessSpec, ...] = (
    _WitnessSpec(
        "observer-alias",
        "observer-alias.lookup-invariant",
        "observer-alias-duplicate-kind",
        '''
OBSERVER %r1, "kind"
OBSERVER %r2, "kind"
REZ %r3, "phase"
COMPRESS %r4, %r3, %r1
ECHO %r5, %r4, %r4, %r2
''',
    ),
    _WitnessSpec(
        "compress-alias",
        "compress-alias.same-pair-local-law",
        "compress-alias-same-pair",
        '''
REZ %r1, "phase"
OBSERVER %r2, "kind"
COMPRESS %r3, %r1, %r2
COMPRESS %r4, %r1, %r2
ECHO %r5, %r3, %r4, %r2
''',
    ),
    _WitnessSpec(
        "compress-idempotent",
        "compress-idempotent.same-observer-local-law",
        "compress-idempotent-same-observer",
        '''
REZ %r1, "phase"
OBSERVER %r2, "kind"
COMPRESS %r3, %r1, %r2
COMPRESS %r4, %r3, %r2
ECHO %r5, %r3, %r4, %r2
''',
    ),
    _WitnessSpec(
        "compress-idempotent",
        "compress-idempotent.visible-use-observer-local-law",
        "compress-idempotent-visible-observe-use",
        '''
REZ %r1, "phase"
OBSERVER %r2, "kind"
COMPRESS %r3, %r1, %r2
COMPRESS %r4, %r3, %r2
OBSERVE %r5, %r4, %r2
ECHO %r6, %r5, %r5, %r2
CERT %r7, "visible-use", %r6, "same observer visible"
''',
    ),
    _WitnessSpec(
        "compress-idempotent",
        "compress-idempotent.different-observer-reject-local-law",
        "compress-idempotent-different-observer-reject",
        '''
REZ %r1, "phase"
OBSERVER %r2, "kind"
OBSERVER %r3, "length"
COMPRESS %r4, %r1, %r2
COMPRESS %r5, %r4, %r3
ECHO %r6, %r4, %r5, %r2
''',
        False,
    ),
    _WitnessSpec(
        "compress-idempotent",
        "compress-idempotent.obstruction-boundary-reject-local-law",
        "compress-idempotent-obstruction-boundary-reject",
        '''
REZ %r1, "phase"
OBSERVER %r2, "kind"
COMPRESS %r3, %r1, %r2
COMPRESS %r4, %r3, %r2
OBSTRUCT %r5, %r4, "boundary"
''',
        False,
    ),
    _WitnessSpec(
        "dead-shadow",
        "dead-shadow.unused-lookup-local-law",
        "dead-shadow-unused-compress",
        '''
REZ %r1, "phase"
OBSERVER %r2, "kind"
COMPRESS %r3, %r1, %r2
''',
    ),
)


def optimizer_prepost_witness_rows() -> tuple[OptimizerPrePostWitness, ...]:
    """Return six deterministic executable witnesses in optimizer pass order."""
    logger.debug("optimizer_prepost_witness_rows entry")
    result = tuple(_witness_from_spec(spec) for spec in _SPECS)
    logger.debug("optimizer_prepost_witness_rows exit rows=%d", len(result))
    return result


def optimizer_prepost_witness_payload() -> tuple[dict[str, object], ...]:
    """Return JSON-friendly optimizer pre/post witness rows."""
    logger.debug("optimizer_prepost_witness_payload entry")
    result = tuple(asdict(row) for row in optimizer_prepost_witness_rows())
    logger.debug("optimizer_prepost_witness_payload exit rows=%d", len(result))
    return result


def optimizer_prepost_witness_summary() -> dict[str, object]:
    """Summarize bounded executable witness evidence without overclaiming."""
    logger.debug("optimizer_prepost_witness_summary entry")
    rows = optimizer_prepost_witness_rows()
    summary: dict[str, object] = {
        "total_rows": len(rows),
        "accepted_rows": sum(1 for row in rows if row.accepted),
        "safe_equivalence_rows": sum(1 for row in rows if row.equivalence_status == "equivalent"),
        "local_laws": tuple(row.local_law for row in rows),
        "boundary": BOUNDARY,
        "claim": CLAIM,
    }
    logger.debug(
        "optimizer_prepost_witness_summary exit total=%d accepted=%d safe=%d",
        summary["total_rows"],
        summary["accepted_rows"],
        summary["safe_equivalence_rows"],
    )
    return summary


def assert_no_optimizer_prepost_overclaim_terms(rows_or_payload: object) -> None:
    """Raise if witness rows or payloads contain out-of-bound claim language."""
    rows = _coerce_rows(rows_or_payload)
    logger.debug("assert_no_optimizer_prepost_overclaim_terms entry rows=%d", len(rows))
    for row in rows:
        text = "\n".join(str(value).lower() for value in row.values())
        for term in OVERCLAIM_TERMS:
            if term in text:
                logger.debug("assert_no_optimizer_prepost_overclaim_terms fail term=%s", term)
                raise ValueError(f"overclaim term present: {term}")
    logger.debug("assert_no_optimizer_prepost_overclaim_terms exit ok")


def _witness_from_spec(spec: _WitnessSpec) -> OptimizerPrePostWitness:
    logger.debug("optimizer_prepost_witness_from_spec entry pass=%s", spec.pass_name)
    program = parse_vmasm(spec.source)
    report = optimize(program)
    equivalence = summarize_equivalence(report.original, report.optimized)
    decisions = [
        row for row in report.rows if row.pass_name == spec.pass_name and row.accepted is spec.expected_accepted
    ]
    result = OptimizerPrePostWitness(
        pass_name=spec.pass_name,
        local_law=spec.local_law,
        program_name=spec.program_name,
        precondition_status="witnessed" if decisions else "not-witnessed",
        postcondition_status="preserved" if equivalence.status == "equivalent" else "not-preserved",
        accepted=bool(decisions and decisions[0].accepted),
        equivalence_status=equivalence.status,
        optimized_delta=len(report.original) - len(report.optimized),
        optimizer_detail=decisions[0].detail if decisions else "no matching optimizer row",
    )
    logger.debug(
        "optimizer_prepost_witness_from_spec exit pass=%s accepted=%s equivalence=%s",
        result.pass_name,
        result.accepted,
        result.equivalence_status,
    )
    return result


def _coerce_rows(rows_or_payload: object) -> tuple[Mapping[str, object], ...]:
    logger.debug("optimizer_prepost_coerce_rows entry type=%s", type(rows_or_payload).__name__)
    if isinstance(rows_or_payload, Mapping) or _is_dataclass_instance(rows_or_payload):
        items: Sequence[object] = (rows_or_payload,)
    else:
        items = tuple(cast(Iterable[object], rows_or_payload))
    result = tuple(_row_mapping(item) for item in items)
    logger.debug("optimizer_prepost_coerce_rows exit rows=%d", len(result))
    return result


def _row_mapping(item: object) -> Mapping[str, object]:
    if isinstance(item, Mapping):
        return cast(Mapping[str, object], item)
    if _is_dataclass_instance(item):
        return asdict(cast(_DataclassInstance, item))
    raise TypeError(f"unsupported optimizer prepost row: {type(item).__name__}")


def _is_dataclass_instance(value: object) -> bool:
    return is_dataclass(value) and not isinstance(value, type)
