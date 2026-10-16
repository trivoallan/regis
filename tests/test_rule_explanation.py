"""Each rule entry says what it read: observed facts, threshold, missing keys."""

import json
from pathlib import Path

import jsonschema

import regis
from regis.core.domain.playbook.context import MissingDataTracker
from regis.core.domain.rules.evaluator import _explain, evaluate_rules


def _rule(report: dict, criterion: str, provider: str, options: dict | None = None):
    res = evaluate_rules(
        report,
        {
            "rules": [
                {
                    "provider": provider,
                    "criterion": criterion,
                    "slug": "r",
                    "options": options or {},
                }
            ]
        },
    )
    return next(r for r in res["rules"] if r["slug"] == "r")


def test_failed_rule_carries_fact_and_threshold() -> None:
    report = {
        "request": {"analyzers": ["freshness"]},
        "results": {"freshness": {"age_days": 15, "reproducible_build": False}},
    }
    rule = _rule(report, "age", "freshness", {"max_days": 7})
    assert rule["status"] == "failed"
    assert rule["observed"] == {
        "results.freshness.age_days": 15,
        "results.freshness.reproducible_build": False,
    }
    assert rule["threshold"] == {"max_days": 7}
    assert rule["missing_keys"] == []


def test_incomplete_rule_names_missing_key() -> None:
    report = {"request": {"analyzers": ["freshness"]}, "results": {}}
    rule = _rule(report, "age", "freshness", {"max_days": 90})
    assert rule["status"] == "incomplete"
    assert rule["missing_keys"] == ["results.freshness"]
    assert rule["observed"] == {}
    assert rule["threshold"] == {"max_days": 90}


def test_request_fact_is_observed() -> None:
    report = {
        "request": {"analyzers": ["oci"], "tag": "latest"},
        "results": {"oci": {}},
    }
    rule = _rule(report, "tag-blacklist", "oci")
    assert rule["status"] == "failed"
    assert rule["observed"] == {"request.tag": "latest"}
    assert rule["threshold"] == {}


def test_explain_keeps_deepest_keys_and_both_param_aliases() -> None:
    context = {
        "results": {"cve": {"fixed_count": 5}},
        "criterion": {"params": {"max_count": 0}},
        "rule": {"params": {"level": "high"}},
        "other": {"x": 1},
    }
    tracker = MissingDataTracker(context)
    tracker["results"]["cve"]["fixed_count"]
    tracker["criterion"]["params"]["max_count"]
    tracker["rule"]["params"]["level"]
    tracker["other"]["x"]
    observed, threshold = _explain(tracker, context)
    assert observed == {"results.cve.fixed_count": 5}
    assert threshold == {"max_count": 0, "level": "high"}


def test_explain_summarizes_large_values() -> None:
    context = {
        "results": {
            "few": ["a", "b"],
            "many": list(range(11)),
            "nested": [{"a": 1}],
            "obj": {"a": 1, "b": 2},
        }
    }
    tracker = MissingDataTracker(context)
    for key in ("few", "many", "nested", "obj"):
        tracker["results"][key]
    observed, _ = _explain(tracker, context)
    assert observed == {
        "results.few": ["a", "b"],
        "results.many": "<list of 11>",
        "results.nested": "<list of 1>",
        "results.obj": "<object with 2 keys>",
    }


def test_rule_entry_validates_against_result_schema() -> None:
    report = {"request": {"analyzers": ["freshness"]}, "results": {}}
    rule = _rule(report, "age", "freshness")
    path = Path(regis.__file__).parent / "schemas/playbook/result.schema.json"
    item_schema = json.loads(path.read_text())["properties"]["rules"]["items"]
    jsonschema.validate(rule, item_schema)
