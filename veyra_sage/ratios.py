"""Sage-native/fallback Veyra ratio parent and element."""

from __future__ import annotations

from fractions import Fraction
import logging

from src.core.ratio import (
    RatioMode,
    add_ratios,
    add_ratios_raw,
    canonical_ratio,
    inverse_ratio,
    multiply_ratios,
    multiply_ratios_raw,
    ratio_from_fraction,
    ratio_from_ints,
    ratio_shadow,
    subtract_ratios,
    subtract_ratios_raw,
)

from .modes import Element, Parent, SAGE_AVAILABLE

logger = logging.getLogger(__name__)


class VeyraRatioParent(Parent):
    """Parent/factory for Veyra ratio elements over one tact."""

    def __init__(self, tact: str = "τ"):
        """Create ratio parent."""
        logger.debug("VeyraRatioParent.__init__ entry tact=%r", tact)
        if not tact:
            logger.error("VeyraRatioParent empty tact")
            raise ValueError("tact must be non-empty")
        self.tact = tact
        if SAGE_AVAILABLE:
            Parent.__init__(self)
        logger.debug("VeyraRatioParent.__init__ exit tact=%r", self.tact)

    def _element_constructor_(self, value: object, denominator: int | None = None) -> "VeyraRatioElement":
        """Construct ratio element from core ratio, Fraction, int, or pair."""
        logger.debug("VeyraRatioParent._element_constructor_ entry value=%r denominator=%r", value, denominator)
        ratio = self._coerce_ratio(value, denominator)
        result = VeyraRatioElement(self, ratio)
        logger.debug("VeyraRatioParent._element_constructor_ exit result=%s", result.word)
        return result

    def _coerce_ratio(self, value: object, denominator: int | None = None) -> RatioMode:
        """Coerce a Python/core value into RatioMode."""
        logger.debug("VeyraRatioParent._coerce_ratio entry value=%r denominator=%r", value, denominator)
        if isinstance(value, VeyraRatioElement):
            result = value.ratio
        elif isinstance(value, RatioMode):
            result = value
        elif isinstance(value, Fraction):
            result = ratio_from_fraction(value, self.tact)
        elif isinstance(value, int):
            result = ratio_from_ints(value, 1 if denominator is None else denominator, self.tact)
        elif isinstance(value, tuple) and len(value) == 2:
            result = ratio_from_ints(int(value[0]), int(value[1]), self.tact)
        else:
            logger.error("VeyraRatioParent cannot coerce value=%r", value)
            raise TypeError(f"cannot build Veyra ratio from {type(value)!r}")
        logger.debug("VeyraRatioParent._coerce_ratio exit result=%s", result.word)
        return result

    def __call__(self, value: object, denominator: int | None = None) -> "VeyraRatioElement":
        """Fallback/Sage-compatible element construction."""
        logger.debug("VeyraRatioParent.__call__ entry value=%r denominator=%r", value, denominator)
        if SAGE_AVAILABLE:
            result = Parent.__call__(self, value, denominator)
        else:
            result = self._element_constructor_(value, denominator)
        logger.debug("VeyraRatioParent.__call__ exit result=%s", result.word)
        return result

    def _repr_(self) -> str:
        """Sage repr."""
        return f"Veyra ratios over tact {self.tact!r}"

    def __repr__(self) -> str:
        """Python repr."""
        return self._repr_()

    def zero(self) -> "VeyraRatioElement":
        """Return zero ratio."""
        logger.debug("VeyraRatioParent.zero entry")
        result = self(0)
        logger.debug("VeyraRatioParent.zero exit result=%s", result.word)
        return result

    def one(self) -> "VeyraRatioElement":
        """Return unit ratio."""
        logger.debug("VeyraRatioParent.one entry")
        result = self(1)
        logger.debug("VeyraRatioParent.one exit result=%s", result.word)
        return result


