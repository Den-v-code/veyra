"""Sage-native/fallback Veyra polynomial parent and element."""

from __future__ import annotations

from fractions import Fraction
import logging

from src.core.polynomial import (
    Polynomial,
    add_polynomials,
    derivative_polynomial,
    eval_polynomial,
    multiply_polynomials,
    normalize_polynomial,
)
from src.core.ratio import RatioMode, multiply_ratios, ratio_from_ints, ratio_shadow

from .modes import Element, Parent, SAGE_AVAILABLE
from .ratios import VeyraRatioElement, VeyraRatioParent, VeyraRatios

logger = logging.getLogger(__name__)


class VeyraPolynomialParent(Parent):
    """Parent/factory for Veyra polynomial ratio forms."""

    def __init__(self, tact: str = "τ", variable: str = "x"):
        """Create polynomial parent."""
        logger.debug("VeyraPolynomialParent.__init__ entry tact=%r variable=%r", tact, variable)
        if not variable:
            logger.error("VeyraPolynomialParent empty variable")
            raise ValueError("variable must be non-empty")
        self.ratios = VeyraRatios(tact)
        self.variable = variable
        if SAGE_AVAILABLE:
            Parent.__init__(self)
        logger.debug("VeyraPolynomialParent.__init__ exit tact=%r variable=%r", tact, variable)

    @property
    def tact(self) -> str:
        """Return coefficient tact."""
        logger.debug("VeyraPolynomialParent.tact entry")
        result = self.ratios.tact
        logger.debug("VeyraPolynomialParent.tact exit result=%r", result)
        return result

    def _element_constructor_(self, coefficients: object) -> "VeyraPolynomialElement":
        """Construct polynomial element from core polynomial or coefficients."""
        logger.debug("VeyraPolynomialParent._element_constructor_ entry coefficients=%r", coefficients)
        poly = self._coerce_polynomial(coefficients)
        result = VeyraPolynomialElement(self, poly)
        logger.debug("VeyraPolynomialParent._element_constructor_ exit result=%s", result.word)
        return result

    def _coerce_polynomial(self, coefficients: object) -> Polynomial:
        """Coerce value into a core polynomial."""
        logger.debug("VeyraPolynomialParent._coerce_polynomial entry coefficients=%r", coefficients)
        if isinstance(coefficients, VeyraPolynomialElement):
            result = coefficients.polynomial
        elif isinstance(coefficients, Polynomial):
            result = coefficients
        elif isinstance(coefficients, (list, tuple)):
            result = Polynomial(tuple(self._coerce_ratio(item) for item in coefficients))
        else:
            result = Polynomial((self._coerce_ratio(coefficients),))
        result = normalize_polynomial(result)
        logger.debug("VeyraPolynomialParent._coerce_polynomial exit degree=%d", result.degree)
        return result

    def _coerce_ratio(self, value: object) -> RatioMode:
        """Coerce coefficient into RatioMode."""
        logger.debug("VeyraPolynomialParent._coerce_ratio entry value=%r", value)
        if isinstance(value, VeyraRatioElement):
            result = value.ratio
        elif isinstance(value, RatioMode):
            result = value
        elif isinstance(value, Fraction):
            result = self.ratios(value).ratio
        elif isinstance(value, int):
            result = ratio_from_ints(value, 1, self.tact)
        elif isinstance(value, tuple) and len(value) == 2:
            result = self.ratios(value).ratio
        else:
            logger.error("VeyraPolynomialParent cannot coerce coefficient=%r", value)
            raise TypeError(f"cannot build polynomial coefficient from {type(value)!r}")
        logger.debug("VeyraPolynomialParent._coerce_ratio exit result=%s", result.word)
        return result

    def __call__(self, coefficients: object) -> "VeyraPolynomialElement":
        """Fallback/Sage-compatible element construction."""
        logger.debug("VeyraPolynomialParent.__call__ entry coefficients=%r", coefficients)
        if SAGE_AVAILABLE:
            result = Parent.__call__(self, coefficients)
        else:
            result = self._element_constructor_(coefficients)
        logger.debug("VeyraPolynomialParent.__call__ exit result=%s", result.word)
        return result

    def _repr_(self) -> str:
        """Sage repr."""
        return f"Veyra polynomials in {self.variable} over tact {self.tact!r}"

    def __repr__(self) -> str:
        """Python repr."""
        return self._repr_()

    def zero(self) -> "VeyraPolynomialElement":
        """Return zero polynomial."""
        logger.debug("VeyraPolynomialParent.zero entry")
        result = self([0])
        logger.debug("VeyraPolynomialParent.zero exit result=%s", result.word)
        return result

    def one(self) -> "VeyraPolynomialElement":
        """Return unit polynomial."""
        logger.debug("VeyraPolynomialParent.one entry")
        result = self([1])
        logger.debug("VeyraPolynomialParent.one exit result=%s", result.word)
        return result


