"""Private inert work records for the iterative KPT1 wire preflight."""

from __future__ import annotations

from typing import NamedTuple

from .omegaa_kpt1_types import KernelTermTagV1


class TermTask(NamedTuple):
    start: int
    end: int
    depth: int


class FieldsTask(NamedTuple):
    tag: KernelTermTagV1
    position: int
    offset: int
    end: int
    depth: int


class LevelTask(NamedTuple):
    start: int
    end: int
    depth: int


class LevelFieldsTask(NamedTuple):
    item_count: int
    position: int
    offset: int
    end: int
    depth: int


class ListTask(NamedTuple):
    start: int
    end: int
    depth: int


class ListItemsTask(NamedTuple):
    item_count: int
    position: int
    offset: int
    end: int
    depth: int


class NatTask(NamedTuple):
    start: int
    end: int


class DigestTask(NamedTuple):
    start: int
    end: int


WireTask = TermTask | FieldsTask | LevelTask | LevelFieldsTask | ListTask | ListItemsTask | NatTask | DigestTask
