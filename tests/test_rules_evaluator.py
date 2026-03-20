"""Tests for rules evaluator."""

from regis_cli.rules.evaluator import evaluate_rules, get_default_rules, merge_rules


def test_get_default_rules():
    rules = get_default_rules(["skopeo", "freshness"])
    slugs = [r.get("slug") for r in rules]
    assert "core.registry-domain-whitelist" in slugs
    assert "skopeo.no-root" in slugs
    assert "freshness.age" in slugs


def test_merge_rules():
    defaults = [{"slug": "test.1", "description": "A", "messages": {"pass": "ok"}}]
    custom = [{"slug": "test.1", "description": "B", "messages": {"fail": "bad"}}]

    merged = merge_rules(defaults, custom)
    assert len(merged) == 1
    assert merged[0]["description"] == "B"
    assert merged[0]["messages"]["pass"] == "ok"
    assert merged[0]["messages"]["fail"] == "bad"

    # Deep merging didn't destroy existing properties that weren't overridden
    assert merged[0]["slug"] == "test.1"


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
    rule_res = next(r for r in res["rules"] if r["slug"] == "freshness.age")
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

    # Disabled rule should not be in results
    assert (
        len(res2["rules"]) == 3
    )  # core.registry-domain-whitelist + freshness.age + missing-data-rule
    assert not any(r["slug"] == "disabled-rule" for r in res2["rules"])


def test_evaluate_rule_params():
    report = {
        "request": {"registry": "docker.io", "analyzers": ["freshness"]},
        "results": {"freshness": {"age_days": 15}},
    }

    # 1. Defaults: freshness max_days is 30. Age is 15. Condition: 15 < 30 -> Pass.
    res1 = evaluate_rules(report)
    freshness = next(r for r in res1["rules"] if r["slug"] == "freshness.age")
    assert freshness["passed"] is True

    # 2. Override configured param to 7. Condition 15 < 7 -> Fail.
    rules_def = {"rules": [{"slug": "freshness.age", "params": {"max_days": 7}}]}
    res2 = evaluate_rules(report, rules_def)
    freshness2 = next(r for r in res2["rules"] if r["slug"] == "freshness.age")
    assert freshness2["passed"] is False
    assert freshness2["message"] == "Image is older than 7 days (15 days)."
