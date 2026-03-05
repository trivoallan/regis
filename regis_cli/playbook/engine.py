"""Playbook evaluation engine — backward-compatible re-export module.

All symbols are now implemented in the sub-modules of this package.
This file re-exports them so that existing imports of the form::

    from regis_cli.playbook.engine import evaluate, load_playbook, _flatten, ...

continue to work without modification.
"""

from __future__ import annotations

# Condition helpers
from regis_cli.playbook.conditions import _stringify_condition

# Context helpers
from regis_cli.playbook.context import (
    MissingDataTracker,
    NamedList,
    _flatten,
)

# Top-level orchestrator
from regis_cli.playbook.evaluator import evaluate

# Loader
from regis_cli.playbook.loader import load_playbook

# Section evaluator (kept for any internal consumers)
from regis_cli.playbook.sections import _evaluate_section

# Template helpers
from regis_cli.playbook.templates import (
    _format_date,
    _format_datetime,
    _format_number,
    _format_time,
    _resolve_path,
    _resolve_template,
)

__all__ = [
    # context
    "MissingDataTracker",
    "NamedList",
    "_flatten",
    # conditions
    "_stringify_condition",
    # templates
    "_format_date",
    "_format_datetime",
    "_format_number",
    "_format_time",
    "_resolve_path",
    "_resolve_template",
    # loader
    "load_playbook",
    # sections
    "_evaluate_section",
    # evaluator
    "evaluate",
]
