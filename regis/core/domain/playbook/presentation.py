"""Presentation resolvers for the playbook engine.

Evaluates platform-neutral presentation directives (labels from badges,
checklists, templates) against the full evaluation context. Consumed by
downstream integrations (GitLab MR, GitHub PR, Backstage, …).
"""

from __future__ import annotations

import logging
from typing import Any

from regis.core.domain.playbook.conditions import evaluate_condition

logger = logging.getLogger(__name__)


def _resolve_badge_labels(
    integration: dict[str, Any],
    full_context: dict[str, Any],
) -> dict[str, Any]:
    """Resolve badge slugs to platform labels surfaced to downstream integrations."""
    badge_slugs = integration.get("badges", [])
    if not badge_slugs:
        return {}

    # Get available badges for lookup
    available_badges = {
        b["slug"]: b for b in full_context.get("badges", []) if "slug" in b
    }

    resolved_badge_labels: list[dict[str, Any]] = []
    for slug in badge_slugs:
        if slug in available_badges:
            badge = available_badges[slug]
            resolved_badge_labels.append(
                {
                    "name": badge["label"],
                    "class": badge["class"],
                }
            )

    if resolved_badge_labels:
        return {"badge_labels": resolved_badge_labels}
    return {}


def _resolve_checklists(
    integration: dict[str, Any],
    full_context: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate presentation checklist items against the evaluation context."""
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
        return {"checklists": resolved_checklists}
    return {}


def _resolve_templates(
    integration: dict[str, Any],
    full_context: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate presentation template conditions and return resolved template entries."""
    template_defs = integration.get("templates", [])
    if not template_defs:
        return {}

    resolved_templates: list[dict[str, str]] = []
    for tmpl_def in template_defs:
        url = tmpl_def.get("url")
        package = tmpl_def.get("package")
        if not url and not package:
            continue

        label = url or package
        condition = tmpl_def.get("condition")
        if condition:
            result = evaluate_condition(condition, full_context, label=label)
            if result is None:
                pass  # no condition → include
            elif not result.passed or result.incomplete:
                continue

        resolved_tmpl: dict[str, str] = {}
        if url:
            resolved_tmpl["url"] = url
        if package:
            resolved_tmpl["package"] = package
        if tmpl_def.get("directory"):
            resolved_tmpl["directory"] = tmpl_def["directory"]
        resolved_templates.append(resolved_tmpl)

    if resolved_templates:
        return {"templates": resolved_templates}
    return {}


def resolve_presentation(
    playbook: dict[str, Any],
    full_context: dict[str, Any],
) -> dict[str, Any]:
    """Resolve all presentation directives (badges, checklists, templates).

    Reads the normalized flat ``playbook["presentation"]`` (the loader projects
    ``spec.presentation`` onto the top level). Returns a dict merged into the
    evaluation result by the orchestrator.
    """
    presentation = playbook.get("presentation", {})
    result: dict[str, Any] = {}
    result.update(_resolve_badge_labels(presentation, full_context))
    result.update(_resolve_checklists(presentation, full_context))
    result.update(_resolve_templates(presentation, full_context))

    return result
