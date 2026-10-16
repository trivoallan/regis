"""MissingDataTracker records which required keys were absent."""

import pytest

from regis.core.domain.playbook.context import MissingDataTracker


def test_keyerror_records_full_nested_key() -> None:
    tracker = MissingDataTracker({"results": {"cve": {}}})
    with pytest.raises(KeyError):
        tracker["results"]["cve"]["critical_count"]
    assert tracker.missing_accessed is True
    assert tracker.missing_keys == ["results.cve.critical_count"]


def test_none_value_is_missing() -> None:
    tracker = MissingDataTracker({"results": {"freshness": None}})
    assert tracker["results"]["freshness"] is None
    assert tracker.missing_keys == ["results.freshness"]


def test_failed_contains_is_missing() -> None:
    tracker = MissingDataTracker({"results": {}})
    assert "sbom" not in tracker["results"]
    assert tracker.missing_keys == ["results.sbom"]


def test_keys_are_deduplicated_in_access_order() -> None:
    tracker = MissingDataTracker({"results": {}})
    tracker.get("results").get("secrets")
    tracker.get("results").get("dockle")
    tracker.get("results").get("secrets")
    assert tracker.missing_keys == ["results.secrets", "results.dockle"]


def test_present_keys_and_optional_namespace_not_recorded() -> None:
    tracker = MissingDataTracker({"results": {"cve": {"n": 0}}, "metadata": {}})
    assert tracker["results"]["cve"]["n"] == 0
    assert tracker.get("metadata").get("owner") is None
    assert tracker.missing_accessed is False
    assert tracker.missing_keys == []
