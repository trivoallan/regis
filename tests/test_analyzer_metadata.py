"""Tests for MetadataAnalyzer."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from regis.analyzers.metadata import MetadataAnalyzer


class TestMetadataAnalyzerWellKnownOnly:
    """Tests without a playbook meta_schema_path."""

    def test_empty_metadata_valid(self):
        analyzer = MetadataAnalyzer(metadata={})
        result = analyzer.analyze()
        assert result["analyzer"] == "metadata"
        assert result["valid"] is True
        # Schema-defined optional fields appear as null when absent
        assert result["metadata"].get("ci.platform") is None
        assert result["metadata"].get("ci.job.id") is None
        # All schema-defined fields should be valid (they're optional)
        for v in result["metadata_validation"].values():
            assert v == {"valid": True}

    def test_valid_well_known_field(self):
        analyzer = MetadataAnalyzer(metadata={"ci.platform": "github"})
        result = analyzer.analyze()
        assert result["valid"] is True
        assert result["metadata"]["ci.platform"] == "github"
        assert result["metadata_validation"]["ci.platform"] == {"valid": True}

    def test_invalid_well_known_enum_value(self):
        analyzer = MetadataAnalyzer(metadata={"ci.platform": "bitbucket"})
        result = analyzer.analyze()
        assert result["valid"] is False
        assert result["metadata_validation"]["ci.platform"]["valid"] is False
        assert "error" in result["metadata_validation"]["ci.platform"]

    def test_optional_field_absent_appears_as_null(self):
        analyzer = MetadataAnalyzer(metadata={})
        result = analyzer.analyze()
        # Optional schema-defined fields absent from input appear as null in metadata
        assert result["metadata"].get("ci.platform") is None
        assert result["metadata_validation"].get("ci.platform") == {"valid": True}

    def test_unknown_keys_passthrough_in_metadata_not_in_validation(self):
        analyzer = MetadataAnalyzer(
            metadata={"custom.key": "value", "ci.platform": "github"}
        )
        result = analyzer.analyze()
        assert result["valid"] is True
        assert result["metadata"]["custom.key"] == "value"
        assert "custom.key" not in result["metadata_validation"]
        assert "ci.platform" in result["metadata_validation"]

    def test_analyze_ignores_positional_args(self):
        """analyze() should work when called with client/repo/tag args (BaseAnalyzer compat)."""
        analyzer = MetadataAnalyzer(metadata={"ci.job.id": "123"})
        client = MagicMock()
        result = analyzer.analyze(client, "repo/name", "latest", "linux/amd64")
        assert result["valid"] is True
        assert result["metadata"]["ci.job.id"] == "123"

    def test_validate_is_noop(self):
        """validate() should not raise."""
        analyzer = MetadataAnalyzer(metadata={})
        analyzer.validate({})  # should not raise


class TestMetadataAnalyzerWithPlaybookSchema:
    """Tests with a custom playbook meta_schema_path."""

    def _write_schema(self, tmp_path: Path, schema: dict) -> Path:
        p = tmp_path / "meta.schema.json"
        p.write_text(json.dumps(schema))
        return p

    def test_required_field_present(self, tmp_path):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["PROJECT_ID"],
            "properties": {
                "PROJECT_ID": {"type": "string"},
            },
        }
        schema_path = self._write_schema(tmp_path, schema)
        analyzer = MetadataAnalyzer(
            metadata={"PROJECT_ID": "PROJ-42"},
            meta_schema_path=schema_path,
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
            "properties": {
                "PROJECT_ID": {"type": "string"},
            },
        }
        schema_path = self._write_schema(tmp_path, schema)
        analyzer = MetadataAnalyzer(
            metadata={},
            meta_schema_path=schema_path,
        )
        result = analyzer.analyze()
        assert result["valid"] is False
        # PROJECT_ID should appear as null in metadata
        assert result["metadata"].get("PROJECT_ID") is None
        # And it should be reported as invalid
        assert result["metadata_validation"]["PROJECT_ID"]["valid"] is False
        assert "error" in result["metadata_validation"]["PROJECT_ID"]

    def test_required_field_wrong_type(self, tmp_path):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["PROJECT_ID"],
            "properties": {
                "PROJECT_ID": {"type": "string"},
            },
        }
        schema_path = self._write_schema(tmp_path, schema)
        analyzer = MetadataAnalyzer(
            metadata={"PROJECT_ID": 42},  # int instead of str
            meta_schema_path=schema_path,
        )
        result = analyzer.analyze()
        assert result["valid"] is False
        assert result["metadata_validation"]["PROJECT_ID"]["valid"] is False

    def test_optional_field_absent_appears_as_null(self, tmp_path):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "ci.platform": {"type": "string"},
                "OPTIONAL_FIELD": {"type": "string"},
            },
        }
        schema_path = self._write_schema(tmp_path, schema)
        analyzer = MetadataAnalyzer(
            metadata={},
            meta_schema_path=schema_path,
        )
        result = analyzer.analyze()
        assert result["valid"] is True
        assert result["metadata"].get("OPTIONAL_FIELD") is None
        assert (
            result["metadata_validation"].get("OPTIONAL_FIELD", {}).get("valid") is True
        )

    def test_nonexistent_schema_path_falls_back_to_well_known(self, tmp_path):
        nonexistent = tmp_path / "does_not_exist.json"
        analyzer = MetadataAnalyzer(
            metadata={"ci.platform": "github"},
            meta_schema_path=nonexistent,
        )
        result = analyzer.analyze()
        assert result["valid"] is True

    def test_combined_well_known_and_playbook_fields(self, tmp_path):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["PROJECT_ID"],
            "properties": {
                "PROJECT_ID": {"type": "string"},
            },
        }
        schema_path = self._write_schema(tmp_path, schema)
        analyzer = MetadataAnalyzer(
            metadata={"PROJECT_ID": "PROJ-1", "ci.platform": "gitlab"},
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
        # Schema-defined optional fields appear as null (no user-supplied values)
        assert result["metadata"].get("ci.platform") is None
