"""Uniform non-secret logging for the proof-surface implementation."""
from __future__ import annotations

from collections.abc import Callable
from functools import wraps
import logging
from typing import ParamSpec, TypeVar


P = ParamSpec("P")
R = TypeVar("R")


def traced(logger: logging.Logger) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorate a function with entry, exit, and propagated-error logs."""
    logger.debug("traced entry logger=%s", logger.name)

    def decorate(function: Callable[P, R]) -> Callable[P, R]:
        logger.debug("traced decorate state function=%s", function.__name__)

        @wraps(function)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            logger.debug("%s entry", function.__name__)
            try:
                result = function(*args, **kwargs)
            except Exception as exc:
                logger.debug("%s error state type=%s detail=%s", function.__name__, type(exc).__name__, exc)
                raise
            logger.debug("%s exit state=result-type:%s", function.__name__, type(result).__name__)
            return result

        logger.debug("traced decorate exit function=%s", function.__name__)
        return wrapped

    logger.debug("traced exit logger=%s", logger.name)
    return decorate
