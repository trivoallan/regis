import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from regis_cli.analyzers.freshness import FreshnessAnalyzer, _get_created_date


class TestFreshnessAnalyzer:
    @pytest.fixture
    def client(self):
        m = MagicMock()
        m.registry = "example.com"
        m.username = "user"
        m.password = "pass"
        return m

    @patch("regis_cli.analyzers.freshness.subprocess.run")
    def test_get_created_date_creds(self, mock_run, client):
        mock_run.return_value = MagicMock(
            stdout=json.dumps({"created": "2024-01-01T00:00:00Z"}),
            check_returncode=lambda: None,
        )
        date = _get_created_date(client, "repo", "tag")
        assert date == "2024-01-01T00:00:00Z"
        # Verify creds were used (hit line 34)
        args = mock_run.call_args[0][0]
        assert "--creds" in args
        assert "user:pass" in args

    @patch("regis_cli.analyzers.freshness.subprocess.run")
    def test_get_created_date_failure(self, mock_run, client):
        # Hit exception block (line 45-47)
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        date = _get_created_date(client, "repo", "tag")
        assert date is None

    @patch("regis_cli.analyzers.freshness._get_created_date")
    def test_analyze_datetime_errors(self, mock_get_date):
        # Hit datetime parse errors (line 80-81, 92-93)
        # First call: current tag, Second call: latest tag
        mock_get_date.side_effect = ["invalid-date", "2024-01-01T00:00:00Z"]
        analyzer = FreshnessAnalyzer()
        report = analyzer.analyze(MagicMock(), "repo", "tag")
        assert report["age_days"] is None
        assert report["behind_latest_days"] is None

    @patch("regis_cli.analyzers.freshness._get_created_date")
    def test_analyze_negative_behind(self, mock_get_date):
        # Hit negative behind_days (line 91)
        # Current is NEWER than latest (maybe latest repo is stale)
        mock_get_date.side_effect = ["2024-02-01T00:00:00Z", "2024-01-01T00:00:00Z"]
        analyzer = FreshnessAnalyzer()
        report = analyzer.analyze(MagicMock(), "repo", "tag")
        assert report["behind_latest_days"] == 0
        assert report["is_latest"] is True
