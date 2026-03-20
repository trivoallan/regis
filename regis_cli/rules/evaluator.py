"""Rules evaluation engine."""

from __future__ import annotations

import logging
import re
from typing import Any

import json_logic
from json_logic import jsonLogic

from regis_cli.playbook.context import MissingDataTracker, _build_context

logger = logging.getLogger(__name__)

# Pattern for interpolating ${path.to.var}
_INTERPOLATION_RE = re.compile(r"\$\{([^}]+)\}")


def _interpolate_string(template: str, context: dict[str, Any]) -> str:
    """Interpolate ${vars} in a string using the context."""
    if not template:
        return template

    def _repl(match: re.Match[str]) -> str:
        var_path = match.group(1).strip()
        # Find in context (can be flat key or nested)
        if var_path in context:
            return str(context[var_path])
        parts = var_path.split(".")
        curr: Any = context
        for part in parts:
            if isinstance(curr, dict) and part in curr:
                curr = curr[part]
            elif isinstance(curr, list):
                if part == "length":
                    curr = len(curr)
                else:
                    try:
                        idx = int(part)
                        curr = curr[idx]
                    except (ValueError, IndexError):
                        return match.group(0)
            else:
                return match.group(0)  # leave unresolved
        return str(curr)

    return _INTERPOLATION_RE.sub(_repl, template)


def get_default_rules(analyzers_present: list[str]) -> list[dict[str, Any]]:
    """Gather default rules from analyzers present in the report."""
    from regis_cli.cli import _discover_analyzers

    analyzers = _discover_analyzers()
    default_rules = []

    # Add core rules manually
    default_rules.append(
        {
            "slug": "core.registry-domain-whitelist",
            "provider": "core",
            "description": "Checks if requested image registry domain is in the domains list.",
            "level": "critical",
            "tags": ["security"],
            "params": {
                "domains": ["docker.io", "registry-1.docker.io", "quay.io", "ghcr.io"]
            },
            "condition": {
                "in": [
                    {"var": "request.registry"},
                    {"var": "rule.params.domains"},
                ]
            },
            "messages": {
                "pass": "Image registry domain '${request.registry}' is in the domains list.",  # nosec B105
                "fail": "Image registry domain '${request.registry}' is not in the domains list.",
            },
        }
    )

    for name in analyzers_present:
        if name in analyzers:
            cls = analyzers[name]
            rules = cls.default_rules()
            for rule in rules:
                rule["provider"] = name
            default_rules.extend(rules)

    return default_rules


