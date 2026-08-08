"""Exact six-byte KCC1 empty-configuration syntax; no checker semantics."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import final

logger = logging.getLogger(__name__)


@final
@dataclass(frozen=True, slots=True)
class EmptyCheckerConfigV1:
    """The sole inert KCC1 value, with no fields or extension authority."""


EMPTY_CHECKER_CONFIG_V1 = EmptyCheckerConfigV1()
