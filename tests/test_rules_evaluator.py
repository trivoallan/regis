"""Tests for rules evaluator."""

import pytest

from regis.rules.evaluator import (
    evaluate_rules,
    get_criterion_templates,
    resolve_rules,
)


def test_get_criterion_templates():
    rules = get_criterion_templates(["oci", "freshness"])
    slugs = [r.get("slug") for r in rules]
    assert "registry-domain-whitelist" in slugs
    assert "user-blacklist" in slugs
    assert "age" in slugs


def test_resolve_rules_instantiates_template():
    templates = [
        {
            "provider": "freshness",
            "slug": "age",
            "description": "Age check",
            "params": {"max_days": 30},
            "condition": {"<": [{"var": "results.freshness.age_days"}, 30]},
            "messages": {"pass": "fresh", "fail": "stale"},
        }
    ]
    declared = [
        {
            "provider": "freshness",
            "criterion": "age",
            "slug": "age",
            "options": {"max_days": 7},
        }
    ]
    resolved = resolve_rules(templates, declared)
    assert len(resolved) == 1
    assert resolved[0]["slug"] == "age"
    # Option override merged onto the template params.
    assert resolved[0]["params"]["max_days"] == 7
    # Template message preserved.
    assert resolved[0]["messages"]["pass"] == "fresh"


def test_resolve_rules_drops_unreferenced_templates():
    templates = [
        {"provider": "oci", "slug": "max-size", "condition": {"==": [1, 1]}},
    ]
    # Nothing declared -> nothing resolved.
    assert resolve_rules(templates, []) == []


def test_evaluate_rules():
    report = {
        "request": {"registry": "docker.io", "analyzers": ["freshness"]},
        "results": {"freshness": {"age_days": 10}},
    }
    rules_def = {
        "rules": [
            {
                "slug": "freshness.age",
                "condition": {"<": [{"var": "results.freshness.age_days"}, 30]},
                "messages": {"pass": "Age is ${results.freshness.age_days}"},
            }
        ]
    }

    res = evaluate_rules(report, rules_def)
    assert len(res["all_rules"]) > 0
    assert len(res["passed_rules"]) > 0

    # Check interpolation
    rule_res = next(r for r in res["rules"] if r["slug"] == "age")
    assert rule_res["passed"] is True
    assert rule_res["message"] == "Age is 10"

    # Check incomplete evaluations when data is missing
    rules_def_broken = {
        "rules": [
            {
                "slug": "missing-data-rule",
                "condition": {"==": [{"var": "results.nonexistent.val"}, 1]},
                "messages": {"fail": "Should be incomplete"},
            },
            {
                "slug": "disabled-rule",
                "enable": False,
                "condition": {"==": [1, 1]},
                "messages": {"pass": "Should not run"},
            },
        ]
    }
    res2 = evaluate_rules(report, rules_def_broken)

    # Disabled rule should not be in results. Only declared rules are evaluated:
    # rules_def_broken declares only missing-data-rule (disabled-rule is filtered).
    assert len(res2["rules"]) == 1  # missing-data-rule only
    assert not any(r["slug"] == "disabled-rule" for r in res2["rules"])


def test_evaluate_rule_params():
    report = {
        "request": {"registry": "docker.io", "analyzers": ["freshness"]},
        "results": {"freshness": {"age_days": 15}},
    }

    # 1. Declare the age criterion; template default max_days is 30. Age is 15 -> Pass.
    res1 = evaluate_rules(
        report,
        {"rules": [{"provider": "freshness", "criterion": "age", "slug": "age"}]},
    )
    freshness = next(r for r in res1["rules"] if r["slug"] == "age")
    assert freshness["passed"] is True

    # 2. Declare the age criterion with max_days=7 override; 15 < 7 -> Fail.
    rules_def = {
        "rules": [
            {
                "provider": "freshness",
                "criterion": "age",
                "slug": "age",
                "options": {"max_days": 7},
            }
        ]
    }
    res2 = evaluate_rules(report, rules_def)
    freshness2 = next(r for r in res2["rules"] if r["slug"] == "age")
    assert freshness2["passed"] is False
    assert freshness2["message"] == "Image is older than 7 days (15 days)."


