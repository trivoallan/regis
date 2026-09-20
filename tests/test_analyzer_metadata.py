"""Tests for MetadataAnalyzer (nested well-known schema + format checking)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from regis.core.domain.analyzers.base import AnalyzerError
from regis.core.domain.analyzers.metadata import MetadataAnalyzer


class TestMetadataAnalyzerWellKnownOnly:
    """Tests without a playbook meta_schema_path. Meta is nested, as in production."""

    def test_empty_metadata_valid(self):
        analyzer = MetadataAnalyzer(metadata={})
        result = analyzer.analyze()
        assert result["analyzer"] == "metadata"
        assert result["valid"] is True
        # Every known leaf field is reported valid when absent (optional).
        for v in result["metadata_validation"].values():
            assert v == {"valid": True}
        # Known leaf paths are dotted.
        assert "ci.platform" in result["metadata_validation"]
        assert "ci.job.url" in result["metadata_validation"]

    def test_valid_well_known_field(self):
        analyzer = MetadataAnalyzer(metadata={"ci": {"platform": "github"}})
        result = analyzer.analyze()
        assert result["valid"] is True
        assert result["metadata"]["ci"]["platform"] == "github"
        assert result["metadata_validation"]["ci.platform"] == {"valid": True}

    def test_invalid_well_known_enum_value(self):
        analyzer = MetadataAnalyzer(metadata={"ci": {"platform": "bitbucket"}})
        result = analyzer.analyze()
        assert result["valid"] is False
        assert result["metadata_validation"]["ci.platform"]["valid"] is False
        assert "error" in result["metadata_validation"]["ci.platform"]

    def test_valid_well_known_uri(self):
        analyzer = MetadataAnalyzer(
            metadata={"ci": {"job": {"url": "https://ci.example/run/9"}}}
        )
        result = analyzer.analyze()
        assert result["valid"] is True
        assert result["metadata_validation"]["ci.job.url"] == {"valid": True}

    def test_invalid_well_known_uri(self):
        analyzer = MetadataAnalyzer(metadata={"ci": {"job": {"url": "not a url"}}})
        result = analyzer.analyze()
        assert result["valid"] is False
        assert result["metadata_validation"]["ci.job.url"]["valid"] is False

    def test_unknown_keys_passthrough_not_in_validation(self):
        analyzer = MetadataAnalyzer(
            metadata={"custom": {"key": "value"}, "ci": {"platform": "github"}}
        )
        result = analyzer.analyze()
        assert result["valid"] is True
        assert result["metadata"]["custom"]["key"] == "value"
        assert "custom.key" not in result["metadata_validation"]
        assert "ci.platform" in result["metadata_validation"]

    def test_analyze_ignores_positional_args(self):
        analyzer = MetadataAnalyzer(metadata={"ci": {"job": {"id": "123"}}})
        ctx = MagicMock()
        result = analyzer.analyze(ctx)
        assert result["valid"] is True
        assert result["metadata"]["ci"]["job"]["id"] == "123"

    def test_validate_is_noop(self):
        analyzer = MetadataAnalyzer(metadata={})
        analyzer.validate({})  # should not raise


class TestMetadataAnalyzerWithPlaybookSchema:
    """Tests with a custom playbook meta_schema_path (merged via allOf)."""

    def _write_schema(self, tmp_path: Path, schema: dict) -> Path:
        p = tmp_path / "meta.schema.json"
        p.write_text(json.dumps(schema))
        return p

    def test_required_field_present(self, tmp_path):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["PROJECT_ID"],
            "properties": {"PROJECT_ID": {"type": "string"}},
        }
        schema_path = self._write_schema(tmp_path, schema)
        analyzer = MetadataAnalyzer(
            metadata={"PROJECT_ID": "PROJ-42"}, meta_schema_paths=[schema_path]
        )
        result = analyzer.analyze()
        assert result["valid"] is True
        assert result["metadata"]["PROJECT_ID"] == "PROJ-42"
        assert result["metadata_validation"]["PROJECT_ID"] == {"valid": True}

    def test_required_field_missing(self, tmp_path):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["PROJECT_ID"],
            "properties": {"PROJECT_ID": {"type": "string"}},
        }
        schema_path = self._write_schema(tmp_path, schema)
        analyzer = MetadataAnalyzer(metadata={}, meta_schema_paths=[schema_path])
        result = analyzer.analyze()
        assert result["valid"] is False
        assert result["metadata_validation"]["PROJECT_ID"]["valid"] is False
        assert "error" in result["metadata_validation"]["PROJECT_ID"]

    def test_required_field_wrong_type(self, tmp_path):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["PROJECT_ID"],
            "properties": {"PROJECT_ID": {"type": "string"}},
        }
        schema_path = self._write_schema(tmp_path, schema)
        analyzer = MetadataAnalyzer(
            metadata={"PROJECT_ID": 42}, meta_schema_paths=[schema_path]
        )
        result = analyzer.analyze()
        assert result["valid"] is False
        assert result["metadata_validation"]["PROJECT_ID"]["valid"] is False

    def test_optional_field_absent(self, tmp_path):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {"OPTIONAL_FIELD": {"type": "string"}},
        }
        schema_path = self._write_schema(tmp_path, schema)
        analyzer = MetadataAnalyzer(metadata={}, meta_schema_paths=[schema_path])
        result = analyzer.analyze()
        assert result["valid"] is True
        assert "OPTIONAL_FIELD" not in result["metadata"]
        assert result["metadata_validation"]["OPTIONAL_FIELD"] == {"valid": True}

    def test_nonexistent_schema_path_is_a_hard_error(self, tmp_path):
        """A named-but-unreadable schema must not silently degrade to well-known only."""
        nonexistent = tmp_path / "does_not_exist.json"
        analyzer = MetadataAnalyzer(
            metadata={"ci": {"platform": "github"}}, meta_schema_paths=[nonexistent]
        )
        with pytest.raises(AnalyzerError, match="does_not_exist.json"):
            analyzer.analyze()

    def test_malformed_schema_is_a_hard_error(self, tmp_path):
        broken = tmp_path / "meta.schema.json"
        broken.write_text("{ not json", encoding="utf-8")
        analyzer = MetadataAnalyzer(metadata={}, meta_schema_paths=[broken])
        with pytest.raises(AnalyzerError, match="meta.schema.json"):
            analyzer.analyze()

    def test_combined_well_known_and_playbook_fields(self, tmp_path):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["PROJECT_ID"],
            "properties": {"PROJECT_ID": {"type": "string"}},
        }
        schema_path = self._write_schema(tmp_path, schema)
        analyzer = MetadataAnalyzer(
            metadata={"PROJECT_ID": "PROJ-1", "ci": {"platform": "gitlab"}},
            meta_schema_paths=[schema_path],
        )
        result = analyzer.analyze()
        assert result["valid"] is True
        assert result["metadata_validation"]["PROJECT_ID"] == {"valid": True}
        assert result["metadata_validation"]["ci.platform"] == {"valid": True}

    def test_none_metadata_defaults_to_empty(self):
        analyzer = MetadataAnalyzer(metadata=None)
        result = analyzer.analyze()
        assert result["valid"] is True
        assert result["metadata"] == {}

    def test_required_field_partially_present(self, tmp_path):
        """When some required fields are present, only the missing ones are invalid."""
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["FIELD_A", "FIELD_B"],
            "properties": {
                "FIELD_A": {"type": "string"},
                "FIELD_B": {"type": "string"},
            },
        }
        schema_path = self._write_schema(tmp_path, schema)
        analyzer = MetadataAnalyzer(
            metadata={"FIELD_A": "present"}, meta_schema_paths=[schema_path]
        )
        result = analyzer.analyze()
        assert result["valid"] is False
        assert result["metadata_validation"]["FIELD_A"] == {"valid": True}
        assert result["metadata_validation"]["FIELD_B"]["valid"] is False

    def test_unexpected_key_rejected_by_strict_schema(self, tmp_path):
        """A structural (no-path) error is surfaced, keeping valid and the map consistent."""
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {"KNOWN": {"type": "string"}},
            "additionalProperties": False,
        }
        schema_path = self._write_schema(tmp_path, schema)
        analyzer = MetadataAnalyzer(
            metadata={"KNOWN": "ok", "SURPRISE": "x"}, meta_schema_paths=[schema_path]
        )
        result = analyzer.analyze()
        assert result["valid"] is False
        # The structural error is recorded (not silently dropped).
        invalid = [
            k for k, v in result["metadata_validation"].items() if not v["valid"]
        ]
        assert invalid, "expected at least one invalid entry for the structural error"


class TestMetadataAnalyzerSeveralSchemas:
    """Every schema source stacks by allOf; none can relax another."""

    @staticmethod
    def _write(path: Path, required: str) -> Path:
        path.write_text(
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "required": [required],
                    "properties": {required: {"type": "string"}},
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_both_schemas_are_enforced(self, tmp_path):
        a = self._write(tmp_path / "a.json", "PROJECT_ID")
        b = self._write(tmp_path / "b.json", "SAISINE_URL")
        analyzer = MetadataAnalyzer(
            metadata={"PROJECT_ID": "PROJ-42"}, meta_schema_paths=[a, b]
        )
        result = analyzer.analyze()
        assert result["valid"] is False
        assert result["metadata_validation"]["PROJECT_ID"] == {"valid": True}
        assert result["metadata_validation"]["SAISINE_URL"]["valid"] is False

    def test_all_requirements_satisfied(self, tmp_path):
        a = self._write(tmp_path / "a.json", "PROJECT_ID")
        b = self._write(tmp_path / "b.json", "SAISINE_URL")
        analyzer = MetadataAnalyzer(
            metadata={"PROJECT_ID": "PROJ-42", "SAISINE_URL": "https://x.example/c"},
            meta_schema_paths=[a, b],
        )
        assert analyzer.analyze()["valid"] is True

    def test_schema_sources_lists_loaded_schemas_in_order(self, tmp_path):
        a = self._write(tmp_path / "a.json", "PROJECT_ID")
        b = self._write(tmp_path / "b.json", "SAISINE_URL")
        result = MetadataAnalyzer(metadata={}, meta_schema_paths=[a, b]).analyze()
        assert result["schema_sources"] == [str(a), str(b)]

    def test_schema_sources_empty_without_a_source(self):
        result = MetadataAnalyzer(metadata={"ci": {"platform": "github"}}).analyze()
        assert result["schema_sources"] == []


def test_metadata_analyze_ignores_context():
    """analyze accepts a context but ignores it; result depends only on __init__ data."""
    from regis.core.domain.analyzers.metadata import MetadataAnalyzer

    a = MetadataAnalyzer(metadata={"ci": {"job": {"id": "1"}}})
    via_none = a.analyze()  # rerun-style no-arg call must still work
    via_ctx = a.analyze(object())  # loop-style call with an (ignored) ctx
    assert via_none == via_ctx
    assert via_none["metadata"] == {"ci": {"job": {"id": "1"}}}


class TestMetadataAnalyzerAdvisoryMode:
    """Advisory mode suspends the sanction, never the finding."""

    @staticmethod
    def _schema(tmp_path: Path) -> Path:
        path = tmp_path / "meta.schema.json"
        path.write_text(
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "required": ["SAISINE_URL"],
                    "properties": {"SAISINE_URL": {"type": "string"}},
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_enforcing_by_default(self, tmp_path):
        result = MetadataAnalyzer(
            metadata={}, meta_schema_paths=[self._schema(tmp_path)]
        ).analyze()
        assert result["enforcement"] == "enforcing"

    def test_advisory_keeps_the_finding_intact(self, tmp_path):
        schema = self._schema(tmp_path)
        result = MetadataAnalyzer(
            metadata={}, meta_schema_paths=[schema], advisory=True
        ).analyze()
        assert result["enforcement"] == "advisory"
        # The derogation suspends the sanction, not the constatation.
        assert result["valid"] is False
        assert result["metadata_validation"]["SAISINE_URL"]["valid"] is False
        assert result["schema_sources"] == [str(schema)]

    def test_advisory_recorded_even_when_valid(self, tmp_path):
        result = MetadataAnalyzer(
            metadata={"SAISINE_URL": "https://x.example/c"},
            meta_schema_paths=[self._schema(tmp_path)],
            advisory=True,
        ).analyze()
        assert result["valid"] is True
        assert result["enforcement"] == "advisory"
