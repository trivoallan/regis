"""Playbook evaluation engine.

Loads playbook definitions (YAML/JSON) containing scorecards with JsonLogic
conditions and evaluates them against a regis-cli analysis report.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yaml
from jinja2 import BaseLoader, ChainableUndefined, Environment
from json_logic import jsonLogic

logger = logging.getLogger(__name__)

# Ordered from lowest to highest.
_LEVEL_ORDER = {"bronze": 1, "silver": 2, "gold": 3}


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


_WIDGET_ENV = Environment(
    loader=BaseLoader(), undefined=ChainableUndefined, autoescape=True
)
_WIDGET_ENV.filters["format_date"] = _format_date
_WIDGET_ENV.filters["format_datetime"] = _format_datetime
_WIDGET_ENV.filters["format_time"] = _format_time


def _resolve_template(
    template_str: Any, context: dict[str, Any], nested_context: dict[str, Any] = None
) -> Any:
    """Evaluate a string strictly as a Jinja2 template."""
    if not isinstance(template_str, str):
        return template_str
    try:
        render_ctx = nested_context if nested_context is not None else context
        template = _WIDGET_ENV.from_string(template_str)
        return template.render(**render_ctx)
    except Exception as exc:
        logger.debug("Failed to resolve Jinja2 template '%s': %s", template_str, exc)
        return template_str


def _resolve_path(
    path: Any, context: dict[str, Any], nested_context: dict[str, Any] = None
) -> Any:
    """Resolve a dot-separated path in a nested context.
    Supports list indexing with integers (e.g. 'playbooks.0.score').
    """
    if not isinstance(path, str):
        return path

    # If it contains | or is wrapped in {{ }}, use Jinja2
    if "|" in path or ("{{" in path and "}}" in path):
        try:
            # Use nested_context for Jinja2 if available, fallback to context
            render_ctx = nested_context if nested_context is not None else context
            template = _WIDGET_ENV.from_string(path)
            return template.render(**render_ctx)
        except Exception as exc:
            logger.debug("Failed to resolve Jinja2 path '%s': %s", path, exc)
            return path

    # Basic cleanup if user used Jinja-like braces or bracket indexing
    clean_path = path.strip("{} ").replace("[", ".").replace("]", "")

    parts = clean_path.split(".")
    val = context
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


def _flatten(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten a nested dict into dot-separated keys.

    Example::

        {"results": {"tags": {"total_tags": 42}}}
        → {"results.tags.total_tags": 42}
    """
    flat: dict[str, Any] = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(_flatten(value, full_key))
        else:
            flat[full_key] = value
    return flat


class NamedList(list):
    """A list wrapper that allows item access by index, slug, or normalized name."""

    def __init__(self, data: list[Any]):
        super().__init__(data)
        self._keys: dict[str, Any] = {}
        for item in data:
            if isinstance(item, dict):
                if "slug" in item:
                    self._keys[item["slug"]] = item
                if "name" in item:
                    # Create a normalized name: lowercase, replace spaces/dashes with underscores
                    norm = item["name"].lower().replace(" ", "_").replace("-", "_")
                    self._keys[norm] = item

    def __getitem__(self, key: Any) -> Any:
        # Standard integer index access
        if isinstance(key, int):
            return super().__getitem__(key)

        # String-based access
        if isinstance(key, str):
            # Try interpreting as index first
            try:
                idx = int(key)
                return super().__getitem__(idx)
            except ValueError:
                pass

            # Lookup by slug or normalized name
            if key in self._keys:
                return self._keys[key]

        return super().__getitem__(key)


def load_playbook(path: str | Path) -> dict[str, Any]:
    """Load a playbook definition from a local file or remote URL."""
    if isinstance(path, str) and (
        path.startswith("http://") or path.startswith("https://")
    ):
        import requests

        try:
            response = requests.get(path, timeout=30)
            response.raise_for_status()
            text = response.text
            # Infer format from URL or try YAML (which is a superset of JSON)
            if path.lower().endswith(".json"):
                return json.loads(text)
            return yaml.safe_load(text)
        except Exception as exc:
            raise ValueError(f"Failed to download playbook from {path}: {exc}") from exc

    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(text)
    return json.loads(text)


class MissingDataTracker(dict):
    """A dictionary wrapper that tracks which keys were accessed and if they were missing."""

    def __init__(
        self,
        data: dict[str, Any],
        path: str = "",
        root_tracker: MissingDataTracker | None = None,
    ):
        super().__init__(data)
        self.missing_accessed = False
        self.path = path
        # If this is a nested tracker, use the root tracker's accessed_keys set
        if root_tracker:
            self.root = root_tracker
            self.accessed_keys = root_tracker.accessed_keys
        else:
            self.root = self
            self.accessed_keys: set[str] = set()

    def __getitem__(self, key: str) -> Any:
        full_key = f"{self.path}.{key}" if self.path else key
        self.accessed_keys.add(full_key)
        try:
            val = super().__getitem__(key)
        except KeyError:
            self.root.missing_accessed = True
            raise

        if val is None:
            self.root.missing_accessed = True
            return None

        if isinstance(val, dict):
            return MissingDataTracker(val, full_key, self.root)
        return val

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key: object) -> bool:
        if isinstance(key, str):
            full_key = f"{self.path}.{key}" if self.path else key
            self.accessed_keys.add(full_key)
        if not super().__contains__(key):
            self.root.missing_accessed = True
            return False
        return True


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