def test_criterion_key_equivalent_to_legacy_rule_key():
    """A `criterion:` template reference yields a report identical to `rule:`."""
    report = {
        "request": {"registry": "docker.io", "analyzers": ["cve"]},
        "results": {
            "cve": {
                "critical_count": 3,
                "high_count": 5,
                "fixed_count": 0,
            }
        },
    }

    legacy_def = {
        "rules": [
            {
                "provider": "cve",
                "rule": "cve-count",
                "slug": "cve-critical",
                "options": {"level": "critical", "max_count": 0},
            }
        ]
    }
    new_def = {
        "rules": [
            {
                "provider": "cve",
                "criterion": "cve-count",
                "slug": "cve-critical",
                "options": {"level": "critical", "max_count": 0},
            }
        ]
    }

    res_legacy = evaluate_rules(report, legacy_def)
    res_new = evaluate_rules(report, new_def)

    assert res_new == res_legacy

    # And the instantiated criterion is actually present and evaluated.
    crit = next(r for r in res_new["rules"] if r["slug"] == "cve-critical")
    assert crit["passed"] is False


def test_legacy_rule_key_emits_deprecation_warning():
    """Using the legacy `rule:` template key fires a deprecation warning."""
    report = {
        "request": {"registry": "docker.io", "analyzers": ["cve"]},
        "results": {"cve": {"critical_count": 0, "fixed_count": 0}},
    }
    legacy_def = {
        "rules": [
            {
                "provider": "cve",
                "rule": "cve-count",
                "slug": "cve-critical",
                "options": {"level": "critical", "max_count": 0},
            }
        ]
    }

    with pytest.warns(DeprecationWarning, match="criterion"):
        evaluate_rules(report, legacy_def)


def test_criterion_key_does_not_warn():
    """Using the preferred `criterion:` key emits no deprecation warning."""
    report = {
        "request": {"registry": "docker.io", "analyzers": ["cve"]},
        "results": {"cve": {"critical_count": 0, "fixed_count": 0}},
    }
    new_def = {
        "rules": [
            {
                "provider": "cve",
                "criterion": "cve-count",
                "slug": "cve-critical",
                "options": {"level": "critical", "max_count": 0},
            }
        ]
    }

    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        evaluate_rules(report, new_def)


def test_unreferenced_template_not_evaluated():
    """A default criterion not referenced by the playbook is never evaluated."""
    report = {
        "request": {"registry": "docker.io", "analyzers": ["oci"]},
        "results": {"oci": {"size_mb": 50, "layers": 5}},
    }
    # The oci analyzer ships max-size / layers-count / ... criteria, but the
    # playbook declares nothing: none of them must be evaluated.
    res = evaluate_rules(report, {"rules": []})
    assert res["rules"] == []


def test_only_declared_rules_evaluated():
    """The evaluated set equals exactly the declared rules (no inheritance)."""
    report = {
        "request": {"registry": "docker.io", "analyzers": ["oci", "freshness"]},
        "results": {"oci": {"size_mb": 50}, "freshness": {"age_days": 10}},
    }
    rules_def = {
        "rules": [
            {
                "provider": "freshness",
                "criterion": "age",
                "slug": "age",
                "options": {"max_days": 30},
            }
        ]
    }
    res = evaluate_rules(report, rules_def)
    assert [r["slug"] for r in res["rules"]] == ["age"]


def test_helper_operators_registered():
    """The new helper operators evaluate through json_logic."""
    import regis.rules.evaluator  # noqa: F401  (registers operators on import)
    from json_logic import jsonLogic

    assert jsonLogic({"is_true": [{"var": "v"}]}, {"v": "yes"}) is True
    assert jsonLogic({"is_true": [{"var": "v"}]}, {"v": "nope"}) is False
    assert jsonLogic({"is_false": [{"var": "v"}]}, {"v": "off"}) is True
    assert jsonLogic({"is_url": [{"var": "v"}]}, {"v": "https://x.io"}) is True
    assert jsonLogic({"is_url": [{"var": "v"}]}, {"v": "x.io"}) is False
    assert jsonLogic({"is_empty": [{"var": "v"}]}, {"v": ""}) is True
    assert jsonLogic({"is_set": [{"var": "v"}]}, {"v": "x"}) is True
    assert (
        jsonLogic({"matches": [{"var": "v"}, "^job-[0-9]+$"]}, {"v": "job-7"}) is True
    )
