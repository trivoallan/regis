"""Tests for the freshness analyzer."""

import json
from unittest.mock import patch

from regis_cli.analyzers.freshness import FreshnessAnalyzer


class MockRegistryClient:
    def __init__(self):
        self.registry = "registry-1.docker.io"
        self.username = None
        self.password = None


class TestFreshnessAnalyzer:
    @patch("regis_cli.analyzers.freshness.subprocess.run")
    def test_with_created_date(self, mock_run):
        def side_effect(cmd, **kwargs):
            class MockResponse:
                def __init__(self, stdout):
                    self.stdout = stdout

            target = cmd[-1]
            if "latest" in target:
                return MockResponse(json.dumps({"created": "2025-01-02T00:00:00Z"}))
            else:
                return MockResponse(json.dumps({"created": "2025-01-01T00:00:00Z"}))

        mock_run.side_effect = side_effect
        client = MockRegistryClient()
        analyzer = FreshnessAnalyzer()
        report = analyzer.analyze(client, "library/test", "1.0.0")
        analyzer.validate(report)

        assert report["tag_created"] == "2025-01-01T00:00:00Z"
        assert report["latest_created"] == "2025-01-02T00:00:00Z"
        assert report["age_days"] is not None
        assert report["behind_latest_days"] == 1
        assert report["is_latest"] is False
