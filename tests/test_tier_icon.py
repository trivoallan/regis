import importlib.resources
import json
from importlib import resources

import jsonschema
import yaml
from referencing import Registry, Resource

from regis.core.domain.playbook.evaluator import evaluate


def _schema_validator() -> jsonschema.Draft202012Validator:
    pkg = importlib.resources.files("regis.schemas.playbook.v1alpha1")
    schema = json.loads(
        pkg.joinpath("playbook.schema.json").read_text(encoding="utf-8")
    )
    pb_root = importlib.resources.files("regis.schemas.playbook")
    jsonlogic = json.loads(
        pb_root.joinpath("jsonlogic.schema.json").read_text(encoding="utf-8")
    )
    registry = Registry().with_resources(
        [
            (schema["$id"], Resource.from_contents(schema)),
            ("../jsonlogic.schema.json", Resource.from_contents(jsonlogic)),
        ]
    )
    return jsonschema.Draft202012Validator(schema, registry=registry)


def _minimal_report():
    return {
        "schemaVersion": 1,
        "version": "0.0.0",
        "request": {"registry": "r", "repository": "x", "tag": "t"},
        "results": {},
    }


def test_evaluator_emits_tier_icon():
    playbook = {
        "name": "p",
        "apiVersion": "regis.io/v1alpha1",
        "tiers": [
            {
                "name": "Gold",
                "icon": "🥇",
                "condition": {">": [{"var": "rules_summary.score"}, -1]},
            },
        ],
        "rules": [],
    }
    result = evaluate(playbook, _minimal_report())
    assert result["tier"] == "Gold"
    assert result["tier_icon"] == "🥇"


def test_evaluator_tier_without_icon_emits_none():
    playbook = {
        "name": "p",
        "apiVersion": "regis.io/v1alpha1",
        "tiers": [
            {"name": "Plain", "condition": {">": [{"var": "rules_summary.score"}, -1]}},
        ],
        "rules": [],
    }
    result = evaluate(playbook, _minimal_report())
    assert result["tier"] == "Plain"
    assert result.get("tier_icon") is None


def test_schema_accepts_optional_tier_icon():
    pb = {
        "apiVersion": "regis.io/v1alpha1",
        "kind": "Playbook",
        "metadata": {"name": "t", "labels": {"app.kubernetes.io/version": "1.0.0"}},
        "spec": {
            "tiers": [
                {"name": "Gold", "icon": "🥇", "condition": {">": [{"var": "x"}, 1]}}
            ]
        },
    }
    _schema_validator().validate(pb)  # must not raise


def test_default_playbook_tiers_have_icons():
    pb_text = (
        resources.files("regis") / "playbooks" / "default" / "playbook.yaml"
    ).read_text(encoding="utf-8")
    pb = yaml.safe_load(pb_text)
    tiers = pb["spec"]["tiers"]
    assert [t.get("icon") for t in tiers] == ["🥇", "🥈", "🥉"]
