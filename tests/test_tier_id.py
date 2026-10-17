from pathlib import Path

import jsonschema
import pytest
import yaml

from regis.core.domain.playbook.evaluator import evaluate
from regis.core.domain.playbook.loader import load_playbook
from tests.test_tier_icon import _minimal_report, _schema_validator


def _envelope(tiers: list[dict]) -> dict:
    return {
        "apiVersion": "regis.io/v1alpha1",
        "kind": "Playbook",
        "metadata": {"name": "t", "labels": {"app.kubernetes.io/version": "1.0.0"}},
        "spec": {"tiers": tiers},
    }


def _tier(name: str, **extra: str) -> dict:
    return {"name": name, "condition": {">": [{"var": "x"}, 1]}, **extra}


def test_schema_accepts_optional_tier_id():
    _schema_validator().validate(_envelope([_tier("Quarantaine", id="quarantine")]))
    _schema_validator().validate(_envelope([_tier("Quarantaine")]))


def test_schema_rejects_malformed_tier_id():
    with pytest.raises(jsonschema.ValidationError):
        _schema_validator().validate(_envelope([_tier("Q", id="Quarantine!")]))


def test_loader_rejects_duplicate_tier_ids(tmp_path: Path):
    path = tmp_path / "playbook.yaml"
    path.write_text(
        yaml.safe_dump(
            _envelope([_tier("A", id="quarantine"), _tier("B", id="quarantine")])
        ),
        encoding="utf-8",
    )
    with pytest.raises(jsonschema.ValidationError, match="quarantine"):
        load_playbook(path)


def test_loader_accepts_distinct_tier_ids(tmp_path: Path):
    path = tmp_path / "playbook.yaml"
    path.write_text(
        yaml.safe_dump(_envelope([_tier("A", id="quarantine"), _tier("B")])),
        encoding="utf-8",
    )
    assert [t.get("id") for t in load_playbook(path)["tiers"]] == ["quarantine", None]


def _playbook(**tier: str) -> dict:
    return {
        "name": "p",
        "apiVersion": "regis.io/v1alpha1",
        "tiers": [{"condition": {">": [{"var": "rules_summary.score"}, -1]}, **tier}],
        "rules": [],
    }


def test_evaluator_emits_tier_id():
    result = evaluate(_playbook(name="Quarantaine", id="quarantine"), _minimal_report())
    assert result["tier"] == "Quarantaine"
    assert result["tier_id"] == "quarantine"


def test_evaluator_omits_absent_tier_id():
    result = evaluate(_playbook(name="Plain"), _minimal_report())
    assert result["tier"] == "Plain"
    assert "tier_id" not in result
