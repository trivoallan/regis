"""Pure predicate helpers shared by rule operators and meta validation.

These functions are intentionally free of any ``json_logic`` dependency so they
can be reused by :mod:`regis.analyzers.metadata` (format checking) and unit-tested
in isolation. They follow a defensive style: unexpected input types yield a falsy
result rather than raising.
"""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_TRUTHY = {"true", "1", "yes", "on"}
_FALSY = {"false", "0", "no", "off"}


def is_truthy(value: Any) -> bool:
    """True for boolean ``True`` or a truthy string (true/1/yes/on, case-insensitive)."""
    if value is True:
        return True
    return isinstance(value, str) and value.strip().lower() in _TRUTHY


def is_falsy(value: Any) -> bool:
    """True for boolean ``False`` or a falsy string (false/0/no/off, case-insensitive).

    Not the strict complement of :func:`is_truthy`: a junk string ("maybe") is
    neither truthy nor falsy.
    """
    if value is False:
        return True
    return isinstance(value, str) and value.strip().lower() in _FALSY


def is_url(value: Any) -> bool:
    """True if ``value`` is a well-formed http/https URL (scheme + netloc).

    Relies on ``urllib.parse.urlparse`` but additionally rejects a ``netloc``
    containing whitespace (urlparse otherwise accepts such malformed values),
    so it is suitable as a ``format: uri`` checker for well-formed URL fields.
    """
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value)
    except (ValueError, AttributeError):
        return False
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    return not any(ch.isspace() for ch in parsed.netloc)


def is_empty(value: Any) -> bool:
    """True if ``value`` is None, an empty string, or whitespace-only."""
    return value is None or (isinstance(value, str) and value.strip() == "")


def matches(value: Any, pattern: Any) -> bool:
    """True if ``value`` (a string) matches the regular expression ``pattern``.

    Non-string input or an invalid regex yields ``False`` (a warning is logged for
    the latter).
    """
    if not isinstance(value, str) or not isinstance(pattern, str):
        return False
    try:
        return bool(re.search(pattern, value))
    except re.error:
        logger.warning("matches: invalid regex pattern %r", pattern)
        return False
