"""GitLab integration resolvers for the playbook engine.

Evaluates GitLab-specific playbook directives (labels, MR description
checklists, MR templates) against the full evaluation context.
"""

from __future__ import annotations

import logging
from typing import Any

from regis_cli.playbook.conditions import evaluate_condition

logger = logging.getLogger(__name__)


def _resolve_labels(
    integration: dict[str, Any],
    full_context: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate GitLab label conditions and return resolved label names."""
    label_defs = integration.get("labels", [])
    if not label_defs:
        return {}

    resolved_labels: list[str] = []
    for label_def in label_defs:
        condition = label_def.get("condition")
        if condition:
            result = evaluate_condition(
                condition, full_context, label=label_def.get("name", "")
            )
            if result and result.passed:
                resolved_labels.append(label_def["name"])
        else:
            resolved_labels.append(label_def["name"])

    return {"labels": list(set(resolved_labels))}


def _resolve_checklists(
    integration: dict[str, Any],
    full_context: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate GitLab MR description checklist items."""
    checklist_defs = integration.get("checklist")
    checklists_defs = integration.get("checklists", [])

    # Backwards compatibility: wrap old `checklist` into the new `checklists` format
    if checklist_defs is not None and not checklists_defs:
        checklists_defs = [{"items": checklist_defs}]

    if not checklists_defs:
        return {}

    resolved_checklists: list[dict[str, Any]] = []
    for checklist_def in checklists_defs:
        title = checklist_def.get("title", "📝 Review Checklist")
        items = checklist_def.get("items", [])
        if not items:
            continue

        resolved_items: list[dict[str, Any]] = []
        for item_def in items:
            label = item_def.get("label", "")
            if not label:
                continue

            # --- display condition ---
            show_condition = item_def.get("show_if")
            if show_condition:
                result = evaluate_condition(show_condition, full_context, label=label)
                if result is None or not result.passed or result.incomplete:
                    continue

            # --- checked condition ---
            checked = False
            checked_condition = item_def.get("check_if")
            if checked_condition:
                result = evaluate_condition(
                    checked_condition, full_context, label=label
                )
                if result is not None:
                    checked = result.passed and not result.incomplete

            resolved_items.append({"label": label, "checked": checked})

        if resolved_items:
            resolved_checklists.append({"title": title, "items": resolved_items})

    if resolved_checklists:
        return {"mr_description_checklists": resolved_checklists}
    return {}


def _resolve_templates(
    integration: dict[str, Any],
    full_context: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate GitLab MR template conditions and return resolved template entries."""
    template_defs = integration.get("templates", [])
    if not template_defs:
        return {}

    resolved_templates: list[dict[str, str]] = []
    for tmpl_def in template_defs:
        url = tmpl_def.get("url")
        if not url:
            continue

        condition = tmpl_def.get("condition")
        if condition:
            result = evaluate_condition(condition, full_context, label=url)
            if result is None:
                pass  # no condition → include
            elif not result.passed or result.incomplete:
                continue

        resolved_tmpl: dict[str, str] = {"url": url}
        if tmpl_def.get("directory"):
            resolved_tmpl["directory"] = tmpl_def["directory"]
        resolved_templates.append(resolved_tmpl)

    if resolved_templates:
        return {"mr_templates": resolved_templates}
    return {}


def resolve_gitlab_integration(
    playbook: dict[str, Any],
    full_context: dict[str, Any],
) -> dict[str, Any]:
    """Resolve all GitLab integration directives (labels, checklists, templates).

    Returns a dict merged into the evaluation result by the orchestrator.
    """
    integration = playbook.get("integrations", {}).get("gitlab", {})
    result: dict[str, Any] = {}
    result.update(_resolve_labels(integration, full_context))
    result.update(_resolve_checklists(integration, full_context))
    result.update(_resolve_templates(integration, full_context))
    return result
