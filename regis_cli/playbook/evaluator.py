"""Playbook evaluation orchestrator.

The ``evaluate`` function is the main entry point. It:
1. Builds the evaluation context from the analysis report.
2. Evaluates each page and section (scorecards, widgets).
3. Assembles the result dict.
4. Performs a final widget resolution pass using the full context.
5. Resolves playbook-level links and GitLab integration directives.
"""

from __future__ import annotations

import logging
from typing import Any

from regis_cli.playbook.context import NamedList, _build_context
from regis_cli.playbook.integrations.gitlab import resolve_gitlab_integration
from regis_cli.playbook.sections import _evaluate_section, resolve_widgets_final
from regis_cli.playbook.templates import _resolve_template
from regis_cli.rules.evaluator import evaluate_rules

logger = logging.getLogger(__name__)


def _normalize_pages(playbook: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the pages list, wrapping bare ``sections`` in a default page.

    Playbooks that rely solely on ``rules`` may omit both ``pages`` and
    ``sections``; in that case an empty list is returned and page evaluation
    is skipped.
    """
    pages_defs = playbook.get("pages")
    sections_defs = playbook.get("sections")

    if not pages_defs and not sections_defs:
        return []

    if not pages_defs:
        return [{"name": "Default", "sections": sections_defs}]
    return pages_defs


def _evaluate_pages(
    pages_defs: list[dict[str, Any]],
    raw_context: dict[str, Any],
    nested_context: dict[str, Any],
) -> tuple[list[dict[str, Any]], int, int]:
    """Evaluate all pages and sections.

    Returns:
        (pages_results, total_scorecards, total_passed)
    """
    from json_logic import jsonLogic

    pages_results: list[dict[str, Any]] = []
    total_scorecards_all = 0
    total_passed_all = 0

    for page_def in pages_defs:
        page_sections_defs = page_def.get("sections", [])
        page_sections_results = []
        page_total_scorecards = 0
        page_passed_scorecards = 0

        for section_def in page_sections_defs:
            condition = section_def.get("condition")
            if condition:
                from regis_cli.playbook.context import MissingDataTracker

                tracker = MissingDataTracker(raw_context)
                try:
                    is_active = jsonLogic(condition, tracker)
                    if not is_active and not tracker.missing_accessed:
                        continue
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Section '%s' condition evaluation error: %s",
                        section_def.get("name", "unknown"),
                        exc,
                    )
                    if not tracker.missing_accessed:
                        continue

            section_result = _evaluate_section(
                section_def,
                raw_context,
                nested_context=nested_context,
            )
            page_sections_results.append(section_result)
            page_total_scorecards += section_result["total_scorecards"]
            page_passed_scorecards += section_result["passed_scorecards"]

        pages_results.append(
            {
                "title": page_def.get("title", "Default"),
                "slug": page_def.get("slug"),
                "score": (
                    round(page_passed_scorecards / page_total_scorecards * 100)
                    if page_total_scorecards
                    else 0
                ),
                "total_scorecards": page_total_scorecards,
                "passed_scorecards": page_passed_scorecards,
                "sections": NamedList(page_sections_results),
            }
        )
        total_scorecards_all += page_total_scorecards
        total_passed_all += page_passed_scorecards

    return pages_results, total_scorecards_all, total_passed_all


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
    - ``sections``       — per-section breakdown (scorecards, levels, display, widgets)
    - ``score``          — overall percentage of scorecards passed (0–100)
    """
    # 0. Evaluate rules (merges analyzer defaults with playbook 'rules' section)
    rules_results = evaluate_rules(report, playbook)

    # Inject rule results into the report so they are available in context (via dots)
    # NamedList allows lookup by slug (e.g. rules.trivy-no-critical.passed)
    report["rules"] = NamedList(rules_results["rules"])
    report["rules_summary"] = {
        "score": rules_results["score"],
        "total": rules_results["all_rules"],
        "passed": rules_results["passed_rules"],
        "by_tag": rules_results["by_tag"],
    }

    raw_context, nested_context = _build_context(report)
    pages_defs = _normalize_pages(playbook)
    pages_results, total_scorecards_all, total_passed_all = _evaluate_pages(
        pages_defs, raw_context, nested_context
    )

    result: dict[str, Any] = {
        "playbook_name": playbook.get("name", "unnamed"),
        "score": (
            round(total_passed_all / total_scorecards_all * 100)
            if total_scorecards_all
            else 0
        ),
        "total_scorecards": total_scorecards_all,
        "passed_scorecards": total_passed_all,
        "pages": NamedList(pages_results),
        "rules": report["rules"],
        "rules_summary": report["rules_summary"],
        "slug": playbook.get("slug"),
    }

    # Build the full context that includes the evaluation result itself (for widgets
    # and links that reference playbook-level scores, pages, etc.)
    full_context: dict[str, Any] = {
        **report,
        **result,
        "playbook": result,
        "playbooks": [result],
        "score": result.get("score", 0),
    }

    # Final widget resolution pass (filters conditions, re-resolves playbook-aware paths)
    resolve_widgets_final(result["pages"], full_context)

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
                        break
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Tier condition evaluation failed: %s", exc)

    # Resolve badges
    badges = playbook.get("badges", [])
    if badges:
        resolved_badges = []
        import re

        from json_logic import jsonLogic

        from regis_cli.playbook.templates import _resolve_path

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

    # Resolve sidebar, links, and GitLab integration
    sidebar = playbook.get("sidebar")
    if sidebar:
        result["sidebar"] = sidebar

    _resolve_links(playbook, result, full_context, report)
    result.update(resolve_gitlab_integration(playbook, full_context))

    if source_name:
        result["_meta"] = {"source_name": source_name}

    return result
