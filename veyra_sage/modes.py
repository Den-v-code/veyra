"""Sage-native/fallback Veyra mode parent and element."""

from __future__ import annotations

import logging

from src.core.modes import Mode, TEST_FAMILIES, echo_key
from src.core.resonance import resonance_profile
from src.core.tact_similarity import aura_cost_map
from src.core.weighted_resonance import weighted_resonance_profile

logger = logging.getLogger(__name__)

try:
    from sage.structure.element import Element
    from sage.structure.parent import Parent
    SAGE_AVAILABLE = True
except Exception:  # pragma: no cover - exercised when Sage is absent
    Element = object
    Parent = object
    SAGE_AVAILABLE = False


class VeyraModeParent(Parent):
    """Parent/factory for Veyra mode elements over a finite alphabet."""

    def __init__(self, alphabet: list[str] | tuple[str, ...] | str):
        """Create Veyra mode parent."""
        logger.debug("VeyraModeParent.__init__ entry alphabet=%r", alphabet)
        self.alphabet = tuple(alphabet)
        if SAGE_AVAILABLE:
            Parent.__init__(self)
        logger.debug("VeyraModeParent.__init__ exit alphabet=%r", self.alphabet)

    def _element_constructor_(self, word: str | Mode | "VeyraModeElement") -> "VeyraModeElement":
        """Construct an element."""
        logger.debug("VeyraModeParent._element_constructor_ entry word=%r", word)
        if isinstance(word, VeyraModeElement):
            mode = word.mode
        elif isinstance(word, Mode):
            mode = word
        else:
            mode = Mode.from_word(word)
        missing = sorted(set(mode.tacts) - set(self.alphabet))
        if missing:
            logger.error("VeyraModeParent invalid tacts=%r alphabet=%r", missing, self.alphabet)
            raise ValueError(f"tacts outside parent alphabet: {missing}")
        result = VeyraModeElement(self, mode)
        logger.debug("VeyraModeParent._element_constructor_ exit result=%s", result.word)
        return result

    def __call__(self, word: str | Mode | "VeyraModeElement") -> "VeyraModeElement":
        """Fallback/Sage-compatible element construction."""
        logger.debug("VeyraModeParent.__call__ entry word=%r", word)
        if SAGE_AVAILABLE:
            result = Parent.__call__(self, word)
        else:
            result = self._element_constructor_(word)
        logger.debug("VeyraModeParent.__call__ exit result=%s", result.word)
        return result

    def _repr_(self) -> str:
        """Sage repr."""
        return f"Veyra modes over {''.join(self.alphabet)}"

    def __repr__(self) -> str:
        """Python repr."""
        return self._repr_()

    def one(self) -> "VeyraModeElement":
        """Return first non-silent one-tact element."""
        logger.debug("VeyraModeParent.one entry")
        if not self.alphabet:
            logger.error("VeyraModeParent.one empty alphabet")
            raise ValueError("empty alphabet has no one-tact element")
        result = self(self.alphabet[0])
        logger.debug("VeyraModeParent.one exit result=%s", result.word)
        return result


class VeyraModeElement(Element):
    """Veyra mode element with Sage-style methods."""

    def __init__(self, parent: VeyraModeParent, mode: Mode):
        """Create element."""
        logger.debug("VeyraModeElement.__init__ entry mode=%s", mode.word)
        self._parent = parent
        self.mode = mode
        if SAGE_AVAILABLE:
            Element.__init__(self, parent)
        logger.debug("VeyraModeElement.__init__ exit")

    @property
    def word(self) -> str:
        """Return compact mode word."""
        logger.debug("VeyraModeElement.word entry")
        result = self.mode.word
        logger.debug("VeyraModeElement.word exit result=%s", result)
        return result

    def parent(self) -> VeyraModeParent:
        """Return parent in fallback mode."""
        logger.debug("VeyraModeElement.parent entry")
        result = self._parent
        logger.debug("VeyraModeElement.parent exit result=%r", result)
        return result

    def _repr_(self) -> str:
        """Sage repr."""
        return self.word

    def __repr__(self) -> str:
        """Python repr."""
        return self.word

    def __eq__(self, other: object) -> bool:
        """Compare by parent alphabet and mode."""
        logger.debug("VeyraModeElement.__eq__ entry other=%r", other)
        result = isinstance(other, VeyraModeElement) and self.parent().alphabet == other.parent().alphabet and self.mode == other.mode
        logger.debug("VeyraModeElement.__eq__ exit result=%s", result)
        return result

    def echo_key(self, test_name: str = "ordered") -> tuple[object, ...]:
        """Return echo key for a named core test family."""
        logger.debug("VeyraModeElement.echo_key entry test=%s", test_name)
        tests = TEST_FAMILIES[test_name]
        result = echo_key(self.mode, tests)
        logger.debug("VeyraModeElement.echo_key exit result=%r", result)
        return result

    def cyclic_resonates(self, whole: "VeyraModeElement") -> bool:
        """Return True iff self cyclic-resonates in whole."""
        logger.debug("VeyraModeElement.cyclic_resonates entry part=%s whole=%s", self.word, whole.word)
        result = resonance_profile(self.mode, whole.mode).cyclic
        logger.debug("VeyraModeElement.cyclic_resonates exit result=%s", result)
        return result

    def resonance_profile(self, whole: "VeyraModeElement"):
        """Return core resonance profile."""
        logger.debug("VeyraModeElement.resonance_profile entry part=%s whole=%s", self.word, whole.word)
        result = resonance_profile(self.mode, whole.mode)
        logger.debug("VeyraModeElement.resonance_profile exit result=%r", result)
        return result

    def aura_costs(self) -> dict[tuple[str, str], float]:
        """Return aura-derived costs using this mode as context."""
        logger.debug("VeyraModeElement.aura_costs entry mode=%s", self.word)
        result = aura_cost_map([self.mode], self.parent().alphabet)
        logger.debug("VeyraModeElement.aura_costs exit count=%d", len(result))
        return result

    def weighted_resonates(self, whole: "VeyraModeElement", budget: float = 0.5) -> bool:
        """Return weighted resonance using aura costs from whole context."""
        logger.debug("VeyraModeElement.weighted_resonates entry part=%s whole=%s", self.word, whole.word)
        costs = aura_cost_map([whole.mode], whole.parent().alphabet)
        result = weighted_resonance_profile(self.mode, whole.mode, budget, costs).resonates
        logger.debug("VeyraModeElement.weighted_resonates exit result=%s", result)
        return result


def VeyraModes(alphabet: list[str] | tuple[str, ...] | str) -> VeyraModeParent:
    """Factory for Veyra mode parent."""
    logger.debug("VeyraModes entry alphabet=%r", alphabet)
    result = VeyraModeParent(alphabet)
    logger.debug("VeyraModes exit result=%r", result)
    return result