def merge_rules(
    default_rules: list[dict[str, Any]], custom_rules: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Merge custom rules over default rules based on 'slug'. Deeply merges nested dicts."""
    merged = {}
    for rule in default_rules:
        slug = rule.get("slug")
        if slug:
            merged[slug] = rule
        else:
            merged[str(id(rule))] = rule

    for rule in custom_rules:
        slug = rule.get("slug")
        key = slug if slug else str(id(rule))

        if key in merged:
            # Specifically merge 'messages' which is a nested dict
            base_rule = merged[key]
            override_rule = dict(rule)

            if "messages" in override_rule and "messages" in base_rule:
                merged_msg = dict(base_rule["messages"])
                merged_msg.update(override_rule["messages"])
                override_rule["messages"] = merged_msg

            if "params" in override_rule and "params" in base_rule:
                merged_params = dict(base_rule["params"])
                merged_params.update(override_rule["params"])
                override_rule["params"] = merged_params

            merged[key] = {**base_rule, **override_rule}
        else:
            merged[key] = rule

    return list(merged.values())


def _add_custom_operations():
    """Add custom regis-specific operations to jsonLogic."""
    # intersects: any element of a is in b
    # Usage: {"intersects": [["val1", "val2"], ["val2", "val3"]]} -> True
    json_logic.add_operation(
        "intersects",
        lambda a, b: (
            any(x in b for x in a)
            if isinstance(a, list) and isinstance(b, list)
            else False
        ),
    )

    # contains_all: all elements of b are in a
    # Usage: {"contains_all": [["val1", "val2", "val3"], ["val1", "val2"]]} -> True
    json_logic.add_operation(
        "contains_all",
        lambda a, b: (
            all(x in a for x in b)
            if isinstance(a, list) and isinstance(b, list)
            else False
        ),
    )

    # subset: all elements of a are in b
    # Usage: {"subset": [["val1", "val2"], ["val1", "val2", "val3"]]} -> True
    json_logic.add_operation(
        "subset",
        lambda a, b: (
            all(x in b for x in a)
            if isinstance(a, list) and isinstance(b, list)
            else False
        ),
    )

    # keys: get keys of a dictionary
    # Usage: {"keys": [{"var": "labels"}]} -> ["key1", "key2"]
    json_logic.add_operation(
        "keys", lambda a: list(a.keys()) if isinstance(a, dict) else []
    )

    # env_contains: any string in b is a substring of any string in a
    # Usage: {"env_contains": [{"var": "results.skopeo.platforms.0.env"}, ["DEBUG", "SECRET"]]}
    json_logic.add_operation(
        "env_contains",
        lambda a, b: (
            any(any(sub in s for s in a) for sub in b)
            if isinstance(a, list) and isinstance(b, list)
            else False
        ),
    )


_add_custom_operations()


def evaluate_rules(
    report: dict[str, Any], rules_def: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Evaluate a set of rules against the analysis report.

    Args:
        report: The analysis report dict.
        rules_def: Optional parsed rules.yaml.
    """
    flat_context, _ = _build_context(report)

    request_info = report.get("request", {})
    analyzers_present = request_info.get("analyzers", [])

    defaults = get_default_rules(analyzers_present)

    custom = []
    if rules_def and isinstance(rules_def.get("rules"), list):
        custom = rules_def["rules"]

    final_rules = merge_rules(defaults, custom)

    results = []

    # Filter out disabled rules first
    enabled_rules = [r for r in final_rules if r.get("enable", True)]

    for rule in enabled_rules:
        # Inject the current rule into the flattened context
        # This makes it accessible via e.g. {"var": "rule.params.max_days"}
        flat_context["rule"] = rule

        condition = rule.get("condition", {})
        tracker = MissingDataTracker(flat_context)
        try:
            passed = bool(jsonLogic(condition, tracker))
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Rule '%s' evaluation error: %s", rule.get("slug", "unknown"), exc
            )
            passed = False

        status = (
            "incomplete"
            if tracker.missing_accessed
            else ("passed" if passed else "failed")
        )

        messages = rule.get("messages", {})
        message_tmpl = messages.get("pass" if passed else "fail", "")
        message_resolved = _interpolate_string(message_tmpl, flat_context)

        involved_analyzers = set()
        for key in tracker.accessed_keys:
            if key.startswith("results."):
                parts = key.split(".")
                if len(parts) > 1:
                    involved_analyzers.add(parts[1])

        results.append(
            {
                "slug": rule.get("slug", ""),
                "description": rule.get("description", ""),
                "level": rule.get("level", "info"),
                "tags": rule.get("tags", []),
                "passed": passed,
                "status": status,
                "message": message_resolved,
                "analyzers": sorted(involved_analyzers),
            }
        )

    # Sort results to be deterministic: failures first over passes, then by level, then slug
    # Levels ordered by severity
    level_order = {"critical": 1, "warning": 2, "info": 3, "none": 4}

    results.sort(
        key=lambda r: (
            not r["passed"],
            level_order.get(str(r["level"]).lower(), 99),
            r["slug"],
        )
    )

    all_rule_slugs = [r["slug"] for r in results]
    passed_rule_slugs = [r["slug"] for r in results if r["passed"]]

    # Group by tag
    by_tag: dict[str, dict[str, Any]] = {}
    for r in results:
        for tag in r.get("tags", []):
            if tag not in by_tag:
                by_tag[tag] = {"rules": [], "passed_rules": [], "score": 0}

            # Use explicit cast or type checking for mypy
            rules_list = by_tag[tag]["rules"]
            passed_list = by_tag[tag]["passed_rules"]

            if isinstance(rules_list, list):
                rules_list.append(r["slug"])
            if r["passed"] and isinstance(passed_list, list):
                passed_list.append(r["slug"])

    for tag_stats in by_tag.values():
        t_rules = tag_stats.get("rules", [])
        t_passed = tag_stats.get("passed_rules", [])
        if isinstance(t_rules, list) and isinstance(t_passed, list):
            n_total = len(t_rules)
            n_passed = len(t_passed)
            if n_total > 0:
                tag_stats["score"] = round(n_passed / n_total * 100)

    return {
        "score": (
            round(len(passed_rule_slugs) / len(all_rule_slugs) * 100)
            if all_rule_slugs
            else 0
        ),
        "all_rules": all_rule_slugs,
        "passed_rules": passed_rule_slugs,
        "by_tag": by_tag,
        "rules": results,
    }