class VeyraRatioElement(Element):
    """Veyra ratio element with Sage-style arithmetic."""

    def __init__(self, parent: VeyraRatioParent, ratio: RatioMode):
        """Create ratio element."""
        logger.debug("VeyraRatioElement.__init__ entry ratio=%s", ratio.word)
        self._parent = parent
        self.ratio = ratio
        if SAGE_AVAILABLE:
            Element.__init__(self, parent)
        logger.debug("VeyraRatioElement.__init__ exit")

    @property
    def word(self) -> str:
        """Return compact ratio word."""
        logger.debug("VeyraRatioElement.word entry")
        result = self.ratio.word
        logger.debug("VeyraRatioElement.word exit result=%s", result)
        return result

    def parent(self) -> VeyraRatioParent:
        """Return parent in fallback mode."""
        logger.debug("VeyraRatioElement.parent entry")
        result = self._parent
        logger.debug("VeyraRatioElement.parent exit result=%r", result)
        return result

    def _repr_(self) -> str:
        """Sage repr."""
        return self.word

    def __repr__(self) -> str:
        """Python repr."""
        return self.word

    def __eq__(self, other: object) -> bool:
        """Compare by exact rational shadow."""
        logger.debug("VeyraRatioElement.__eq__ entry other=%r", other)
        result = isinstance(other, VeyraRatioElement) and self.shadow() == other.shadow()
        logger.debug("VeyraRatioElement.__eq__ exit result=%s", result)
        return result

    def _coerce_other(self, other: object) -> "VeyraRatioElement":
        """Coerce other value through this parent."""
        logger.debug("VeyraRatioElement._coerce_other entry other=%r", other)
        result = other if isinstance(other, VeyraRatioElement) else self.parent()(other)
        logger.debug("VeyraRatioElement._coerce_other exit result=%s", result.word)
        return result

    def shadow(self) -> Fraction:
        """Return exact rational shadow."""
        logger.debug("VeyraRatioElement.shadow entry ratio=%s", self.word)
        result = ratio_shadow(self.ratio)
        logger.debug("VeyraRatioElement.shadow exit result=%s", result)
        return result

    def canonical(self) -> "VeyraRatioElement":
        """Return canonical length-shadow form."""
        logger.debug("VeyraRatioElement.canonical entry ratio=%s", self.word)
        result = self.parent()(canonical_ratio(self.ratio, self.parent().tact))
        logger.debug("VeyraRatioElement.canonical exit result=%s", result.word)
        return result

    def raw_add(self, other: object) -> "VeyraRatioElement":
        """Add without canonical collapse."""
        logger.debug("VeyraRatioElement.raw_add entry left=%s other=%r", self.word, other)
        rhs = self._coerce_other(other)
        result = self.parent()(add_ratios_raw(self.ratio, rhs.ratio))
        logger.debug("VeyraRatioElement.raw_add exit result=%s", result.word)
        return result

    def raw_sub(self, other: object) -> "VeyraRatioElement":
        """Subtract without canonical collapse."""
        logger.debug("VeyraRatioElement.raw_sub entry left=%s other=%r", self.word, other)
        rhs = self._coerce_other(other)
        result = self.parent()(subtract_ratios_raw(self.ratio, rhs.ratio))
        logger.debug("VeyraRatioElement.raw_sub exit result=%s", result.word)
        return result

    def raw_mul(self, other: object) -> "VeyraRatioElement":
        """Multiply without canonical collapse."""
        logger.debug("VeyraRatioElement.raw_mul entry left=%s other=%r", self.word, other)
        rhs = self._coerce_other(other)
        result = self.parent()(multiply_ratios_raw(self.ratio, rhs.ratio))
        logger.debug("VeyraRatioElement.raw_mul exit result=%s", result.word)
        return result

    def _add_(self, other: object) -> "VeyraRatioElement":
        """Sage addition hook."""
        logger.debug("VeyraRatioElement._add_ entry left=%s other=%r", self.word, other)
        rhs = self._coerce_other(other)
        result = self.parent()(add_ratios(self.ratio, rhs.ratio, self.parent().tact))
        logger.debug("VeyraRatioElement._add_ exit result=%s", result.word)
        return result

    def __add__(self, other: object) -> "VeyraRatioElement":
        """Python addition hook."""
        logger.debug("VeyraRatioElement.__add__ entry left=%s other=%r", self.word, other)
        result = self._add_(other)
        logger.debug("VeyraRatioElement.__add__ exit result=%s", result.word)
        return result

    def __sub__(self, other: object) -> "VeyraRatioElement":
        """Python subtraction hook."""
        logger.debug("VeyraRatioElement.__sub__ entry left=%s other=%r", self.word, other)
        rhs = self._coerce_other(other)
        result = self.parent()(subtract_ratios(self.ratio, rhs.ratio, self.parent().tact))
        logger.debug("VeyraRatioElement.__sub__ exit result=%s", result.word)
        return result

    def __mul__(self, other: object) -> "VeyraRatioElement":
        """Python multiplication hook."""
        logger.debug("VeyraRatioElement.__mul__ entry left=%s other=%r", self.word, other)
        rhs = self._coerce_other(other)
        result = self.parent()(multiply_ratios(self.ratio, rhs.ratio, self.parent().tact))
        logger.debug("VeyraRatioElement.__mul__ exit result=%s", result.word)
        return result

    def inverse(self) -> "VeyraRatioElement":
        """Return multiplicative inverse."""
        logger.debug("VeyraRatioElement.inverse entry ratio=%s", self.word)
        result = self.parent()(inverse_ratio(self.ratio, self.parent().tact))
        logger.debug("VeyraRatioElement.inverse exit result=%s", result.word)
        return result


def VeyraRatios(tact: str = "τ") -> VeyraRatioParent:
    """Factory for Veyra ratio parent."""
    logger.debug("VeyraRatios entry tact=%r", tact)
    result = VeyraRatioParent(tact)
    logger.debug("VeyraRatios exit result=%r", result)
    return result
