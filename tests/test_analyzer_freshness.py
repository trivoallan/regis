import json
from unittest.mock import MagicMock, patch

import pytest

from regis.analyzers.base import AnalyzerError
from regis.analyzers.freshness import FreshnessAnalyzer, _get_created_date


class TestFreshnessAnalyzer:
    @pytest.fixture
    def client(self):
        m = MagicMock()
        m.registry = "example.com"
        m.username = "user"
        m.password = "pass"
        return m

    @patch("regis.analyzers.freshness.run_regctl")
    def test_get_created_date_creds(self, mock_regctl, client):
        mock_regctl.return_value = json.dumps({"created": "2024-01-01T00:00:00Z"})
        date = _get_created_date(client, "repo", "tag")
        assert date == "2024-01-01T00:00:00Z"
        # Verify run_regctl was called with the expected args
        call_args = mock_regctl.call_args[0]
        regctl_args = call_args[1]
        assert regctl_args[0] == "image"
        assert regctl_args[1] == "inspect"
        assert "--platform" in regctl_args

    @patch("regis.analyzers.freshness.run_regctl")
    def test_get_created_date_failure(self, mock_regctl, client):
        # Hit exception block
        mock_regctl.side_effect = AnalyzerError("boom")
        date = _get_created_date(client, "repo", "tag")
        assert date is None

    @patch("regis.analyzers.freshness._get_created_date")
    def test_analyze_datetime_errors(self, mock_get_date):
        # Hit datetime parse errors (line 80-81, 92-93)
        # First call: current tag, Second call: latest tag
        mock_get_date.side_effect = ["invalid-date", "2024-01-01T00:00:00Z"]
        analyzer = FreshnessAnalyzer()
        report = analyzer.analyze(MagicMock(), "repo", "tag")
        assert report["age_days"] is None
        assert report["behind_latest_days"] is None

    @patch("regis.analyzers.freshness._get_created_date")
    def test_analyze_negative_behind(self, mock_get_date):
        # Hit negative behind_days (line 91)
        # Current is NEWER than latest (maybe latest repo is stale)
        mock_get_date.side_effect = ["2024-02-01T00:00:00Z", "2024-01-01T00:00:00Z"]
        analyzer = FreshnessAnalyzer()
        report = analyzer.analyze(MagicMock(), "repo", "tag")
        assert report["behind_latest_days"] == 0
        assert report["is_latest"] is True
