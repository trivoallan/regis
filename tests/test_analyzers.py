import pytest

from regis_cli.analyzers.base import AnalyzerError
from regis_cli.analyzers.skopeo import SkopeoAnalyzer

# ---------------------------------------------------------------------------
# Fixtures — mock RegistryClient


# ---------------------------------------------------------------------------
# ImageAnalyzer


# ---------------------------------------------------------------------------
# Schema validation — negative tests
# ---------------------------------------------------------------------------


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
