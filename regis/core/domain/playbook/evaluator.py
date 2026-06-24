"""Playbook evaluation orchestrator.

The ``evaluate`` function is the main entry point. It:
1. Builds the evaluation context from the analysis report.
2. Evaluates the playbook's declared rules.
3. Assembles the result dict.
4. Resolves tiers, badges, links, and presentation directives.
"""

from __future__ import annotations

import logging
from typing import Any

from regis.core.domain.playbook.context import NamedList
from regis.core.domain.playbook.presentation import resolve_presentation
from regis.core.domain.playbook.templates import _resolve_template
from regis.core.domain.rules.evaluator import evaluate_rules

logger = logging.getLogger(__name__)


def _resolve_links(
    playbook: dict[str, Any],
    result: dict[str, Any],
    full_context: dict[str, Any],
    report: dict[str, Any],
) -> None:
    """Resolve playbook-level links and attach them to *result*."""
    resolved_links = []
    for link_def in playbook.get("links", []):
        if not isinstance(link_def, dict):
            continue

        condition = link_def.get("condition")
        if condition:
            try:
                from json_logic import jsonLogic

                if not jsonLogic(condition, full_context):
                    continue
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to evaluate link condition for '%s': %s",
                    link_def.get("label"),
                    exc,
                )
                continue

        url_tmpl = link_def.get("url")
        if not isinstance(url_tmpl, str):
            continue

        try:
            if "{{" in url_tmpl or "{%" in url_tmpl:
                url = _resolve_template(
                    url_tmpl, full_context, nested_context=full_context
                )
            else:
                url = url_tmpl.format(**report)

            if url:
                resolved_links.append({"label": link_def.get("label", ""), "url": url})
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Could not resolve link '%s': %s", link_def.get("label"), exc
            )

    if resolved_links:
        result["links"] = resolved_links


def evaluate(
    playbook: dict[str, Any],
    report: dict[str, Any],
    source_name: str | None = None,
) -> dict[str, Any]:
    """Evaluate a playbook against an analysis report.

    Returns a result dict with:
    - ``playbook_name``  — name of the playbook
    - ``rules``          — per-rule evaluation results
    - ``score``          — overall percentage of rules passed (0–100)
    """
    # 0. Evaluate the playbook's declared rules (resolved against the criterion catalogue)
    rules_results = evaluate_rules(report, playbook)

    # Inject rule results into the report so they are available in context (via dots)
    # NamedList allows lookup by slug (e.g. rules.cve-no-critical.passed)
    report["rules"] = NamedList(rules_results["rules"])
    report["rules_summary"] = {
        "score": rules_results["score"],
        "total": rules_results["all_rules"],
        "passed": rules_results["passed_rules"],
        "by_tag": rules_results["by_tag"],
    }

    result: dict[str, Any] = {
        "playbook_name": playbook.get("name", "unnamed"),
        "playbook_version": playbook.get("version"),
        "api_version": playbook.get("apiVersion"),
        "score": rules_results["score"],
        "rules": report["rules"],
        "rules_summary": report["rules_summary"],
        "slug": playbook.get("slug"),
        "ruleset_hash": rules_results["ruleset_hash"],
    }

    # Build the full context that includes the evaluation result itself (for badges
    # and links that reference playbook-level scores).
    full_context: dict[str, Any] = {
        **report,
        **result,
        "playbook": result,
        "playbooks": [result],
        "score": result.get("score", 0),
    }

    # Resolve tiers
    tiers = playbook.get("tiers", [])
    if tiers:
        from json_logic import jsonLogic

        for tier in tiers:
            condition = tier.get("condition")
            if condition:
                try:
                    if jsonLogic(condition, full_context):
                        result["tier"] = tier.get("name")
                        result["tier_icon"] = tier.get("icon")
                        break
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Tier condition evaluation failed: %s", exc)

    # Resolve badges
    badges = playbook.get("badges", [])
    if badges:
        resolved_badges = []
        import re

        from json_logic import jsonLogic

        from regis.core.domain.playbook.templates import _resolve_path

        # Regex for ${var.path} interpolation
        interp_re = re.compile(r"\$\{([^}]+)\}")

        def interpolate(tmpl: str, ctx: dict[str, Any]) -> str:
            def _repl(m: re.Match[str]) -> str:
                path = m.group(1).strip()
                val = _resolve_path(path, ctx)
                return str(val) if val is not None else m.group(0)

            return interp_re.sub(_repl, tmpl)

        for badge_def in badges:
            condition = badge_def.get("condition")
            if condition:
                try:
                    if not jsonLogic(condition, full_context):
                        continue
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Badge condition evaluation failed: %s", exc)
                    continue

            scope = badge_def.get("scope", "")
            value_tmpl = badge_def.get("value")
            resolved_value = (
                interpolate(value_tmpl, full_context) if value_tmpl else None
            )

            badge_res = {
                "slug": badge_def.get("slug"),
                "scope": scope,
                "value": resolved_value,
                "class": badge_def.get("class", "information"),
            }
            if badge_res["value"]:
                badge_res["label"] = f"{scope}: {badge_res['value']}"
            else:
                badge_res["label"] = scope

            resolved_badges.append(badge_res)
        result["badges"] = resolved_badges

    # Resolve sidebar, links, and presentation directives
    sidebar = playbook.get("sidebar")
    if sidebar:
        result["sidebar"] = sidebar

    _resolve_links(playbook, result, full_context, report)
    result.update(resolve_presentation(playbook, full_context))

    if source_name:
        result["_meta"] = {"source_name": source_name}

    return result
