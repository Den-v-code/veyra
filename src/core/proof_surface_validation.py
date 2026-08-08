"""Origin, span, and total-node validation for captured proof-surface ASTs."""
from __future__ import annotations

from hashlib import sha256
import logging
from typing import NoReturn

from .proof_surface_trace import traced
from .proof_surface_types import (
    ABSOLUTE_TYPED_AST_NODES, CAPTURED_SOURCE_DOMAIN, ProofSyntax, PropSyntax,
    SourceSpan, SurfaceLanguageError, SurfaceProgram, TermSyntax,
)


logger = logging.getLogger(__name__)
trace = traced(logger)


@trace
def _fail(code: str, span: SourceSpan | None = None) -> NoReturn:
    logger.error("surface validation rejection state code=%s span=%r", code, span)
    raise SurfaceLanguageError("elaborate", code, span)


@trace
def captured_source_digest(source: bytes) -> str:
    """Bind exact captured bytes under the composite R10 source domain."""
    if type(source) is not bytes:
        _fail("captured-source-must-be-bytes")
    result = sha256(CAPTURED_SOURCE_DOMAIN + source).hexdigest()
    logger.debug("captured_source_digest state bytes=%d digest=%s", len(source), result)
    return result


@trace
def _checked_span(
    span: object, parent: SourceSpan | None, source_size: int,
) -> SourceSpan:
    if (
        type(span) is not SourceSpan
        or type(span.start) is not int or type(span.end) is not int
        or span.start < 0 or span.start >= span.end or span.end > source_size
    ):
        _fail("invalid-source-span")
    if parent is not None and (span.start < parent.start or span.end > parent.end):
        _fail("source-span-not-contained", span)
    return span


@trace
def validate_captured_surface(
    program: SurfaceProgram, source_size: int, max_nodes: int,
) -> int:
    """Validate every typed node/span iteratively and enforce one total budget."""
    if type(source_size) is not int or source_size <= 0:
        _fail("invalid-captured-source-size")
    if (
        type(max_nodes) is not int or max_nodes <= 0
        or max_nodes > ABSOLUTE_TYPED_AST_NODES
    ):
        _fail("invalid-typed-ast-node-limit")
    if type(program) is not SurfaceProgram:
        _fail("invalid-surface-program")
    stack: list[tuple[object, SourceSpan | None]] = [(program, None)]
    count = 0
    while stack:
        node, parent = stack.pop()
        span = _checked_span(getattr(node, "span", None), parent, source_size)
        count += 1
        if count > max_nodes:
            _fail("typed-ast-node-limit", span)
        if type(node) is SurfaceProgram:
            children: tuple[object, ...] = (node.claim, node.proof)
        elif type(node) is TermSyntax:
            if type(node.children) is not tuple:
                _fail("invalid-typed-ast-containers", span)
            children = node.children
        elif type(node) is PropSyntax:
            if type(node.terms) is not tuple or type(node.props) is not tuple:
                _fail("invalid-typed-ast-containers", span)
            children = (*node.terms, *node.props)
        elif type(node) is ProofSyntax:
            if type(node.proofs) is not tuple or type(node.terms) is not tuple or type(node.props) is not tuple:
                _fail("invalid-typed-ast-containers", span)
            children = (*node.proofs, *node.terms, *node.props)
        else:
            _fail("invalid-typed-ast-node", span)
        stack.extend((child, span) for child in reversed(children))
    logger.debug("validate_captured_surface state nodes=%d source-bytes=%d", count, source_size)
    return count
