"""Condition evaluation helpers for the playbook engine.

Provides a single, reusable ``evaluate_condition`` function that wraps
JsonLogic evaluation with ``MissingDataTracker`` support, replacing the
repeated try/except blocks that were scattered across the original engine.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from json_logic import jsonLogic

from regis_cli.playbook.context import MissingDataTracker

logger = logging.getLogger(__name__)


@dataclass
class ConditionResult:
    """Result of a JsonLogic condition evaluation."""

    passed: bool
    incomplete: bool


def evaluate_condition(
    condition: Any,
    context: dict[str, Any],
    *,
    label: str = "unknown",
) -> ConditionResult | None:
    """Evaluate a JsonLogic condition with missing-data tracking.

    Args:
        condition: A JsonLogic condition dict, or ``None`` / falsy to skip.
        context:   The flat or nested data context to evaluate against.
        label:     A human-readable label used in warning log messages.

    Returns:
        ``None`` if *condition* is absent/falsy (caller should not filter).
        A ``ConditionResult`` otherwise — check ``.passed`` and ``.incomplete``.
    """
    if not condition:
        return None
    tracker = MissingDataTracker(context)
    try:
        passed = bool(jsonLogic(condition, tracker))
        return ConditionResult(passed=passed, incomplete=tracker.missing_accessed)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Condition evaluation error for '%s': %s", label, exc)
        return ConditionResult(passed=False, incomplete=True)


def _stringify_condition(condition: Any, context: dict[str, Any]) -> str:
    """Turn a JsonLogic condition into a human-readable string with values.

    Example: {">": [{"var": "a"}, 10]} -> "a (42) > 10"
    """
    if not isinstance(condition, dict) or not condition:
        if condition is None:
            return "MISSING"
        return str(condition)

    op = list(condition.keys())[0]
    args = condition[op]

    # Handle var specifically: "key (value)"
    if op == "var":
        val = context.get(args)
        if val is None:
            return f"{args} (MISSING)"
        return f"{args} ({val})"

    if not isinstance(args, list):
        args = [args]

    # Recurse on arguments
    parts = [_stringify_condition(a, context) for a in args]

    # Pretty-print common operators
    if op in (">", ">=", "<", "<=", "==", "!="):
        if len(parts) >= 2:
            return f"{parts[0]} {op} {parts[1]}"
        return f"{op}({', '.join(parts)})"
    if op == "in" and len(parts) == 2:
        return f"{parts[0]} in {parts[1]}"
    if op == "!" and len(parts) == 1:
        return f"!({parts[0]})"
    if op == "and":
        return " and ".join(f"({p})" for p in parts)
    if op == "or":
        return " or ".join(f"({p})" for p in parts)

    return f"{op}({', '.join(parts)})"
