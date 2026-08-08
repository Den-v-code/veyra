"""Counted, length-prefixed, domain-separated P1-D2 commitments."""

from __future__ import annotations

from hashlib import sha256
import logging

from .productivity_counterpressure_types import (
    CounterpressureAlphabet, CounterpressureBasisSource, CounterpressureCertificate,
    CounterpressureEvidence, CounterpressureRequest,
    CounterpressureResourceLimit, DecreasingTreeRequest, DescentCountermodelEvidence,
    FiniteRunInsufficiencyEvidence, LedgerInsufficiencyEvidence, LedgerRow,
    LongRunRequest, NonuniformLedgerRequest, ShrinkingStageRequest,
    ShrinkingTailCountermodelEvidence, TargetChooserRequest, TargetDependenceEvidence,
)

logger = logging.getLogger(__name__)


def _frame(domain: str, fields: tuple[tuple[str, bytes], ...]) -> bytes:
    logger.debug("_frame entry domain=%s fields=%d", domain, len(fields))
    output = bytearray(b"VEYRA-P1-D2\x00")
    _token(output, b"domain", domain.encode())
    _token(output, b"field-count", len(fields).to_bytes(8, "big"))
    for tag, value in fields:
        _token(output, tag.encode(), value)
    result = bytes(output)
    logger.debug("_frame exit domain=%s bytes=%d", domain, len(result))
    return result


def _token(output: bytearray, tag: bytes, value: bytes) -> None:
    logger.debug("_token entry tag=%d value=%d", len(tag), len(value))
    output.extend(len(tag).to_bytes(4, "big"))
    output.extend(tag)
    output.extend(len(value).to_bytes(8, "big"))
    output.extend(value)
    logger.debug("_token exit")


def _digest(domain: str, fields: tuple[tuple[str, bytes], ...]) -> str:
    logger.debug("_digest entry domain=%s", domain)
    result = sha256(_frame(domain, fields)).hexdigest()
    logger.debug("_digest exit domain=%s", domain)
    return result


