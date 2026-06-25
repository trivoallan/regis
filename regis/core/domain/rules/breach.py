"""Shared ``--fail`` breach detection.

Which non-passing rules meet the requested fail threshold. Extracted so the
``analyze`` use-case and the ``analyze`` / ``rules evaluate`` CLI commands share
one definition. They had drifted into three copies of a ``level_order`` map that
disagreed on the ``none``/unknown fail level (one treated it as "never fail",
another as "fail on everything", a third as "fail as if critical"), so the same
``--fail-level`` could behave differently per command. This is the single source
of truth.

Severity rank: lower = more severe. A non-passing rule breaches when its own
level is at or above the requested fail level (``rank <= threshold``). An unknown
or ``"none"`` fail level yields no threshold, so nothing breaches.

    fail_level   threshold   non-passing rule breaches when its level is...
    ----------   ---------   ----------------------------------------------
    critical         1       critical
    warning          2       critical, warning
    info             3       critical, warning, info (any breach)
    none / other    --       never (no breach)
"""

from __future__ import annotations

from typing import Any

_LEVEL_RANK: dict[str, int] = {"critical": 1, "warning": 2, "info": 3}
# An unlabelled rule level is treated as the least severe known level (info).
_RULE_LEVEL_DEFAULT = _LEVEL_RANK["info"]


def breached_slugs(rules: list[dict[str, Any]], fail_level: str) -> list[str]:
    """Return the slugs of non-passing rules at or above ``fail_level``.

    Empty when ``fail_level`` is ``"none"`` or any value outside
    ``critical``/``warning``/``info`` -- i.e. "do not fail on anything".
    """
    threshold = _LEVEL_RANK.get((fail_level or "").lower())
    if threshold is None:
        return []
    return [
        rule.get("slug", "unknown")
        for rule in rules
        if not rule.get("passed", False)
        and _LEVEL_RANK.get(str(rule.get("level", "info")).lower(), _RULE_LEVEL_DEFAULT)
        <= threshold
    ]