def _evaluate_section(
    section: dict[str, Any],
    raw_context: dict[str, Any],
    nested_context: dict[str, Any] = None,
) -> dict[str, Any]:
    """Evaluate a single playbook section against an already-flattened report context.

    Returns a result dict for the section with scorecards, levels_summary, display, etc.
    """
    scorecards_defs = section.get("scorecards", [])

    scorecard_results: list[dict[str, Any]] = []
    for scorecard in scorecards_defs:
        condition = scorecard.get("condition", {})
        tracker = MissingDataTracker(raw_context)
        try:
            result = jsonLogic(condition, tracker)
            passed = bool(result)
            incomplete = tracker.missing_accessed
        except Exception as exc:
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

    # Determine summary by level.
    levels_defined = {
        lv["name"]: lv.get("order", _LEVEL_ORDER.get(lv["name"], 0))
        for lv in section.get("levels", [])
    }

    levels_summary = {}
    for level_name in sorted(levels_defined, key=lambda n: levels_defined[n]):
        level_scorecards = [r for r in scorecard_results if r["level"] == level_name]
        if level_scorecards:
            passed_level = sum(1 for r in level_scorecards if r["passed"])
            levels_summary[level_name] = {
                "total": len(level_scorecards),
                "passed": passed_level,
                "percentage": round(passed_level / len(level_scorecards) * 100),
            }

    tags_defined = set()
    for r in scorecard_results:
        for t in r.get("tags", []):
            tags_defined.add(t)

    tags_summary = {}
    for tag_name in sorted(tags_defined):
        tag_scorecards = [r for r in scorecard_results if tag_name in r.get("tags", [])]
        if tag_scorecards:
            passed_tag = sum(1 for r in tag_scorecards if r["passed"])
            tags_summary[tag_name] = {
                "total": len(tag_scorecards),
                "passed": passed_tag,
                "percentage": round(passed_tag / len(tag_scorecards) * 100),
            }

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

    # Resolve display preferences and widget values.
    display = section.get("display")
    if display:
        section_result["display"] = dict(display)

    raw_widgets = list(section.get("widgets", []))
    if display and "widgets" in display:
        raw_widgets.extend(display["widgets"])

    if raw_widgets:
        resolved_widgets = []
        for widget in raw_widgets:
            # Check condition early
            condition = widget.get("condition")
            if condition:
                tracker = MissingDataTracker(raw_context)
                try:
                    is_active = jsonLogic(condition, tracker)
                    if not is_active and not tracker.missing_accessed:
                        continue
                except Exception as exc:
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
        section_result["widgets"] = resolved_widgets

    # Build render_order from the YAML key order.
    # Python 3.7+ dicts preserve insertion order, so iterating
    # over the section dict reflects the original YAML order.
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

    section_result["render_order"] = render_order

    return section_result


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
    # Build data context.
    raw_context = _flatten(report)
    raw_context.update(report)

    pages_defs = playbook.get("pages")
    sections_defs = playbook.get("sections")

    if not pages_defs and not sections_defs:
        raise ValueError(
            f"Playbook '{playbook.get('name', 'unnamed')}' is missing "
            "both 'pages' and 'sections'. Every playbook must define at least one."
        )

    if not pages_defs:
        # Implicitly wrap root sections in a single defaults page
        pages_defs = [{"name": "Default", "sections": sections_defs}]

    pages_results = []
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
                tracker = MissingDataTracker(raw_context)
                try:
                    is_active = jsonLogic(condition, tracker)
                    if not is_active and not tracker.missing_accessed:
                        continue
                except Exception as exc:
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
                nested_context=report,
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

    # Result object setup
    result = {
        "playbook_name": playbook.get("name", "unnamed"),
        "score": (
            round(total_passed_all / total_scorecards_all * 100)
            if total_scorecards_all
            else 0
        ),
        "total_scorecards": total_scorecards_all,
        "passed_scorecards": total_passed_all,
        "pages": NamedList(pages_results),
        "slug": playbook.get("slug"),
    }

    # Final pass to resolve widgets that might need the final score or result object
    # We build a 'full' context that includes the results of this playbook evaluation.
    full_context = {
        **report,
        **result,
        "playbook": result,
        "playbooks": [result],
        "score": result.get("score", 0),
    }
    for page in result["pages"]:
        filtered_sections = []
        for section in page["sections"]:
            condition = section.get("condition")
            if condition:
                try:
                    if not jsonLogic(condition, full_context):
                        continue
                except Exception:
                    continue

            filtered_widgets = []
            for widget in section.get("widgets", []):
                w_condition = widget.get("condition")
                if w_condition:
                    try:
                        if not jsonLogic(w_condition, full_context):
                            continue
                    except Exception:
                        continue

                # Only re-resolve if we didn't find a value in the first pass
                # OR if it starts with 'playbook' or 'page' or 'score'
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

                # Resolve subvalue as well
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

                # Final pass for URLs too
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

    sidebar = playbook.get("sidebar")
    if sidebar:
        result["sidebar"] = sidebar

    meta = {}
    if source_name:
        meta["source_name"] = source_name
    if meta:
        result["_meta"] = meta

    # Resolve format strings for any playbook-level links using the report context
    resolved_links = []
    for link_def in playbook.get("links", []):
        if not isinstance(link_def, dict):
            continue

        # Evaluate condition if present
        condition = link_def.get("condition")
        if condition:
            try:
                if not jsonLogic(condition, full_context):
                    continue
            except Exception as exc:
                logger.warning(
                    "Failed to evaluate link condition for '%s': %s",
                    link_def.get("label"),
                    exc,
                )
                continue

        url_tmpl = link_def.get("url")
        if not isinstance(url_tmpl, str):
            continue

        # Try to resolve as Jinja2 template (new) or fall back to old .format()
        try:
            if "{{" in url_tmpl or "{%" in url_tmpl:
                url = _resolve_template(
                    url_tmpl, full_context, nested_context=full_context
                )
            else:
                url = url_tmpl.format(**report)

            if url:
                resolved_links.append({"label": link_def.get("label", ""), "url": url})
        except Exception as e:
            logger.warning(
                "Could not resolve link '%s': %s",
                link_def.get("label"),
                e,
            )

    if resolved_links:
        result["links"] = resolved_links

    # Evaluate GitLab integration labels
    gitlab_integration = playbook.get("integrations", {}).get("gitlab", {})
    label_defs = gitlab_integration.get("labels", [])
    if label_defs:
        resolved_labels = []
        for label_def in label_defs:
            condition = label_def.get("condition")
            if condition:
                try:
                    # Use full_context which includes final score and result summary
                    if jsonLogic(condition, full_context):
                        resolved_labels.append(label_def["name"])
                except Exception as exc:
                    logger.warning(
                        "Failed to evaluate label condition for '%s': %s",
                        label_def.get("name"),
                        exc,
                    )
        result["labels"] = list(set(resolved_labels))

    # Evaluate GitLab MR description checklists
    checklist_defs = gitlab_integration.get("checklist")
    checklists_defs = gitlab_integration.get("checklists", [])

    # Backwards compatibility: wrap old `checklist` into the new `checklists` format
    if checklist_defs is not None and not checklists_defs:
        checklists_defs = [{"items": checklist_defs}]

    if checklists_defs:
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
                condition = item_def.get("show_if")
                if condition:
                    try:
                        tracker = MissingDataTracker(full_context)
                        is_active = jsonLogic(condition, tracker)
                        if not is_active or tracker.missing_accessed:
                            continue
                    except Exception as exc:
                        logger.warning(
                            "Failed to evaluate checklist condition for '%s': %s",
                            label,
                            exc,
                        )
                        continue

                # --- checked condition ---
                checked = False
                checked_condition = item_def.get("check_if")
                if checked_condition:
                    try:
                        tracker = MissingDataTracker(full_context)
                        checked = (
                            bool(jsonLogic(checked_condition, tracker))
                            and not tracker.missing_accessed
                        )
                    except Exception as exc:
                        logger.warning(
                            "Failed to evaluate checklist checked_condition for '%s': %s",
                            label,
                            exc,
                        )

                resolved_items.append({"label": label, "checked": checked})

            if resolved_items:
                resolved_checklists.append({"title": title, "items": resolved_items})

        if resolved_checklists:
            result["mr_description_checklists"] = resolved_checklists

    # Evaluate GitLab MR templates
    template_defs = gitlab_integration.get("templates", [])
    if template_defs:
        resolved_templates: list[dict[str, str]] = []
        for tmpl_def in template_defs:
            url = tmpl_def.get("url")
            if not url:
                continue

            # Evaluate condition if present
            condition = tmpl_def.get("condition")
            if condition:
                try:
                    tracker = MissingDataTracker(full_context)
                    is_active = jsonLogic(condition, tracker)
                    if not is_active or tracker.missing_accessed:
                        continue
                except Exception as exc:
                    logger.warning(
                        "Failed to evaluate template condition for '%s': %s",
                        url,
                        exc,
                    )
                    continue

            resolved_tmpl = {"url": url}
            if tmpl_def.get("directory"):
                resolved_tmpl["directory"] = tmpl_def["directory"]
            resolved_templates.append(resolved_tmpl)

        if resolved_templates:
            result["mr_templates"] = resolved_templates

    return result
