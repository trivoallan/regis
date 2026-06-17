"""Tests for rules evaluator."""

import warnings

import pytest

from regis.core.domain.rules.evaluator import (
    _interpolate_string,
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
    from json_logic import jsonLogic

    import regis.core.domain.rules.evaluator  # noqa: F401  (registers operators on import)

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


def test_missing_metadata_does_not_mark_incomplete():
    """A rule referencing an absent metadata.* key resolves to a clean fail/pass."""
    report = {
        "request": {"registry": "docker.io", "analyzers": ["metadata"]},
        "results": {},
        "metadata": {},
    }
    rules_def = {
        "rules": [
            {
                "slug": "gate-must-be-set",
                "condition": {"is_set": [{"var": "metadata.gate.enabled"}]},
                "messages": {"pass": "set", "fail": "not set"},
            }
        ]
    }
    res = evaluate_rules(report, rules_def)
    rule = next(r for r in res["rules"] if r["slug"] == "gate-must-be-set")
    assert rule["status"] == "failed"  # absent -> failed, NOT incomplete
    assert rule["passed"] is False


def test_present_metadata_evaluates_normally():
    report = {
        "request": {"registry": "docker.io", "analyzers": ["metadata"]},
        "results": {},
        "metadata": {"ci": {"job": {"url": "https://ci.example/run/1"}}},
    }
    rules_def = {
        "rules": [
            {
                "slug": "job-url-valid",
                "condition": {"is_url": [{"var": "metadata.ci.job.url"}]},
                "messages": {"pass": "ok", "fail": "bad"},
            }
        ]
    }
    res = evaluate_rules(report, rules_def)
    rule = next(r for r in res["rules"] if r["slug"] == "job-url-valid")
    assert rule["status"] == "passed"


def test_missing_results_still_incomplete():
    """Non-metadata missing data must still yield incomplete (no regression)."""
    report = {
        "request": {"registry": "docker.io", "analyzers": ["cve"]},
        "results": {},
    }
    rules_def = {
        "rules": [
            {
                "slug": "needs-cve",
                "condition": {"==": [{"var": "results.cve.critical_count"}, 0]},
                "messages": {"pass": "ok", "fail": "bad"},
            }
        ]
    }
    res = evaluate_rules(report, rules_def)
    rule = next(r for r in res["rules"] if r["slug"] == "needs-cve")
    assert rule["status"] == "incomplete"


# ---------------------------------------------------------------------------
# _interpolate_string edge cases
# ---------------------------------------------------------------------------


def test_interpolate_empty_template_returns_input():
    assert _interpolate_string("", {}) == ""


def test_interpolate_list_length():
    ctx = {"items": ["a", "b", "c"]}
    assert _interpolate_string("n=${items.length}", ctx) == "n=3"


def test_interpolate_list_index():
    ctx = {"items": ["a", "b", "c"]}
    assert _interpolate_string("first=${items.0}", ctx) == "first=a"
    assert _interpolate_string("last=${items.2}", ctx) == "last=c"


def test_interpolate_list_index_out_of_range_keeps_placeholder():
    assert _interpolate_string("x=${items.9}", {"items": ["a"]}) == "x=${items.9}"


def test_interpolate_list_invalid_part_keeps_placeholder():
    """A non-integer, non-'length' part on a list keeps the placeholder."""
    assert (
        _interpolate_string("x=${items.foo}", {"items": ["a", "b"]}) == "x=${items.foo}"
    )


def test_interpolate_missing_nested_key_returns_missing():
    """A path that reaches a dict but the key is absent returns MISSING."""
    ctx = {"data": {"a": 1}}
    assert _interpolate_string("v=${data.b}", ctx) == "v=MISSING"


# ---------------------------------------------------------------------------
# Custom JSON Logic operators — non-list / non-dict inputs return False / []
# ---------------------------------------------------------------------------


def test_custom_operators_with_non_list_inputs():
    """intersects, contains_all, subset, env_contains return False for non-list inputs."""
    from json_logic import jsonLogic

    import regis.core.domain.rules.evaluator  # noqa: F401 — ensures operators are registered

    # intersects: non-list inputs
    assert jsonLogic({"intersects": ["not-a-list", ["a"]]}, {}) is False
    assert jsonLogic({"intersects": [["a"], "not-a-list"]}, {}) is False

    # contains_all: non-list inputs
    assert jsonLogic({"contains_all": ["x", ["a"]]}, {}) is False

    # subset: non-list inputs
    assert jsonLogic({"subset": ["x", ["a"]]}, {}) is False

    # env_contains: non-list inputs
    assert jsonLogic({"env_contains": ["not-list", ["sub"]]}, {}) is False


def test_keys_operator_with_non_dict_returns_empty():
    """keys() returns [] for non-dict input."""
    from json_logic import jsonLogic

    import regis.core.domain.rules.evaluator  # noqa: F401

    assert jsonLogic({"keys": [{"var": "v"}]}, {"v": "not-a-dict"}) == []
    assert jsonLogic({"keys": [{"var": "v"}]}, {"v": ["a", "b"]}) == []


def test_get_operator_with_non_dict_returns_none():
    """get() returns None for non-dict data."""
    from json_logic import jsonLogic

    import regis.core.domain.rules.evaluator  # noqa: F401

    assert jsonLogic({"get": [{"var": "v"}, "key"]}, {"v": "not-a-dict"}) is None


# ---------------------------------------------------------------------------
# resolve_rules — merge when same (provider, slug) appears twice
# ---------------------------------------------------------------------------


def test_resolve_rules_merges_duplicate_slug():
    """Two declared rules with the same (provider, slug) merge messages and params."""
    templates = []
    declared = [
        {
            "provider": "custom",
            "slug": "my-rule",
            "condition": {"==": [1, 1]},
            "messages": {"pass": "v1-pass", "fail": "v1-fail"},
            "params": {"threshold": 10},
        },
        {
            "provider": "custom",
            "slug": "my-rule",
            "messages": {"fail": "v2-fail"},
            "params": {"extra": True},
        },
    ]
    resolved = resolve_rules(templates, declared)
    assert len(resolved) == 1
    rule = resolved[0]
    # Messages merged: v2-fail overrides v1-fail, v1-pass preserved
    assert rule["messages"]["pass"] == "v1-pass"
    assert rule["messages"]["fail"] == "v2-fail"
    # Params merged
    assert rule["params"]["threshold"] == 10
    assert rule["params"]["extra"] is True


# ---------------------------------------------------------------------------
# resolve_rules — Case A: slug auto-generation
# ---------------------------------------------------------------------------


def test_resolve_rules_autogenerate_slug_with_level():
    """When no slug is given and options contains 'level', slug becomes <template>.<level>."""
    templates = [
        {
            "provider": "cve",
            "slug": "cve-count",
            "condition": {"==": [1, 1]},
            "messages": {"pass": "ok", "fail": "err"},
        }
    ]
    declared = [
        {
            "provider": "cve",
            "criterion": "cve-count",
            "options": {"level": "critical"},
            # No slug provided
        }
    ]
    resolved = resolve_rules(templates, declared)
    assert len(resolved) == 1
    assert resolved[0]["slug"] == "cve-count.critical"


def test_resolve_rules_autogenerate_slug_without_level():
    """When no slug and no 'level' in options, slug becomes <template>.<index>."""
    templates = [
        {
            "provider": "cve",
            "slug": "cve-count",
            "condition": {"==": [1, 1]},
            "messages": {"pass": "ok", "fail": "err"},
        }
    ]
    declared = [
        {
            "provider": "cve",
            "criterion": "cve-count",
            # No slug, no level in options
        }
    ]
    resolved = resolve_rules(templates, declared)
    assert len(resolved) == 1
    assert resolved[0]["slug"] == "cve-count.0"


# ---------------------------------------------------------------------------
# resolve_rules — Case A: template not found but slug provided
# ---------------------------------------------------------------------------


def test_resolve_rules_template_not_found_with_slug_appends_raw():
    """When template is not found but a slug is given, the raw rule_def is kept."""
    templates = []
    declared = [
        {
            "provider": "nonexistent",
            "criterion": "ghost-template",
            "slug": "fallback-rule",
            "condition": {"==": [1, 1]},
            "messages": {"pass": "ok", "fail": "err"},
        }
    ]
    resolved = resolve_rules(templates, declared)
    assert len(resolved) == 1
    assert resolved[0]["slug"] == "fallback-rule"
    assert resolved[0]["provider"] == "nonexistent"


# ---------------------------------------------------------------------------
# resolve_rules — Case B: explicit provider on a standalone rule
# ---------------------------------------------------------------------------


def test_resolve_rules_case_b_explicit_provider():
    """Case B with an explicit provider: provider and slug stay as given."""
    templates = []
    declared = [
        {
            "provider": "myteam",
            "slug": "custom-check",
            "condition": {"==": [1, 1]},
            "messages": {"pass": "ok", "fail": "err"},
        }
    ]
    resolved = resolve_rules(templates, declared)
    assert len(resolved) == 1
    assert resolved[0]["provider"] == "myteam"
    assert resolved[0]["slug"] == "custom-check"


def test_resolve_rules_case_b_no_rule_id_skipped():
    """A declared rule with no criterion, rule, or slug is silently skipped."""
    templates = []
    declared = [{"condition": {"==": [1, 1]}}]
    resolved = resolve_rules(templates, declared)
    assert resolved == []


# ---------------------------------------------------------------------------
# resolve_rules — Case A fallback: template found via regis.analyzers.<provider>
# ---------------------------------------------------------------------------


def test_resolve_rules_fallback_prefixed_provider():
    """A template registered under 'regis.analyzers.myprov' is found via plain 'myprov'."""
    templates = [
        {
            "provider": "regis.analyzers.myprov",
            "slug": "some-check",
            "condition": {"==": [1, 1]},
            "messages": {"pass": "ok", "fail": "err"},
        }
    ]
    declared = [
        {
            "provider": "myprov",
            "criterion": "some-check",
            "slug": "my-check",
        }
    ]
    resolved = resolve_rules(templates, declared)
    assert len(resolved) == 1
    assert resolved[0]["slug"] == "my-check"


# ---------------------------------------------------------------------------
# resolve_rules — last-resort: template loaded directly from the analyzer class
# ---------------------------------------------------------------------------


def test_resolve_rules_last_resort_loads_from_analyzer():
    """When template is absent from catalogue, it is loaded directly from the analyzer."""
    # The 'freshness' analyzer is present; its 'age' template should be found
    # even when we pass an empty templates list.
    resolved = resolve_rules(
        [],
        [
            {
                "provider": "freshness",
                "criterion": "age",
                "slug": "age-direct",
            }
        ],
    )
    assert len(resolved) == 1
    assert resolved[0]["slug"] == "age-direct"
    assert "condition" in resolved[0]


# ---------------------------------------------------------------------------
# evaluate_rules — exception in jsonLogic marks rule as failed
# ---------------------------------------------------------------------------


def test_evaluate_rules_condition_exception_marks_failed():
    """A rule whose condition raises an exception is marked failed, not crashed."""
    report = {"request": {"registry": "docker.io", "analyzers": []}, "results": {}}
    rules_def = {
        "rules": [
            {
                "slug": "bad-op",
                "condition": {"__nonexistent_op__": [1, 2]},
                "messages": {"pass": "ok", "fail": "err"},
            }
        ]
    }
    res = evaluate_rules(report, rules_def)
    bad = next(r for r in res["rules"] if r["slug"] == "bad-op")
    assert bad["passed"] is False
    assert bad["status"] == "failed"
