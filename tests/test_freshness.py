"""Tests for the freshness analyzer."""

import json
from unittest.mock import patch

from regis.analyzers.freshness import FreshnessAnalyzer


class MockRegistryClient:
    def __init__(self):
        self.registry = "registry-1.docker.io"
        self.username = None
        self.password = None


class TestFreshnessAnalyzer:
    @patch("regis.analyzers.freshness.run_regctl")
    def test_with_created_date(self, mock_regctl):
        def side_effect(client, args, *a, **k):
            ref = args[2]  # ["image", "inspect", ref, "--platform", "linux/amd64"]
            if "latest" in ref:
                return json.dumps({"created": "2025-01-02T00:00:00Z"})
            else:
                return json.dumps({"created": "2025-01-01T00:00:00Z"})

        mock_regctl.side_effect = side_effect
        client = MockRegistryClient()
        analyzer = FreshnessAnalyzer()
        report = analyzer.analyze(client, "library/test", "1.0.0")
        analyzer.validate(report)

        assert report["tag_created"] == "2025-01-01T00:00:00Z"
        assert report["latest_created"] == "2025-01-02T00:00:00Z"
        assert report["age_days"] is not None
        assert report["behind_latest_days"] == 1
        assert report["is_latest"] is False