class VeyraPolynomialElement(Element):
    """Veyra polynomial element with Sage-style operations."""

    def __init__(self, parent: VeyraPolynomialParent, polynomial: Polynomial):
        """Create polynomial element."""
        logger.debug("VeyraPolynomialElement.__init__ entry degree=%d", polynomial.degree)
        self._parent = parent
        self.polynomial = polynomial
        if SAGE_AVAILABLE:
            Element.__init__(self, parent)
        logger.debug("VeyraPolynomialElement.__init__ exit")

    @property
    def word(self) -> str:
        """Return compact polynomial word."""
        logger.debug("VeyraPolynomialElement.word entry")
        parts = [coeff.word for coeff in self.polynomial.coefficients]
        result = f"P_{self.parent().variable}[{', '.join(parts)}]"
        logger.debug("VeyraPolynomialElement.word exit result=%s", result)
        return result

    def parent(self) -> VeyraPolynomialParent:
        """Return parent in fallback mode."""
        logger.debug("VeyraPolynomialElement.parent entry")
        result = self._parent
        logger.debug("VeyraPolynomialElement.parent exit result=%r", result)
        return result

    def _repr_(self) -> str:
        """Sage repr."""
        return self.word

    def __repr__(self) -> str:
        """Python repr."""
        return self.word

    def __eq__(self, other: object) -> bool:
        """Compare by exact coefficient shadows."""
        logger.debug("VeyraPolynomialElement.__eq__ entry other=%r", other)
        result = isinstance(other, VeyraPolynomialElement) and self.coefficient_shadows() == other.coefficient_shadows()
        logger.debug("VeyraPolynomialElement.__eq__ exit result=%s", result)
        return result

    def _coerce_other(self, other: object) -> "VeyraPolynomialElement":
        """Coerce other value through this parent."""
        logger.debug("VeyraPolynomialElement._coerce_other entry other=%r", other)
        result = other if isinstance(other, VeyraPolynomialElement) else self.parent()(other)
        logger.debug("VeyraPolynomialElement._coerce_other exit result=%s", result.word)
        return result

    def degree(self) -> int:
        """Return polynomial degree."""
        logger.debug("VeyraPolynomialElement.degree entry")
        result = self.polynomial.degree
        logger.debug("VeyraPolynomialElement.degree exit result=%d", result)
        return result

    def coefficient_shadows(self) -> list[Fraction]:
        """Return exact rational coefficient shadows."""
        logger.debug("VeyraPolynomialElement.coefficient_shadows entry")
        result = [ratio_shadow(coeff) for coeff in self.polynomial.coefficients]
        logger.debug("VeyraPolynomialElement.coefficient_shadows exit result=%r", result)
        return result

    def evaluate(self, value: object) -> VeyraRatioElement:
        """Evaluate polynomial at a ratio-like value."""
        logger.debug("VeyraPolynomialElement.evaluate entry value=%r", value)
        ratio = self.parent().ratios(value).ratio
        result = self.parent().ratios(eval_polynomial(self.polynomial, ratio))
        logger.debug("VeyraPolynomialElement.evaluate exit result=%s", result.word)
        return result

    def derivative(self) -> "VeyraPolynomialElement":
        """Return formal derivative."""
        logger.debug("VeyraPolynomialElement.derivative entry degree=%d", self.degree())
        result = self.parent()(derivative_polynomial(self.polynomial))
        logger.debug("VeyraPolynomialElement.derivative exit result=%s", result.word)
        return result

    def _add_(self, other: object) -> "VeyraPolynomialElement":
        """Sage addition hook."""
        logger.debug("VeyraPolynomialElement._add_ entry left=%s other=%r", self.word, other)
        rhs = self._coerce_other(other)
        result = self.parent()(add_polynomials(self.polynomial, rhs.polynomial))
        logger.debug("VeyraPolynomialElement._add_ exit result=%s", result.word)
        return result

    def __add__(self, other: object) -> "VeyraPolynomialElement":
        """Python addition hook."""
        logger.debug("VeyraPolynomialElement.__add__ entry left=%s other=%r", self.word, other)
        result = self._add_(other)
        logger.debug("VeyraPolynomialElement.__add__ exit result=%s", result.word)
        return result

    def _mul_(self, other: object) -> "VeyraPolynomialElement":
        """Sage multiplication hook."""
        logger.debug("VeyraPolynomialElement._mul_ entry left=%s other=%r", self.word, other)
        rhs = self._coerce_other(other)
        result = self.parent()(multiply_polynomials(self.polynomial, rhs.polynomial))
        logger.debug("VeyraPolynomialElement._mul_ exit result=%s", result.word)
        return result

    def __mul__(self, other: object) -> "VeyraPolynomialElement":
        """Python multiplication hook."""
        logger.debug("VeyraPolynomialElement.__mul__ entry left=%s other=%r", self.word, other)
        result = self._mul_(other)
        logger.debug("VeyraPolynomialElement.__mul__ exit result=%s", result.word)
        return result

    def scale(self, value: object) -> "VeyraPolynomialElement":
        """Scale all coefficients by a ratio-like value."""
        logger.debug("VeyraPolynomialElement.scale entry value=%r", value)
        ratio = self.parent().ratios(value).ratio
        coeffs = tuple(multiply_ratios(coeff, ratio, self.parent().tact) for coeff in self.polynomial.coefficients)
        result = self.parent()(Polynomial(coeffs))
        logger.debug("VeyraPolynomialElement.scale exit result=%s", result.word)
        return result


def VeyraPolynomials(tact: str = "τ", variable: str = "x") -> VeyraPolynomialParent:
    """Factory for Veyra polynomial parent."""
    logger.debug("VeyraPolynomials entry tact=%r variable=%r", tact, variable)
    result = VeyraPolynomialParent(tact, variable)
    logger.debug("VeyraPolynomials exit result=%r", result)
    return result
