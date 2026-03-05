"""Section evaluation logic for the playbook engine.

Provides ``_evaluate_section``, which evaluates a single playbook section
against a flattened report context, producing scorecards, level/tag summaries,
widgets, and a render order list.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from regis_cli.playbook.conditions import _stringify_condition
from regis_cli.playbook.context import MissingDataTracker
from regis_cli.playbook.templates import _resolve_path, _resolve_template

logger = logging.getLogger(__name__)

# Ordered from lowest to highest.
_LEVEL_ORDER = {"bronze": 1, "silver": 2, "gold": 3}


def _evaluate_scorecards(
    scorecards_defs: list[dict[str, Any]],
    raw_context: dict[str, Any],
) -> list[dict[str, Any]]:
    """Evaluate each scorecard definition against the raw (flat) context."""
    scorecard_results: list[dict[str, Any]] = []
    for scorecard in scorecards_defs:
        condition = scorecard.get("condition", {})
        tracker = MissingDataTracker(raw_context)
        try:
            from json_logic import jsonLogic

            result = jsonLogic(condition, tracker)
            passed = bool(result)
            incomplete = tracker.missing_accessed
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Scorecard '%s' evaluation error: %s",
                scorecard.get("name"),
                exc,
            )
            passed = False
            incomplete = True

        status = "incomplete" if incomplete else ("passed" if passed else "failed")

        involved_analyzers = set()
        for key in tracker.accessed_keys:
            if key.startswith("results."):
                parts = key.split(".")
                if len(parts) > 1:
                    involved_analyzers.add(parts[1])

        scorecard_results.append(
            {
                "name": scorecard.get("name", ""),
                "title": scorecard.get("title", scorecard.get("name", "")),
                "level": scorecard.get("level"),
                "tags": scorecard.get("tags", []),
                "analyzers": sorted(involved_analyzers),
                "passed": passed,
                "status": status,
                "condition": json.dumps(condition),
                "details": _stringify_condition(condition, tracker),
            }
        )
    return scorecard_results


def _compute_levels_summary(
    scorecard_results: list[dict[str, Any]],
    levels: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a per-level pass/fail summary from evaluated scorecard results."""
    levels_defined = {
        lv["name"]: lv.get("order", _LEVEL_ORDER.get(lv["name"], 0)) for lv in levels
    }
    levels_summary: dict[str, Any] = {}
    for level_name in sorted(levels_defined, key=lambda n: levels_defined[n]):
        level_scorecards = [r for r in scorecard_results if r["level"] == level_name]
        if level_scorecards:
            passed_level = sum(1 for r in level_scorecards if r["passed"])
            levels_summary[level_name] = {
                "total": len(level_scorecards),
                "passed": passed_level,
                "percentage": round(passed_level / len(level_scorecards) * 100),
            }
    return levels_summary


