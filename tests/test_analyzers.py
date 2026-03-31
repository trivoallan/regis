from unittest.mock import MagicMock, patch

import pytest

from regis.analyzers.base import AnalyzerError
from regis.analyzers.skopeo import SkopeoAnalyzer

# ---------------------------------------------------------------------------
# Fixtures — mock RegistryClient


# ---------------------------------------------------------------------------
# ImageAnalyzer


# ---------------------------------------------------------------------------
# Schema validation — negative tests
# ---------------------------------------------------------------------------


class TestDiscoverAnalyzers:
    """Tests for discover_analyzers()."""

    def test_skips_failed_entry_points(self) -> None:
        """A broken entry point is logged and skipped, not raised."""
        from regis.analyzers.discovery import discover_analyzers

        bad_ep = MagicMock()
        bad_ep.name = "broken"
        bad_ep.load.side_effect = ImportError("missing dep")

        with patch("regis.analyzers.discovery.entry_points", return_value=[bad_ep]):
            result = discover_analyzers()

        assert "broken" not in result


class TestRunCmd:
    """Tests for utils/process.run_cmd()."""

    def test_file_not_found_raises_click_exception(self) -> None:
        import click

        from regis.utils.process import run_cmd

        with patch("regis.utils.process.subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(click.ClickException, match="not found in PATH"):
                run_cmd(["nonexistent-binary", "--version"])


class TestSchemaValidation:
    """Verify that invalid reports are rejected by schema validation."""

    def test_skopeo_report_wrong_analyzer_name(self):
        analyzer = SkopeoAnalyzer()
        bad_report = {
            "analyzer": "wrong",
            "repository": "test",
            "tag": "latest",
            "platforms": [],
        }
        with pytest.raises(AnalyzerError):
            analyzer.validate(bad_report)
