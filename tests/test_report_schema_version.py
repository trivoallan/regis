"""Schema and helper tests for the report schemaVersion contract (Phase 0)."""

import importlib.resources
import json

import jsonschema
import pytest


def _report_schema() -> dict:
    text = (
        importlib.resources.files("regis.schemas.report")
        .joinpath("report.schema.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(text)


def _minimal_report(**overrides) -> dict:
    """A report with no playbooks/rules so no $ref resolution is triggered."""
    report = {
        "schemaVersion": 1,
        "version": "0.33.0",
        "request": {
            "url": "registry-1.docker.io/library/nginx:latest",
            "registry": "registry-1.docker.io",
            "repository": "library/nginx",
            "tag": "latest",
            "analyzers": ["metadata"],
            "timestamp": "2026-05-31T00:00:00+00:00",
        },
        "results": {"metadata": {}},
    }
    report.update(overrides)
    return report


class TestReportSchemaVersion:
    def test_accepts_report_with_schema_version(self):
        jsonschema.validate(instance=_minimal_report(), schema=_report_schema())

    def test_rejects_request_metadata(self):
        """request.metadata was removed; request has additionalProperties:false."""
        report = _minimal_report()
        report["request"]["metadata"] = {"ci": {"platform": "github"}}
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=report, schema=_report_schema())

    def test_accepts_top_level_metadata(self):
        report = _minimal_report(metadata={"ci": {"platform": "github"}})
        jsonschema.validate(instance=report, schema=_report_schema())

    def test_rejects_report_missing_schema_version(self):
        report = _minimal_report()
        del report["schemaVersion"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=report, schema=_report_schema())

    def test_rejects_non_integer_schema_version(self):
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(
                instance=_minimal_report(schemaVersion="1"),
                schema=_report_schema(),
            )

    def test_rejects_zero_schema_version(self):
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(
                instance=_minimal_report(schemaVersion=0),
                schema=_report_schema(),
            )


class TestEnsureSchemaVersion:
    def test_constant_is_three(self):
        from regis.utils.report import REPORT_SCHEMA_VERSION

        assert REPORT_SCHEMA_VERSION == 3

    def test_sets_when_missing(self):
        from regis.utils.report import REPORT_SCHEMA_VERSION, ensure_schema_version

        report = {"request": {}, "results": {}}
        result = ensure_schema_version(report)

        assert result is report  # mutates in place and returns it
        assert report["schemaVersion"] == REPORT_SCHEMA_VERSION

    def test_preserves_existing_value(self):
        from regis.utils.report import ensure_schema_version

        report = {"schemaVersion": 7, "request": {}, "results": {}}
        result = ensure_schema_version(report)

        assert result is report
        assert report["schemaVersion"] == 7


class TestContractFixture:
    def test_fixture_validates_against_real_validator(self):
        import json
        from pathlib import Path

        from regis.utils.report import validate_report

        fixture = Path(__file__).parent / "fixtures" / "report.v3.json"
        report = json.loads(fixture.read_text(encoding="utf-8"))

        assert report["schemaVersion"] == 3
        validate_report(report)  # must not raise

    def test_analyzer_blobs_match_their_schemas(self):
        import json
        from pathlib import Path

        import jsonschema

        fixtures = Path(__file__).parent / "fixtures" / "report.v3.json"
        report = json.loads(fixtures.read_text(encoding="utf-8"))

        schema_dir = importlib.resources.files("regis.schemas.analyzer")
        for slug in ("cve", "oci"):
            schema = json.loads(
                schema_dir.joinpath(f"{slug}.schema.json").read_text(encoding="utf-8")
            )
            jsonschema.validate(instance=report["results"][slug], schema=schema)
