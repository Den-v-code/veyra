"""Canonical, span-independent data encoding for proof-surface syntax."""
from __future__ import annotations

import logging
from typing import NoReturn

from .proof_core_codec import canonical_json, digest_data
from .proof_surface_trace import traced
from .proof_surface_types import ProofSyntax, PropSyntax, SurfaceProgram, TermSyntax


logger = logging.getLogger(__name__)
trace = traced(logger)


@trace
def _reject(code: str) -> NoReturn:
    logger.error("surface codec rejection state code=%s", code)
    raise TypeError(code)


@trace
def term_syntax_data(term: TermSyntax) -> dict[str, object]:
    """Encode one typed surface term without whitespace/source-position noise."""
    if type(term) is not TermSyntax:
        _reject("invalid-term-syntax")
    result = {
        "op": term.op.value,
        "name": term.name,
        "children": [term_syntax_data(item) for item in term.children],
    }
    logger.debug("term_syntax_data state op=%s children=%d", term.op.value, len(term.children))
    return result


@trace
def prop_syntax_data(prop: PropSyntax) -> dict[str, object]:
    """Encode one typed surface proposition including its source binder name."""
    if type(prop) is not PropSyntax:
        _reject("invalid-prop-syntax")
    result = {
        "op": prop.op.value,
        "terms": [term_syntax_data(item) for item in prop.terms],
        "props": [prop_syntax_data(item) for item in prop.props],
        "binder": prop.binder_name,
        "type": prop.binder_type,
    }
    logger.debug("prop_syntax_data state op=%s props=%d", prop.op.value, len(prop.props))
    return result


@trace
def proof_syntax_data(proof: ProofSyntax) -> dict[str, object]:
    """Encode one explicit surface proof node and all rule payloads."""
    if type(proof) is not ProofSyntax:
        _reject("invalid-proof-syntax")
    result = {
        "op": proof.op.value,
        "proofs": [proof_syntax_data(item) for item in proof.proofs],
        "terms": [term_syntax_data(item) for item in proof.terms],
        "props": [prop_syntax_data(item) for item in proof.props],
        "name": proof.name,
        "type": proof.binder_type,
        "law": proof.law_id,
    }
    logger.debug("proof_syntax_data state op=%s premises=%d", proof.op.value, len(proof.proofs))
    return result


@trace
def surface_program_data(program: SurfaceProgram) -> dict[str, object]:
    """Return the canonical typed-AST payload used by proof-carrying artifacts."""
    if type(program) is not SurfaceProgram:
        _reject("invalid-surface-program")
    result = {
        "language": program.language_id,
        "version": program.version,
        "claim": prop_syntax_data(program.claim),
        "proof": proof_syntax_data(program.proof),
    }
    logger.debug("surface_program_data state language=%s version=%d", program.language_id, program.version)
    return result


@trace
def canonical_surface_json(program: SurfaceProgram) -> str:
    """Serialize the parsed typed AST canonically; spans are intentionally absent."""
    result = canonical_json(surface_program_data(program))
    logger.debug("canonical_surface_json state bytes=%d", len(result.encode("utf-8")))
    return result


@trace
def surface_syntax_digest(program: SurfaceProgram) -> str:
    """Hash the parsed AST; whitespace changes do not affect this digest."""
    result = digest_data(surface_program_data(program), "veyra-proof-surface-ast-v1")
    logger.debug("surface_syntax_digest state digest=%s", result)
    return result
