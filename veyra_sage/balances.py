"""Sage-native/fallback Veyra balance parent and element."""

from __future__ import annotations

import logging

from src.core.balance import (
    BalanceMode,
    balance_echo_key,
    balance_from_int,
    canonical_length_balance,
    opposite_balance,
    stitch_balance,
    subtract_balance,
)
from src.core.modes import Mode

from .modes import Element, Parent, SAGE_AVAILABLE

logger = logging.getLogger(__name__)


class VeyraBalanceParent(Parent):
    """Parent/factory for Veyra balance elements over one tact."""

    def __init__(self, tact: str = "τ"):
        """Create balance parent."""
        logger.debug("VeyraBalanceParent.__init__ entry tact=%r", tact)
        if not tact:
            logger.error("VeyraBalanceParent empty tact")
            raise ValueError("tact must be non-empty")
        self.tact = tact
        if SAGE_AVAILABLE:
            Parent.__init__(self)
        logger.debug("VeyraBalanceParent.__init__ exit tact=%r", self.tact)

    def _element_constructor_(self, value: object) -> "VeyraBalanceElement":
        """Construct balance element from core balance, int, or mode pair."""
        logger.debug("VeyraBalanceParent._element_constructor_ entry value=%r", value)
        balance = self._coerce_balance(value)
        result = VeyraBalanceElement(self, balance)
        logger.debug("VeyraBalanceParent._element_constructor_ exit result=%s", result.word)
        return result

    def _coerce_balance(self, value: object) -> BalanceMode:
        """Coerce a Python/core value into BalanceMode."""
        logger.debug("VeyraBalanceParent._coerce_balance entry value=%r", value)
        if isinstance(value, VeyraBalanceElement):
            result = value.balance
        elif isinstance(value, BalanceMode):
            result = value
        elif isinstance(value, int):
            result = balance_from_int(value, self.tact)
        elif isinstance(value, tuple) and len(value) == 2:
            result = BalanceMode(Mode.from_word(str(value[0])), Mode.from_word(str(value[1])))
        else:
            logger.error("VeyraBalanceParent cannot coerce value=%r", value)
            raise TypeError(f"cannot build Veyra balance from {type(value)!r}")
        logger.debug("VeyraBalanceParent._coerce_balance exit result=%s", result.word)
        return result

    def __call__(self, value: object) -> "VeyraBalanceElement":
        """Fallback/Sage-compatible element construction."""
        logger.debug("VeyraBalanceParent.__call__ entry value=%r", value)
        if SAGE_AVAILABLE:
            result = Parent.__call__(self, value)
        else:
            result = self._element_constructor_(value)
        logger.debug("VeyraBalanceParent.__call__ exit result=%s", result.word)
        return result

    def _repr_(self) -> str:
        """Sage repr."""
        return f"Veyra balances over tact {self.tact!r}"

    def __repr__(self) -> str:
        """Python repr."""
        return self._repr_()

    def zero(self) -> "VeyraBalanceElement":
        """Return zero balance."""
        logger.debug("VeyraBalanceParent.zero entry")
        result = self(0)
        logger.debug("VeyraBalanceParent.zero exit result=%s", result.word)
        return result

    def one(self) -> "VeyraBalanceElement":
        """Return unit balance."""
        logger.debug("VeyraBalanceParent.one entry")
        result = self(1)
        logger.debug("VeyraBalanceParent.one exit result=%s", result.word)
        return result


