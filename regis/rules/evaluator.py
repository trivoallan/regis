"""Rules evaluation engine."""

from __future__ import annotations

import logging
import re
from typing import Any

import json_logic
from json_logic import jsonLogic

from regis.playbook.context import MissingDataTracker, _build_context

logger = logging.getLogger(__name__)

# Pattern for interpolating ${path.to.var}
# Uses [^${}]+ to match only innermost expressions (no nested braces/dollars),
# enabling multi-pass resolution of nested patterns like ${outer.${inner}}.
_INTERPOLATION_RE = re.compile(r"\$\{([^${}]+)\}")


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
                return "MISSING"
        return str(curr)

    # Multiple passes to handle nested interpolation like ${outer.${inner}}
    for _ in range(5):
        new_template = _INTERPOLATION_RE.sub(_repl, template)
        if new_template == template:
            break
        template = new_template
    return template


def get_default_rules(analyzers_present: list[str]) -> list[dict[str, Any]]:
    """Gather default rules from analyzers present in the report."""
    from regis.analyzers.discovery import discover_analyzers

    analyzers = discover_analyzers()
    default_rules = []

    # Add core rules manually
    default_rules.append(
        {
            "slug": "registry-domain-whitelist",
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
    """Merge custom rules over default rules. Supports slug-based overrides and template instantiation."""
    # Internal map keyed by (provider, slug)
    merged: dict[tuple[str, str], dict[str, Any]] = {}

    # 1. Map defaults by (provider, slug)
    for rule in default_rules:
        provider = rule.get("provider", "custom")
        slug = rule.get("slug", "unknown")
        merged[(provider, slug)] = rule.copy()

    # 2. Process custom rules
    processed_custom: list[dict[str, Any]] = []
    # Track template keys that are explicitly instantiated under a new slug so that
    # the original template entry can be removed from the final set (prevents duplicates).
    instantiated_template_keys: set[tuple[str, str]] = set()
    for rule_def in custom_rules:
        provider = rule_def.get("provider")
        template_name = rule_def.get("rule")
        options = rule_def.get("options", {})
        slug = rule_def.get("slug")

        # Case A: Instantiation (provider + rule)
        if provider and template_name:
            # Find the template in default_rules
            template = merged.get((provider, template_name))

            # Fallback for legacy full slugs or different provider naming
            if not template:
                for p_name in [provider, f"regis.analyzers.{provider}"]:
                    if (p_name, template_name) in merged:
                        template = merged[(p_name, template_name)]
                        break

            # Last resort: load template directly from the analyzer class (handles the
            # case where the analyzer was not run but a custom rule references its template)
            if not template:
                from regis.analyzers.discovery import discover_analyzers

                all_analyzers = discover_analyzers()
                prov_cls = all_analyzers.get(provider)
                if prov_cls:
                    for r in prov_cls.default_rules():
                        if r.get("slug") == template_name:
                            r_copy = r.copy()
                            r_copy["provider"] = provider
                            template = r_copy
                            break

            if template:
                # Create a new instance
                instance = dict(template)
                if options:
                    instance["params"] = {**instance.get("params", {}), **options}

                # If no slug provided, generate one
                if not slug:
                    # Provide a scoped slug for the instance
                    if "level" in options:
                        slug = f"{template_name}.{options['level']}"
                    else:
                        slug = f"{template_name}.{len(processed_custom)}"

                instance["slug"] = slug
                # Merge overrides from the custom rule definition itself
                overrides = {
                    k: v
                    for k, v in rule_def.items()
                    if k not in ("provider", "rule", "options", "slug")
                }
                instance.update(overrides)
                processed_custom.append(instance)
                # Mark the source template as consumed so it is not included twice
                # in the final rule set (the instance takes its place).
                instantiated_template_keys.add((provider, template_name))
            else:
                logger.warning(
                    "Rule template '%s' not found for provider '%s'",
                    template_name,
                    provider,
                )
                if slug:
                    # Normalize slug and provider so later loops don't get confused
                    rule_def["provider"] = provider
                    rule_def["slug"] = slug
                    processed_custom.append(rule_def)

        # Case B: Standard override or new rule
        else:
            rule_id = rule_def.get("rule") or rule_def.get("slug")
            if not rule_id:
                continue

            explicit_provider = rule_def.get("provider")
            if explicit_provider:
                custom_provider = explicit_provider
                rule_slug = rule_id
            elif "." in rule_id:
                custom_provider, rule_slug = rule_id.split(".", 1)
            else:
                custom_provider = "custom"
                rule_slug = rule_id

            rule_def["provider"] = custom_provider
            rule_def["slug"] = rule_slug
            processed_custom.append(rule_def)

    # 3. Merge processed custom rules into the final set
    # Final result is still a list of rules with their (provider, slug) identity
    final_dict: dict[tuple[str, str], dict[str, Any]] = {}
    # Re-initialize with defaults, skipping templates that were explicitly
    # instantiated under a new slug by a custom rule (avoids duplicates).
    for k, v in merged.items():
        if k not in instantiated_template_keys:
            final_dict[k] = v

    for rule in processed_custom:
        # Provider and slug are now properly formatted thanks to previous loop
        provider = rule.get("provider", "custom")
        slug = rule.get("slug")
        if not slug:
            # Should not happen for processed rules but as fallback
            slug = str(id(rule))

        key = (provider, slug)

        if key in final_dict:
            base_rule = final_dict[key]
            override_rule = dict(rule)

            if "messages" in override_rule and "messages" in base_rule:
                merged_msg = dict(base_rule["messages"])
                merged_msg.update(override_rule["messages"])
                override_rule["messages"] = merged_msg

            if "params" in override_rule and "params" in base_rule:
                merged_params = dict(base_rule["params"])
                merged_params.update(override_rule["params"])
                override_rule["params"] = merged_params

            final_dict[key] = {**base_rule, **override_rule}
        else:
            final_dict[key] = rule

    return list(final_dict.values())


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

    # get: get a value from a dictionary by key
    # Usage: {"get": [{"var": "results.trivy"}, "critical_count"]}
    json_logic.add_operation(
        "get",
        lambda data, key: data.get(key) if isinstance(data, dict) else None,
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