def _compute_tags_summary(
    scorecard_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a per-tag pass/fail summary from evaluated scorecard results."""
    tags_defined: set[str] = set()
    for r in scorecard_results:
        for t in r.get("tags", []):
            tags_defined.add(t)

    tags_summary: dict[str, Any] = {}
    for tag_name in sorted(tags_defined):
        tag_scorecards = [r for r in scorecard_results if tag_name in r.get("tags", [])]
        if tag_scorecards:
            passed_tag = sum(1 for r in tag_scorecards if r["passed"])
            tags_summary[tag_name] = {
                "total": len(tag_scorecards),
                "passed": passed_tag,
                "percentage": round(passed_tag / len(tag_scorecards) * 100),
            }
    return tags_summary


def _collect_raw_widgets(section: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect raw widget definitions from section and display.widgets."""
    raw_widgets = list(section.get("widgets", []))
    display = section.get("display")
    if display and "widgets" in display:
        raw_widgets.extend(display["widgets"])
    return raw_widgets


def _evaluate_widgets(
    raw_widgets: list[dict[str, Any]],
    raw_context: dict[str, Any],
    nested_context: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """First-pass widget resolution against raw_context (before full_context exists)."""
    resolved_widgets = []
    for widget in raw_widgets:
        # Check condition early
        condition = widget.get("condition")
        if condition:
            tracker = MissingDataTracker(raw_context)
            try:
                from json_logic import jsonLogic

                is_active = jsonLogic(condition, tracker)
                if not is_active and not tracker.missing_accessed:
                    continue
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Widget '%s' condition evaluation error: %s",
                    widget.get("label", widget.get("template", "unknown")),
                    exc,
                )
                if not tracker.missing_accessed:
                    continue

        resolved = dict(widget)
        value_path = widget.get("value")
        if value_path:
            resolved["resolved_value"] = _resolve_path(
                value_path, raw_context, nested_context
            )

        # Support for optional subvalue in options
        subvalue_path = widget.get("options", {}).get("subvalue")
        if subvalue_path:
            resolved["resolved_subvalue"] = _resolve_path(
                subvalue_path, raw_context, nested_context
            )

        # Support for optional links on widgets
        url_tmpl = widget.get("url")
        if url_tmpl:
            resolved["resolved_url"] = _resolve_template(
                url_tmpl, raw_context, nested_context
            )

        resolved_widgets.append(resolved)
    return resolved_widgets


def _build_render_order(
    section: dict[str, Any],
    tags_summary: dict[str, Any],
) -> list[str]:
    """Build render_order from YAML key order (Python 3.7+ dict preserves insertion order)."""
    render_order: list[str] = []
    for key in section:
        if key == "display":
            display_def = section.get("display", {})
            for display_key in display_def:
                if display_key in ("analyzers", "widgets"):
                    if display_key not in render_order:
                        render_order.append(display_key)
        elif key in ("levels", "scorecards", "widgets"):
            if key not in render_order:
                render_order.append(key)

    if tags_summary and "scorecards" in render_order:
        idx = render_order.index("scorecards")
        render_order.insert(idx, "tags")
    elif tags_summary and "tags" not in render_order:
        render_order.append("tags")

    return render_order


def _evaluate_section(
    section: dict[str, Any],
    raw_context: dict[str, Any],
    nested_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate a single playbook section against an already-flattened report context.

    Returns a result dict for the section with scorecards, levels_summary, display, etc.
    """
    scorecard_results = _evaluate_scorecards(section.get("scorecards", []), raw_context)
    levels_summary = _compute_levels_summary(
        scorecard_results, section.get("levels", [])
    )
    tags_summary = _compute_tags_summary(scorecard_results)

    passed_count = sum(1 for r in scorecard_results if r["passed"])
    total = len(scorecard_results)

    section_result: dict[str, Any] = {
        "name": section.get("name", ""),
        "score": round(passed_count / total * 100) if total else 0,
        "total_scorecards": total,
        "passed_scorecards": passed_count,
        "levels_summary": levels_summary,
        "tags_summary": tags_summary,
        "scorecards": scorecard_results,
    }
    if "hint" in section:
        section_result["hint"] = section["hint"]
    if "condition" in section:
        section_result["condition"] = section["condition"]

    # Resolve display preferences
    display = section.get("display")
    if display:
        section_result["display"] = dict(display)

    # First-pass widget resolution (raw_context only; full_context pass deferred to evaluator)
    raw_widgets = _collect_raw_widgets(section)
    if raw_widgets:
        section_result["widgets"] = _evaluate_widgets(
            raw_widgets, raw_context, nested_context
        )

    section_result["render_order"] = _build_render_order(section, tags_summary)

    return section_result


def resolve_widgets_final(
    pages: list[dict[str, Any]],
    full_context: dict[str, Any],
) -> None:
    """Second (and final) pass: re-resolve widget values using the full evaluation context.

    This pass also re-evaluates widget conditions and filters out inactive widgets.
    Mutates ``pages`` in-place.
    """
    from json_logic import jsonLogic

    for page in pages:
        filtered_sections = []
        for section in page["sections"]:
            # Re-check section condition against full_context
            condition = section.get("condition")
            if condition:
                try:
                    if not jsonLogic(condition, full_context):
                        continue
                except Exception:  # noqa: BLE001
                    continue

            filtered_widgets = []
            for widget in section.get("widgets", []):
                w_condition = widget.get("condition")
                if w_condition:
                    try:
                        if not jsonLogic(w_condition, full_context):
                            continue
                    except Exception:  # noqa: BLE001
                        continue

                # Re-resolve value if missing or if path references playbook-level data
                val_path = widget.get("value")
                if val_path and (
                    widget.get("resolved_value") is None
                    or any(
                        val_path.startswith(p)
                        for p in ["playbook", "score", "pages", "{{"]
                    )
                ):
                    widget["resolved_value"] = _resolve_path(
                        val_path, full_context, nested_context=full_context
                    )

                subvalue_path = widget.get("options", {}).get("subvalue")
                if subvalue_path and (
                    widget.get("resolved_subvalue") is None
                    or any(
                        subvalue_path.startswith(p)
                        for p in ["playbook", "score", "pages", "{{"]
                    )
                ):
                    widget["resolved_subvalue"] = _resolve_path(
                        subvalue_path, full_context, nested_context=full_context
                    )

                url_tmpl = widget.get("url")
                if url_tmpl and (
                    widget.get("resolved_url") is None
                    or any(
                        url_tmpl.startswith(p)
                        for p in ["playbook", "score", "pages", "{{"]
                    )
                ):
                    widget["resolved_url"] = _resolve_template(
                        url_tmpl, full_context, nested_context=full_context
                    )

                filtered_widgets.append(widget)

            section["widgets"] = filtered_widgets
            filtered_sections.append(section)

        page["sections"] = filtered_sections