class VeyraBalanceElement(Element):
    """Veyra balance element with Sage-style signed arithmetic."""

    def __init__(self, parent: VeyraBalanceParent, balance: BalanceMode):
        """Create balance element."""
        logger.debug("VeyraBalanceElement.__init__ entry balance=%s", balance.word)
        self._parent = parent
        self.balance = balance
        if SAGE_AVAILABLE:
            Element.__init__(self, parent)
        logger.debug("VeyraBalanceElement.__init__ exit")

    @property
    def word(self) -> str:
        """Return compact balance word."""
        logger.debug("VeyraBalanceElement.word entry")
        result = self.balance.word
        logger.debug("VeyraBalanceElement.word exit result=%s", result)
        return result

    def parent(self) -> VeyraBalanceParent:
        """Return parent in fallback mode."""
        logger.debug("VeyraBalanceElement.parent entry")
        result = self._parent
        logger.debug("VeyraBalanceElement.parent exit result=%r", result)
        return result

    def _repr_(self) -> str:
        """Sage repr."""
        return self.word

    def __repr__(self) -> str:
        """Python repr."""
        return self.word

    def __eq__(self, other: object) -> bool:
        """Compare by signed length shadow."""
        logger.debug("VeyraBalanceElement.__eq__ entry other=%r", other)
        result = isinstance(other, VeyraBalanceElement) and self.net_length() == other.net_length()
        logger.debug("VeyraBalanceElement.__eq__ exit result=%s", result)
        return result

    def _coerce_other(self, other: object) -> "VeyraBalanceElement":
        """Coerce other value through this parent."""
        logger.debug("VeyraBalanceElement._coerce_other entry other=%r", other)
        result = other if isinstance(other, VeyraBalanceElement) else self.parent()(other)
        logger.debug("VeyraBalanceElement._coerce_other exit result=%s", result.word)
        return result

    def net_length(self) -> int:
        """Return signed length shadow."""
        logger.debug("VeyraBalanceElement.net_length entry balance=%s", self.word)
        result = self.balance.net_length
        logger.debug("VeyraBalanceElement.net_length exit result=%d", result)
        return result

    def echo_key(self, test_name: str = "length") -> object:
        """Return balance echo key."""
        logger.debug("VeyraBalanceElement.echo_key entry test=%s", test_name)
        result = balance_echo_key(self.balance, test_name)
        logger.debug("VeyraBalanceElement.echo_key exit result=%r", result)
        return result

    def canonical(self) -> "VeyraBalanceElement":
        """Return canonical signed length form."""
        logger.debug("VeyraBalanceElement.canonical entry balance=%s", self.word)
        result = self.parent()(canonical_length_balance(self.balance, self.parent().tact))
        logger.debug("VeyraBalanceElement.canonical exit result=%s", result.word)
        return result

    def opposite(self) -> "VeyraBalanceElement":
        """Return opposite balance."""
        logger.debug("VeyraBalanceElement.opposite entry balance=%s", self.word)
        result = self.parent()(opposite_balance(self.balance))
        logger.debug("VeyraBalanceElement.opposite exit result=%s", result.word)
        return result

    def _add_(self, other: object) -> "VeyraBalanceElement":
        """Sage addition hook."""
        logger.debug("VeyraBalanceElement._add_ entry left=%s other=%r", self.word, other)
        rhs = self._coerce_other(other)
        result = self.parent()(stitch_balance(self.balance, rhs.balance)).canonical()
        logger.debug("VeyraBalanceElement._add_ exit result=%s", result.word)
        return result

    def __add__(self, other: object) -> "VeyraBalanceElement":
        """Python addition hook."""
        logger.debug("VeyraBalanceElement.__add__ entry left=%s other=%r", self.word, other)
        result = self._add_(other)
        logger.debug("VeyraBalanceElement.__add__ exit result=%s", result.word)
        return result

    def __sub__(self, other: object) -> "VeyraBalanceElement":
        """Python subtraction hook."""
        logger.debug("VeyraBalanceElement.__sub__ entry left=%s other=%r", self.word, other)
        rhs = self._coerce_other(other)
        result = self.parent()(subtract_balance(self.balance, rhs.balance)).canonical()
        logger.debug("VeyraBalanceElement.__sub__ exit result=%s", result.word)
        return result


def VeyraBalances(tact: str = "τ") -> VeyraBalanceParent:
    """Factory for Veyra balance parent."""
    logger.debug("VeyraBalances entry tact=%r", tact)
    result = VeyraBalanceParent(tact)
    logger.debug("VeyraBalances exit result=%r", result)
    return result
