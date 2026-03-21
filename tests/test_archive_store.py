"""Tests for regis_cli.archive.store."""

import json
from pathlib import Path

from regis_cli.archive.store import (
    _load_json_array,
    _make_summary,
    _safe_segment,
    add_to_archive,
)

_MINIMAL_REPORT = {
    "request": {
        "registry": "docker.io",
        "repository": "library/nginx",
        "tag": "latest",
        "timestamp": "2024-01-15T10:00:00+00:00",
        "digest": "sha256:abc123",
    },
    "rules_summary": {"passed": ["r1", "r2"], "total": ["r1", "r2", "r3"], "score": 66},
    "results": {
        "trivy": {
            "critical_count": 0,
            "high_count": 1,
            "medium_count": 3,
            "low_count": 5,
        },
        "freshness": {"age_days": 10},
        "sbom": {"component_count": 42},
        "scorecarddev": {"score": 7.5},
    },
}


class TestMakeSummary:
    def test_full_report_list_based(self):
        summary = _make_summary(
            _MINIMAL_REPORT, "docker.io/nginx/latest/ts/report.json"
        )
        assert summary["registry"] == "docker.io"
        assert summary["repository"] == "library/nginx"
        assert summary["tag"] == "latest"
        assert summary["rules_passed"] == 2
        assert summary["rules_total"] == 3
        assert summary["score"] == 66
        assert summary["cve_critical"] == 0
        assert summary["cve_high"] == 1
        assert summary["age_days"] == 10
        assert summary["sbom_component_count"] == 42
        assert summary["scorecard_score"] == 7.5
        assert summary["digest"] == "sha256:abc123"
        assert summary["path"] == "docker.io/nginx/latest/ts/report.json"

    def test_int_based_rules_summary(self):
        report = {
            **_MINIMAL_REPORT,
            "rules_summary": {"passed": 5, "total": 10, "score": 50},
        }
        summary = _make_summary(report, "path")
        assert summary["rules_passed"] == 5
        assert summary["rules_total"] == 10

    def test_missing_request_and_results(self):
        summary = _make_summary({}, "path")
        assert summary["registry"] == "unknown"
        assert summary["repository"] == "unknown"
        assert summary["tag"] == "unknown"
        assert summary["rules_passed"] == 0
        assert summary["rules_total"] == 0
        assert summary["cve_critical"] is None
        assert summary["age_days"] is None

    def test_tier_from_top_level(self):
        report = {**_MINIMAL_REPORT, "tier": "gold"}
        summary = _make_summary(report, "path")
        assert summary["tier"] == "gold"

    def test_tier_from_playbook(self):
        report = {**_MINIMAL_REPORT, "playbook": {"tier": "silver"}}
        summary = _make_summary(report, "path")
        assert summary["tier"] == "silver"

    def test_timestamp_auto_generated_when_missing(self):
        report = {"request": {"registry": "r", "repository": "repo", "tag": "t"}}
        summary = _make_summary(report, "path")
        assert isinstance(summary["timestamp"], str)
        assert len(summary["timestamp"]) > 0

    def test_id_format(self):
        summary = _make_summary(_MINIMAL_REPORT, "path")
        assert summary["id"].startswith("docker.io/library/nginx/latest/")


class TestSafeSegment:
    def test_replaces_slash(self):
        assert _safe_segment("a/b") == "a_b"

    def test_replaces_backslash(self):
        assert _safe_segment("a\\b") == "a_b"

    def test_replaces_colon(self):
        assert _safe_segment("host:port") == "host_port"

    def test_plain_string_unchanged(self):
        assert _safe_segment("nginx") == "nginx"


class TestLoadJsonArray:
    def test_missing_file_returns_empty(self, tmp_path):
        assert _load_json_array(tmp_path / "missing.json") == []

    def test_invalid_json_returns_empty(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("not json", encoding="utf-8")
        assert _load_json_array(p) == []

    def test_json_object_returns_empty(self, tmp_path):
        p = tmp_path / "obj.json"
        p.write_text('{"key": "value"}', encoding="utf-8")
        assert _load_json_array(p) == []

    def test_valid_array_returned(self, tmp_path):
        p = tmp_path / "data.json"
        p.write_text('[{"id": "x"}]', encoding="utf-8")
        assert _load_json_array(p) == [{"id": "x"}]


class TestAddToArchive:
    def test_creates_report_file(self, tmp_path):
        dest = add_to_archive(_MINIMAL_REPORT, tmp_path / "archive")
        assert dest.exists()
        assert dest.name == "report.json"

    def test_creates_manifest_and_data(self, tmp_path):
        archive = tmp_path / "archive"
        add_to_archive(_MINIMAL_REPORT, archive)
        assert (archive / "manifest.json").exists()
        assert (archive / "data.json").exists()

    def test_manifest_contains_summary(self, tmp_path):
        archive = tmp_path / "archive"
        add_to_archive(_MINIMAL_REPORT, archive)
        manifest = json.loads((archive / "manifest.json").read_text(encoding="utf-8"))
        assert len(manifest) == 1
        assert manifest[0]["registry"] == "docker.io"

    def test_second_entry_appended(self, tmp_path):
        archive = tmp_path / "archive"
        report2 = {
            **_MINIMAL_REPORT,
            "request": {
                **_MINIMAL_REPORT["request"],
                "timestamp": "2024-01-16T10:00:00+00:00",
            },
        }
        add_to_archive(_MINIMAL_REPORT, archive)
        add_to_archive(report2, archive)
        manifest = json.loads((archive / "manifest.json").read_text(encoding="utf-8"))
        assert len(manifest) == 2

    def test_deduplication_by_id(self, tmp_path):
        archive = tmp_path / "archive"
        add_to_archive(_MINIMAL_REPORT, archive)
        add_to_archive(_MINIMAL_REPORT, archive)
        manifest = json.loads((archive / "manifest.json").read_text(encoding="utf-8"))
        assert len(manifest) == 1

    def test_sorted_newest_first(self, tmp_path):
        archive = tmp_path / "archive"
        old = {
            **_MINIMAL_REPORT,
            "request": {
                **_MINIMAL_REPORT["request"],
                "timestamp": "2024-01-10T00:00:00+00:00",
            },
        }
        new = {
            **_MINIMAL_REPORT,
            "request": {
                **_MINIMAL_REPORT["request"],
                "timestamp": "2024-01-20T00:00:00+00:00",
            },
        }
        add_to_archive(old, archive)
        add_to_archive(new, archive)
        manifest = json.loads((archive / "manifest.json").read_text(encoding="utf-8"))
        assert manifest[0]["timestamp"] > manifest[1]["timestamp"]

    def test_pretty_false_compact_json(self, tmp_path):
        dest = add_to_archive(_MINIMAL_REPORT, tmp_path / "archive", pretty=False)
        content = dest.read_text(encoding="utf-8")
        assert "\n" not in content

    def test_returns_path_object(self, tmp_path):
        dest = add_to_archive(_MINIMAL_REPORT, tmp_path / "archive")
        assert isinstance(dest, Path)
