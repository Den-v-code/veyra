"""Budgeted ASCII S-expression reader with exact source spans."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import NoReturn

from .proof_surface_trace import traced
from .proof_surface_types import (
    ABSOLUTE_SAFE_DEPTH, SourceLimits, SourceSpan, SurfaceLanguageError,
)


logger = logging.getLogger(__name__)
trace = traced(logger)


@dataclass(frozen=True)
class Token:
    """One parenthesis or atom token."""

    text: str
    span: SourceSpan


@dataclass(frozen=True)
class AtomNode:
    """One atom in the generic reader tree."""

    text: str
    span: SourceSpan


@dataclass(frozen=True)
class ListNode:
    """One list in the generic reader tree."""

    items: tuple["SExprNode", ...]
    span: SourceSpan


SExprNode = AtomNode | ListNode


@trace
def _fail(code: str, span: SourceSpan | None = None) -> NoReturn:
    logger.error("sexpr rejection state code=%s span=%r", code, span)
    raise SurfaceLanguageError("parse", code, span)


@trace
def scan_tokens(source: str, limits: SourceLimits) -> tuple[Token, ...]:
    """Tokenize the deliberately tiny, comment-free ASCII grammar."""
    if type(source) is not str:
        _fail("source-must-be-str")
    if type(limits) is not SourceLimits or any(
        type(value) is not int or value <= 0
        for value in (
            limits.max_bytes, limits.max_tokens, limits.max_nodes,
            limits.max_depth, limits.max_identifier_bytes,
        )
    ) or limits.max_depth > ABSOLUTE_SAFE_DEPTH:
        _fail("invalid-source-limits")
    try:
        encoded = source.encode("ascii")
    except UnicodeEncodeError as exc:
        _fail("source-must-be-ascii", SourceSpan(exc.start, exc.end))
    if len(encoded) > limits.max_bytes:
        _fail("source-byte-limit")
    if "\x00" in source:
        _fail("nul-byte-forbidden", SourceSpan(source.index("\x00"), source.index("\x00") + 1))
    tokens: list[Token] = []
    cursor = 0
    while cursor < len(source):
        if source[cursor].isspace():
            cursor += 1
            continue
        start = cursor
        if source[cursor] in "()":
            cursor += 1
        else:
            while cursor < len(source) and not source[cursor].isspace() and source[cursor] not in "()":
                cursor += 1
            if cursor - start > limits.max_identifier_bytes:
                _fail("atom-byte-limit", SourceSpan(start, cursor))
        tokens.append(Token(source[start:cursor], SourceSpan(start, cursor)))
        if len(tokens) > limits.max_tokens:
            _fail("token-limit", tokens[-1].span)
    logger.debug("scan_tokens state bytes=%d tokens=%d", len(encoded), len(tokens))
    return tuple(tokens)


@trace
def read_sexpr(source: str, limits: SourceLimits) -> SExprNode:
    """Read exactly one S-expression under node/depth budgets."""
    tokens = scan_tokens(source, limits)
    if not tokens:
        _fail("empty-source", SourceSpan(0, 0))
    node, cursor, count = _read_node(tokens, 0, 0, 0, limits)
    if cursor != len(tokens):
        _fail("trailing-form", tokens[cursor].span)
    logger.debug("read_sexpr state nodes=%d depth-limit=%d", count, limits.max_depth)
    return node


@trace
def _read_node(
    tokens: tuple[Token, ...], cursor: int, depth: int, count: int, limits: SourceLimits,
) -> tuple[SExprNode, int, int]:
    if cursor >= len(tokens):
        _fail("unexpected-end")
    token = tokens[cursor]
    if token.text == ")":
        _fail("unexpected-close", token.span)
    if token.text != "(":
        total = count + 1
        if total > limits.max_nodes:
            _fail("node-limit", token.span)
        return AtomNode(token.text, token.span), cursor + 1, total
    if depth >= limits.max_depth:
        _fail("nesting-limit", token.span)
    items: list[SExprNode] = []
    index, total = cursor + 1, count + 1
    if total > limits.max_nodes:
        _fail("node-limit", token.span)
    while index < len(tokens) and tokens[index].text != ")":
        item, index, total = _read_node(tokens, index, depth + 1, total, limits)
        items.append(item)
    if index >= len(tokens):
        _fail("unclosed-list", token.span)
    close = tokens[index]
    result = ListNode(tuple(items), SourceSpan(token.span.start, close.span.end))
    logger.debug("_read_node state list-items=%d depth=%d", len(items), depth)
    return result, index + 1, total
