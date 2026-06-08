"""Tests for MetadataAnalyzer (nested well-known schema + format checking)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from regis.analyzers.metadata import MetadataAnalyzer


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
        client = MagicMock()
        result = analyzer.analyze(client, "repo/name", "latest", "linux/amd64")
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
            metadata={"PROJECT_ID": "PROJ-42"}, meta_schema_path=schema_path
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
        analyzer = MetadataAnalyzer(metadata={}, meta_schema_path=schema_path)
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
            metadata={"PROJECT_ID": 42}, meta_schema_path=schema_path
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
        analyzer = MetadataAnalyzer(metadata={}, meta_schema_path=schema_path)
        result = analyzer.analyze()
        assert result["valid"] is True
        assert "OPTIONAL_FIELD" not in result["metadata"]
        assert result["metadata_validation"]["OPTIONAL_FIELD"] == {"valid": True}

    def test_nonexistent_schema_path_falls_back_to_well_known(self, tmp_path):
        nonexistent = tmp_path / "does_not_exist.json"
        analyzer = MetadataAnalyzer(
            metadata={"ci": {"platform": "github"}}, meta_schema_path=nonexistent
        )
        result = analyzer.analyze()
        assert result["valid"] is True

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
            meta_schema_path=schema_path,
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
            metadata={"FIELD_A": "present"}, meta_schema_path=schema_path
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
            metadata={"KNOWN": "ok", "SURPRISE": "x"}, meta_schema_path=schema_path
        )
        result = analyzer.analyze()
        assert result["valid"] is False
        # The structural error is recorded (not silently dropped).
        invalid = [
            k for k, v in result["metadata_validation"].items() if not v["valid"]
        ]
        assert invalid, "expected at least one invalid entry for the structural error"
