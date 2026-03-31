"""Jinja2 template environment and path-resolution utilities.

Provides:
- ``_WIDGET_ENV``       — Jinja2 environment with custom filters
- ``_format_*``         — Jinja2 filter functions (date, datetime, time, number)
- ``_resolve_template`` — Render a string as a Jinja2 template
- ``_resolve_path``     — Resolve a dot-separated path in a nested context
"""

from __future__ import annotations

import logging
from typing import Any

from jinja2 import BaseLoader, ChainableUndefined, Environment

from regis.playbook.context import NamedList

logger = logging.getLogger(__name__)


def _format_date(v: str) -> str:
    from datetime import datetime

    try:
        return datetime.fromisoformat(v).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return v


def _format_datetime(v: str) -> str:
    from datetime import datetime

    try:
        return datetime.fromisoformat(v).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return v


def _format_time(v: str) -> str:
    from datetime import datetime

    try:
        return datetime.fromisoformat(v).strftime("%H:%M:%S")
    except (ValueError, TypeError):
        return v


def _format_number(v: Any) -> str:
    try:
        return f"{int(v):,}"
    except (ValueError, TypeError):
        return str(v)


_WIDGET_ENV = Environment(
    loader=BaseLoader(), undefined=ChainableUndefined, autoescape=True
)
_WIDGET_ENV.filters["format_date"] = _format_date
_WIDGET_ENV.filters["format_datetime"] = _format_datetime
_WIDGET_ENV.filters["format_time"] = _format_time
_WIDGET_ENV.filters["format_number"] = _format_number


def _resolve_template(
    template_str: Any,
    context: dict[str, Any],
    nested_context: dict[str, Any] | None = None,
) -> Any:
    """Evaluate a string strictly as a Jinja2 template."""
    if not isinstance(template_str, str):
        return template_str
    try:
        render_ctx = nested_context if nested_context is not None else context
        template = _WIDGET_ENV.from_string(template_str)
        return template.render(**render_ctx)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to resolve Jinja2 template '%s': %s", template_str, exc)
        return template_str


def _resolve_path(
    path: Any, context: dict[str, Any], nested_context: dict[str, Any] | None = None
) -> Any:
    """Resolve a dot-separated path in a nested context.

    Supports list indexing with integers (e.g. 'playbooks.0.score').
    Also supports Jinja2 templates (pipes or ``{{ }}`` syntax).
    """
    if not isinstance(path, str):
        return path

    # If it contains | or is wrapped in {{ }}, use Jinja2
    if "|" in path or ("{{" in path and "}}" in path):
        try:
            render_ctx = nested_context if nested_context is not None else context
            template = _WIDGET_ENV.from_string(path)
            return template.render(**render_ctx)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Failed to resolve Jinja2 path '%s': %s", path, exc)
            return path

    # Basic cleanup if user used Jinja-like braces or bracket indexing
    clean_path = path.strip("{} ").replace("[", ".").replace("]", "")

    parts = clean_path.split(".")
    val: Any = context
    for part in parts:
        if not part:
            continue
        if isinstance(val, dict):
            val = val.get(part)
        elif isinstance(val, list):
            # First try integer index
            try:
                idx = int(part)
                val = val[idx] if 0 <= idx < len(val) else None
            except ValueError:
                # If it's a NamedList, let it try the string key
                if isinstance(val, NamedList):
                    try:
                        val = val[part]
                    except KeyError:
                        return None
                else:
                    return None
        else:
            return None
    return val
