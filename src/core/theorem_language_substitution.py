"""Token-aware substitution for the legacy finite-obligation harness."""

from __future__ import annotations

from collections.abc import Mapping
import logging
import re

logger = logging.getLogger(__name__)
_PLACEHOLDER = re.compile(r"\$([A-Za-z][A-Za-z0-9_-]*)")
_LEFT_DELIMITERS = frozenset({"(", ","})
_RIGHT_DELIMITERS = frozenset({")", ","})


def template_variables(template: str) -> tuple[str, ...]:
    """Return placeholders that occupy complete expression positions."""
    logger.debug("template_variables entry template=%r", template)
    matches = tuple(_PLACEHOLDER.finditer(template))
    starts = frozenset(match.start() for match in matches)
    if any(char == "$" and index not in starts for index, char in enumerate(template)):
        logger.error("template_variables invalid placeholder syntax template=%r", template)
        raise ValueError("invalid theorem placeholder syntax")
    for match in matches:
        left = template[: match.start()].rstrip()
        right = template[match.end() :].lstrip()
        if (left and left[-1] not in _LEFT_DELIMITERS) or (
            right and right[0] not in _RIGHT_DELIMITERS
        ):
            logger.error(
                "template_variables placeholder is not expression token token=%s",
                match.group(0),
            )
            raise ValueError(
                f"theorem placeholder {match.group(0)} must occupy a complete expression"
            )
    result = tuple(match.group(1) for match in matches)
    logger.debug("template_variables exit variables=%r", result)
    return result


def substitute_template(template: str, assignments: Mapping[str, str]) -> str:
    """Substitute exact ``$identifier`` tokens without prefix capture."""
    logger.debug(
        "substitute_template entry template=%r assignment_count=%d",
        template,
        len(assignments),
    )
    template_variables(template)
    if any("$" in value for value in assignments.values()):
        logger.error("substitute_template replacement contains placeholder marker")
        raise ValueError("theorem assignment cannot contain a placeholder marker")

    def replacement(match: re.Match[str]) -> str:
        logger.debug("substitute_template.replacement entry token=%s", match.group(0))
        name = match.group(1)
        value = assignments.get(name)
        if value is None:
            logger.error("substitute_template.replacement missing assignment name=%s", name)
            raise ValueError(f"missing theorem assignment ${name}")
        logger.debug("substitute_template.replacement exit name=%s", name)
        return value

    result = _PLACEHOLDER.sub(replacement, template)
    logger.debug("substitute_template exit result=%r", result)
    return result
