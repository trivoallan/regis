"""Playbook evaluation engine — backward-compatible re-export module.

All symbols are now implemented in the sub-modules of this package.
This file re-exports them so that existing imports of the form::

    from regis.playbook.engine import evaluate, load_playbook, _flatten, ...

continue to work without modification.
"""

from __future__ import annotations

# Condition helpers
from regis.playbook.conditions import _stringify_condition

# Context helpers
from regis.playbook.context import (
    MissingDataTracker,
    NamedList,
    _flatten,
)

# Top-level orchestrator
from regis.playbook.evaluator import evaluate

# Loader
from regis.playbook.loader import bundle_meta_schema_path, is_bundle, load_playbook

# Section evaluator (kept for any internal consumers)
from regis.playbook.sections import _evaluate_section

# Template helpers
from regis.playbook.templates import (
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
    "is_bundle",
    "bundle_meta_schema_path",
    # sections
    "_evaluate_section",
    # evaluator
    "evaluate",
]