def _nat(value: int) -> bytes:
    logger.debug("_nat entry bits=%d", value.bit_length())
    width = max(1, (value.bit_length() + 7) // 8)
    result = value.to_bytes(width, "big")
    logger.debug("_nat exit bytes=%d", len(result))
    return result


def _optional_nat(value: int | None) -> bytes:
    logger.debug("_optional_nat entry present=%s", value is not None)
    result = b"none" if value is None else b"some\x00" + _nat(value)
    logger.debug("_optional_nat exit bytes=%d", len(result))
    return result


def alphabet_digest(version: str, symbols: tuple[str, ...]) -> str:
    logger.debug("alphabet_digest entry symbols=%d", len(symbols))
    fields = [("version", version.encode()), ("count", _nat(len(symbols)))]
    fields.extend((f"symbol-{i}", symbol.encode()) for i, symbol in enumerate(symbols))
    result = _digest("veyra.p1d2.alphabet.v1", tuple(fields))
    logger.debug("alphabet_digest exit")
    return result


def basis_digest(
    version: str, basis_id: str, derivation_kind: str, foundation_id: str,
    artifact_name: str, artifact_sha256: str, theorem_ids: tuple[str, ...],
    toolchain_id: str, tcb_digest: str,
) -> str:
    logger.debug("basis_digest entry theorems=%d", len(theorem_ids))
    fields = [
        ("version", version.encode()), ("basis-id", basis_id.encode()),
        ("derivation-kind", derivation_kind.encode()),
        ("foundation-id", foundation_id.encode()),
        ("artifact-name", artifact_name.encode()),
        ("artifact-sha256", artifact_sha256.encode()),
        ("theorem-count", _nat(len(theorem_ids))),
    ]
    fields.extend((f"theorem-{i}", theorem.encode()) for i, theorem in enumerate(theorem_ids))
    fields.extend((("toolchain-id", toolchain_id.encode()), ("tcb-digest", tcb_digest.encode())))
    result = _digest("veyra.p1d2.basis.v1", tuple(fields))
    logger.debug("basis_digest exit")
    return result


def policy_digest(version: str, max_request_bytes: int, max_symbolic_cost: int) -> str:
    logger.debug("policy_digest entry")
    result = _digest("veyra.p1d2.policy.v1", (
        ("version", version.encode()), ("max-request-bytes", _nat(max_request_bytes)),
        ("max-symbolic-cost", _nat(max_symbolic_cost)),
    ))
    logger.debug("policy_digest exit")
    return result


def row_bytes(row: LedgerRow) -> bytes:
    logger.debug("row_bytes entry depth=%d", row.depth)
    result = _frame("veyra.p1d2.ledger-row.v1", (
        ("depth", _nat(row.depth)), ("witness", row.witness_label.encode()),
        ("selector", row.selector_label.encode()),
    ))
    logger.debug("row_bytes exit bytes=%d", len(result))
    return result


def _basis_bytes(source: CounterpressureBasisSource) -> bytes:
    logger.debug("_basis_bytes entry")
    fields = (
        ("version", source.version.encode()), ("basis-id", source.basis_id.encode()),
        ("derivation-kind", source.derivation_kind.value.encode()),
        ("foundation-id", source.foundation_id.encode()),
        ("artifact-name", source.artifact_name.encode()),
        ("artifact-sha256", source.artifact_sha256.encode()),
        ("theorem-count", _nat(len(source.theorem_ids))),
        *((f"theorem-{i}", value.encode()) for i, value in enumerate(source.theorem_ids)),
        ("toolchain", source.toolchain_id.encode()), ("tcb", source.tcb_digest.encode()),
        ("basis-digest", source.basis_digest.encode()),
    )
    result = _frame("veyra.p1d2.basis-source.v1", fields)
    logger.debug("_basis_bytes exit bytes=%d", len(result))
    return result


def _alphabet_bytes(value: CounterpressureAlphabet) -> bytes:
    logger.debug("_alphabet_bytes entry symbols=%d", len(value.symbols))
    fields = [("version", value.version.encode()), ("count", _nat(len(value.symbols)))]
    fields.extend((f"symbol-{i}", symbol.encode()) for i, symbol in enumerate(value.symbols))
    fields.append(("digest", value.alphabet_digest.encode()))
    result = _frame("veyra.p1d2.alphabet-source.v1", tuple(fields))
    logger.debug("_alphabet_bytes exit bytes=%d", len(result))
    return result


def request_bytes(request: CounterpressureRequest) -> bytes:
    logger.debug("request_bytes entry type=%s", type(request).__name__)
    if type(request) is NonuniformLedgerRequest:
        fields = [("version", request.version.encode()), ("count", _nat(len(request.rows)))]
        fields.extend((f"row-{i}", row_bytes(row)) for i, row in enumerate(request.rows))
        result = _frame("veyra.p1d2.request.ledger.v1", tuple(fields))
    elif type(request) is DecreasingTreeRequest:
        result = _frame("veyra.p1d2.request.descent.v1", (
            ("version", request.version.encode()), ("sample-depth", _nat(request.sample_depth)),
            ("basis", _basis_bytes(request.basis)),
        ))
    elif type(request) is TargetChooserRequest:
        fields = [
            ("version", request.version.encode()), ("alphabet", _alphabet_bytes(request.alphabet)),
            ("target-count", _nat(len(request.target))),
        ]
        fields.extend((f"target-{i}", symbol.encode()) for i, symbol in enumerate(request.target))
        result = _frame("veyra.p1d2.request.chooser.v1", tuple(fields))
    elif type(request) is LongRunRequest:
        result = _frame("veyra.p1d2.request.long-run.v1", (
            ("version", request.version.encode()), ("steps", _nat(request.steps)),
        ))
    elif type(request) is ShrinkingStageRequest:
        result = _frame("veyra.p1d2.request.shrinking.v1", (
            ("version", request.version.encode()), ("sample-index", _nat(request.sample_index)),
            ("basis", _basis_bytes(request.basis)),
        ))
    else:
        raise TypeError("unknown-counterpressure-request")
    logger.debug("request_bytes exit bytes=%d", len(result))
    return result


def request_digest(request: CounterpressureRequest) -> str:
    logger.debug("request_digest entry")
    result = sha256(request_bytes(request)).hexdigest()
    logger.debug("request_digest exit")
    return result


def symbolic_formula_digest(formula_id: str, value: int) -> str:
    logger.debug("symbolic_formula_digest entry formula=%s", formula_id)
    result = _digest("veyra.p1d2.symbolic-formula.v1", (
        ("formula-id", formula_id.encode()), ("value", _nat(value)),
    ))
    logger.debug("symbolic_formula_digest exit")
    return result


def symbol_tuple_digest(domain: str, values: tuple[str, ...]) -> str:
    logger.debug("symbol_tuple_digest entry domain=%s count=%d", domain, len(values))
    fields = [("count", _nat(len(values)))]
    fields.extend((f"value-{i}", value.encode()) for i, value in enumerate(values))
    result = _digest(f"veyra.p1d2.{domain}.v1", tuple(fields))
    logger.debug("symbol_tuple_digest exit domain=%s", domain)
    return result


def evidence_digest(evidence: CounterpressureEvidence) -> str:
    logger.debug("evidence_digest entry type=%s", type(evidence).__name__)
    if type(evidence) is LedgerInsufficiencyEvidence:
        fields = [
            ("row-count", _nat(evidence.row_count)),
            ("depth-count", _nat(len(evidence.depths))),
            *((f"depth-{i}", _nat(v)) for i, v in enumerate(evidence.depths)),
            ("selector-count", _nat(evidence.selector_count)),
            ("common-source", b"true" if evidence.common_source_supplied else b"false"),
            ("status", evidence.status.value.encode()),
        ]
        domain = "ledger"
    elif type(evidence) is DescentCountermodelEvidence:
        fields = [
            ("sample", _nat(evidence.sample_depth)), ("length", _nat(evidence.witness_length)),
            ("first", _optional_nat(evidence.first_or_none)),
            ("last", _optional_nat(evidence.last_or_none)),
            ("formula", evidence.witness_formula_digest.encode()),
            ("basis", evidence.basis_digest.encode()), ("status", evidence.status.value.encode()),
        ]
        domain = "descent"
    elif type(evidence) is TargetDependenceEvidence:
        fields = [
            ("length", _nat(evidence.target_length)), ("target", evidence.target_digest.encode()),
            ("output", evidence.output_digest.encode()),
            ("exact-match", b"true" if evidence.exact_match else b"false"),
            ("target-read", b"true" if evidence.target_read else b"false"),
            ("independence", evidence.chooser_target_independence.value.encode()),
            ("rule", evidence.chooser_rule_id.encode()), ("status", evidence.status.value.encode()),
        ]
        domain = "chooser"
    elif type(evidence) is FiniteRunInsufficiencyEvidence:
        fields = [
            ("first", _nat(evidence.first_depth)), ("last", _nat(evidence.last_depth)),
            ("count", _nat(evidence.executed_count)),
            ("materialized", b"true" if evidence.materialized else b"false"),
            ("status", evidence.status.value.encode()),
        ]
        domain = "long-run"
    elif type(evidence) is ShrinkingTailCountermodelEvidence:
        fields = [
            ("sample", _nat(evidence.sample_index)), ("witness", _nat(evidence.local_witness)),
            ("nested-from", _nat(evidence.nested_from)),
            ("nested-into", _nat(evidence.nested_into)),
            ("candidate", _nat(evidence.diagonal_candidate)),
            ("excluding", _nat(evidence.excluding_stage)),
            ("basis", evidence.basis_digest.encode()), ("status", evidence.status.value.encode()),
        ]
        domain = "shrinking"
    else:
        raise TypeError("unknown-counterpressure-evidence")
    result = _digest(f"veyra.p1d2.evidence.{domain}.v1", tuple(fields))
    logger.debug("evidence_digest exit domain=%s", domain)
    return result


def certificate_digest(value: CounterpressureCertificate) -> str:
    logger.debug("certificate_digest entry")
    result = _digest("veyra.p1d2.certificate.v1", (
        ("request-kind", value.request_kind.value.encode()),
        ("request", value.request_digest.encode()), ("inference", value.inference_id.value.encode()),
        ("outcome", value.outcome_kind.value.encode()), ("status", value.status.value.encode()),
        ("evidence", value.evidence_digest.encode()), ("basis-use", value.basis_use.value.encode()),
        ("basis", b"none" if value.basis_digest is None else value.basis_digest.encode()),
        ("policy", value.policy_digest.encode()),
        ("generator-nonexistence", value.generator_nonexistence.value.encode()),
        ("all-depth-family", value.all_depth_family.value.encode()),
        ("completed-carrier", value.completed_carrier.value.encode()),
        ("target-independence", value.historical_target_independence.value.encode()),
        ("scope", value.scope.encode()),
    ))
    logger.debug("certificate_digest exit")
    return result


def refusal_digest(value: CounterpressureResourceLimit) -> str:
    logger.debug("refusal_digest entry")
    result = _digest("veyra.p1d2.refusal.v1", (
        ("request-kind", value.request_kind.value.encode()),
        ("request", value.request_digest.encode()), ("failed", value.failed_bound.value.encode()),
        ("required", _nat(value.required_value)), ("allowed", _nat(value.allowed_value)),
        ("policy", value.policy_digest.encode()),
        ("generator-nonexistence", value.generator_nonexistence.value.encode()),
        ("all-depth-family", value.all_depth_family.value.encode()),
        ("completed-carrier", value.completed_carrier.value.encode()),
        ("target-independence", value.historical_target_independence.value.encode()),
        ("scope", value.scope.encode()),
    ))
    logger.debug("refusal_digest exit")
    return result
