"""Exact request/policy snapshots and preflight for P1-D2."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .productivity_counterpressure_basis import snapshot_basis_source
from .productivity_counterpressure_common import exact_dataclass_shape, exact_identifier, exact_natural, reject
from .productivity_counterpressure_digest import alphabet_digest, policy_digest, request_bytes, request_digest
from .productivity_counterpressure_types import (
    CounterpressureAlphabet, CounterpressurePolicy, CounterpressureRequest,
    CounterpressureRequestKind, CounterpressureResourceBound, DecreasingTreeRequest,
    LedgerRow, LongRunRequest, NonuniformLedgerRequest, ShrinkingStageRequest,
    TargetChooserRequest,
)

logger = logging.getLogger(__name__)
REQUEST_VERSION = "p1-d2-request-v1"
ALPHABET_VERSION = "p1-d2-alphabet-v1"
POLICY_VERSION = "p1-d2-policy-v1"
MAX_LEDGER_ROWS = 128
MAX_ALPHABET_SYMBOLS = 16
MAX_TARGET_SYMBOLS = 256
MAX_REQUEST_BYTES = 65_536
MAX_SYMBOLIC_COST = 100_000
DEFAULT_REQUEST_BYTES = 4096
DEFAULT_SYMBOLIC_COST = 4096


@dataclass(frozen=True)
class PreparedCounterpressureRequest:
    request: CounterpressureRequest
    kind: CounterpressureRequestKind
    canonical_bytes: bytes
    digest: str
    symbolic_cost: int


def counterpressure_alphabet(
    symbols: tuple[str, ...], version: str = ALPHABET_VERSION,
) -> CounterpressureAlphabet:
    logger.debug("counterpressure_alphabet entry")
    if type(version) is not str or version != ALPHABET_VERSION:
        reject("unknown-counterpressure-alphabet-version")
    if type(symbols) is not tuple or not 1 <= len(symbols) <= MAX_ALPHABET_SYMBOLS:
        reject("invalid-counterpressure-alphabet")
    captured = tuple(exact_identifier(value, "alphabet-symbol") for value in symbols)
    if len(frozenset(captured)) != len(captured):
        reject("duplicate-counterpressure-alphabet-symbol")
    captured = tuple(list(captured))
    result = CounterpressureAlphabet(
        ALPHABET_VERSION, captured, alphabet_digest(ALPHABET_VERSION, captured))
    logger.debug("counterpressure_alphabet exit symbols=%d", len(captured))
    return result


def snapshot_alphabet(value: CounterpressureAlphabet) -> CounterpressureAlphabet:
    logger.debug("snapshot_alphabet entry")
    exact_dataclass_shape(value, CounterpressureAlphabet, "counterpressure-alphabet")
    try:
        expected = counterpressure_alphabet(value.symbols, value.version)
        supplied = value.alphabet_digest
    except AttributeError:
        reject("counterpressure-alphabet-missing-fields")
    if type(supplied) is not str or supplied != expected.alphabet_digest:
        reject("counterpressure-alphabet-drift")
    logger.debug("snapshot_alphabet exit")
    return expected


def counterpressure_policy(
    max_request_bytes: int = DEFAULT_REQUEST_BYTES,
    max_symbolic_cost: int = DEFAULT_SYMBOLIC_COST,
    version: str = POLICY_VERSION,
) -> CounterpressurePolicy:
    logger.debug("counterpressure_policy entry")
    if type(version) is not str or version != POLICY_VERSION:
        reject("unknown-counterpressure-policy-version")
    if type(max_request_bytes) is not int or not 1 <= max_request_bytes <= MAX_REQUEST_BYTES:
        reject("invalid-policy-max-request-bytes")
    if type(max_symbolic_cost) is not int or not 1 <= max_symbolic_cost <= MAX_SYMBOLIC_COST:
        reject("invalid-policy-max-symbolic-cost")
    result = CounterpressurePolicy(
        POLICY_VERSION, max_request_bytes, max_symbolic_cost,
        policy_digest(POLICY_VERSION, max_request_bytes, max_symbolic_cost),
    )
    logger.debug("counterpressure_policy exit")
    return result


def snapshot_policy(value: CounterpressurePolicy) -> CounterpressurePolicy:
    logger.debug("snapshot_policy entry")
    exact_dataclass_shape(value, CounterpressurePolicy, "counterpressure-policy")
    try:
        expected = counterpressure_policy(
            value.max_request_bytes, value.max_symbolic_cost, value.version
        )
        supplied = value.policy_digest
    except AttributeError:
        reject("counterpressure-policy-missing-fields")
    if type(supplied) is not str or supplied != expected.policy_digest:
        reject("counterpressure-policy-drift")
    logger.debug("snapshot_policy exit")
    return expected


def ledger_request(
    rows: tuple[LedgerRow, ...], version: str = REQUEST_VERSION,
) -> NonuniformLedgerRequest:
    logger.debug("ledger_request entry")
    result = snapshot_request(NonuniformLedgerRequest(version, rows))
    logger.debug("ledger_request exit")
    return result  # type: ignore[return-value]


def decreasing_tree_request(sample_depth: int, basis: object) -> DecreasingTreeRequest:
    logger.debug("decreasing_tree_request entry")
    result = snapshot_request(
        DecreasingTreeRequest(REQUEST_VERSION, sample_depth, basis)  # type: ignore[arg-type]
    )
    logger.debug("decreasing_tree_request exit")
    return result  # type: ignore[return-value]


def target_chooser_request(
    alphabet: CounterpressureAlphabet, target: tuple[str, ...],
) -> TargetChooserRequest:
    logger.debug("target_chooser_request entry")
    result = snapshot_request(TargetChooserRequest(REQUEST_VERSION, alphabet, target))
    logger.debug("target_chooser_request exit")
    return result  # type: ignore[return-value]


def long_run_request(steps: int) -> LongRunRequest:
    logger.debug("long_run_request entry")
    result = snapshot_request(LongRunRequest(REQUEST_VERSION, steps))
    logger.debug("long_run_request exit")
    return result  # type: ignore[return-value]


def shrinking_stage_request(sample_index: int, basis: object) -> ShrinkingStageRequest:
    logger.debug("shrinking_stage_request entry")
    result = snapshot_request(
        ShrinkingStageRequest(REQUEST_VERSION, sample_index, basis)  # type: ignore[arg-type]
    )
    logger.debug("shrinking_stage_request exit")
    return result  # type: ignore[return-value]


def snapshot_request(value: CounterpressureRequest) -> CounterpressureRequest:
    """Capture a closed request before any semantic or Lean operation."""
    logger.debug("snapshot_request entry type=%s", type(value).__name__)
    if type(value) is NonuniformLedgerRequest:
        exact_dataclass_shape(value, NonuniformLedgerRequest, "ledger-request")
        result: CounterpressureRequest = _snapshot_ledger(value)
    elif type(value) is DecreasingTreeRequest:
        exact_dataclass_shape(value, DecreasingTreeRequest, "descent-request")
        _version(value.version)
        result = DecreasingTreeRequest(
            REQUEST_VERSION, exact_natural(value.sample_depth, "sample-depth"),
            snapshot_basis_source(value.basis),
        )
    elif type(value) is TargetChooserRequest:
        exact_dataclass_shape(value, TargetChooserRequest, "chooser-request")
        _version(value.version)
        alphabet = snapshot_alphabet(value.alphabet)
        if type(value.target) is not tuple or not 1 <= len(value.target) <= MAX_TARGET_SYMBOLS:
            reject("invalid-target")
        allowed = frozenset(alphabet.symbols)
        target = tuple(exact_identifier(symbol, "target-symbol") for symbol in value.target)
        if any(symbol not in allowed for symbol in target):
            reject("foreign-target-symbol")
        result = TargetChooserRequest(REQUEST_VERSION, alphabet, tuple(list(target)))
    elif type(value) is LongRunRequest:
        exact_dataclass_shape(value, LongRunRequest, "long-run-request")
        _version(value.version)
        steps = exact_natural(value.steps, "steps")
        if steps == 0:
            reject("steps-must-be-positive")
        result = LongRunRequest(REQUEST_VERSION, steps)
    elif type(value) is ShrinkingStageRequest:
        exact_dataclass_shape(value, ShrinkingStageRequest, "shrinking-request")
        _version(value.version)
        result = ShrinkingStageRequest(
            REQUEST_VERSION, exact_natural(value.sample_index, "sample-index"),
            snapshot_basis_source(value.basis),
        )
    else:
        reject("request-variant-must-be-exact")
    payload = request_bytes(result)
    if len(payload) > MAX_REQUEST_BYTES:
        reject("request-hard-byte-limit")
    logger.debug("snapshot_request exit bytes=%d", len(payload))
    return result


def _snapshot_ledger(value: NonuniformLedgerRequest) -> NonuniformLedgerRequest:
    logger.debug("_snapshot_ledger entry")
    _version(value.version)
    if type(value.rows) is not tuple or not 2 <= len(value.rows) <= MAX_LEDGER_ROWS:
        reject("invalid-ledger-rows")
    rows: list[LedgerRow] = []
    depths: list[int] = []
    selectors: list[str] = []
    for raw in value.rows:
        exact_dataclass_shape(raw, LedgerRow, "ledger-row")
        row = LedgerRow(
            exact_natural(raw.depth, "ledger-depth"),
            exact_identifier(raw.witness_label, "witness-label"),
            exact_identifier(raw.selector_label, "selector-label"),
        )
        rows.append(row)
        depths.append(row.depth)
        selectors.append(row.selector_label)
    if any(left >= right for left, right in zip(depths, depths[1:], strict=False)):
        reject("ledger-depths-must-be-strictly-increasing")
    if len(frozenset(selectors)) != len(selectors):
        reject("ledger-selectors-must-be-unique")
    result = NonuniformLedgerRequest(REQUEST_VERSION, tuple(rows))
    logger.debug("_snapshot_ledger exit rows=%d", len(rows))
    return result


def _version(value: object) -> None:
    logger.debug("_version entry")
    if type(value) is not str or value != REQUEST_VERSION:
        reject("unknown-counterpressure-request-version")
    logger.debug("_version exit")


def prepare_request(value: CounterpressureRequest) -> PreparedCounterpressureRequest:
    logger.debug("prepare_request entry")
    request = snapshot_request(value)
    payload = request_bytes(request)
    kind = request_kind(request)
    cost = symbolic_cost(request, len(payload))
    result = PreparedCounterpressureRequest(
        request, kind, bytes(payload), request_digest(request), cost)
    logger.debug("prepare_request exit kind=%s cost=%d", kind.value, cost)
    return result


def request_kind(value: CounterpressureRequest) -> CounterpressureRequestKind:
    logger.debug("request_kind entry type=%s", type(value).__name__)
    mapping = {
        NonuniformLedgerRequest: CounterpressureRequestKind.LEDGER,
        DecreasingTreeRequest: CounterpressureRequestKind.DESCENT,
        TargetChooserRequest: CounterpressureRequestKind.CHOOSER,
        LongRunRequest: CounterpressureRequestKind.LONG_RUN,
        ShrinkingStageRequest: CounterpressureRequestKind.SHRINKING,
    }
    try:
        result = mapping[type(value)]
    except KeyError:
        reject("request-variant-must-be-exact")
    logger.debug("request_kind exit kind=%s", result.value)
    return result


def symbolic_cost(request: CounterpressureRequest, request_size: int) -> int:
    logger.debug("symbolic_cost entry type=%s", type(request).__name__)
    if type(request) is NonuniformLedgerRequest:
        result = 64 + request_size + 16 * len(request.rows)
    elif type(request) is DecreasingTreeRequest:
        result = 96 + request_size + request.sample_depth.bit_length()
    elif type(request) is TargetChooserRequest:
        result = 64 + request_size + 8 * len(request.target)
    elif type(request) is LongRunRequest:
        result = 64 + request_size + request.steps.bit_length()
    elif type(request) is ShrinkingStageRequest:
        result = 96 + request_size + request.sample_index.bit_length()
    else:
        reject("request-variant-must-be-exact")
    logger.debug("symbolic_cost exit cost=%d", result)
    return result


def first_failed_bound(
    prepared: PreparedCounterpressureRequest, policy: CounterpressurePolicy,
) -> tuple[CounterpressureResourceBound, int, int] | None:
    logger.debug("first_failed_bound entry")
    if len(prepared.canonical_bytes) > policy.max_request_bytes:
        logger.debug("first_failed_bound exit failed=request-bytes")
        return (
            CounterpressureResourceBound.REQUEST_BYTES,
            len(prepared.canonical_bytes), policy.max_request_bytes,
        )
    if prepared.symbolic_cost > policy.max_symbolic_cost:
        logger.debug("first_failed_bound exit failed=symbolic-cost")
        return (
            CounterpressureResourceBound.SYMBOLIC_COST,
            prepared.symbolic_cost, policy.max_symbolic_cost,
        )
    logger.debug("first_failed_bound exit allowed")
    return None


DEFAULT_POLICY = counterpressure_policy()
