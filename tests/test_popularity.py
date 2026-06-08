"""Tests for the popularity analyzer."""

import os
from unittest.mock import MagicMock, patch

import pytest

from regis.analyzers.popularity import PopularityAnalyzer


class MockRegistryClient:
    def list_tags(self):
        return []

    def get_manifest(self, tag):
        return {}

    def get_blob(self, digest):
        return {}


class TestPopularityAnalyzer:
    def test_official_image(self):
        """Docker Hub stats are parsed for an official image (mocked response)."""
        client = MockRegistryClient()
        analyzer = PopularityAnalyzer()
        with patch("requests.get") as m:
            m.return_value = MagicMock(status_code=200)
            m.return_value.json.return_value = {
                "pull_count": 1_000_000_000,
                "star_count": 19000,
                "description": "Official build of Nginx.",
                "last_updated": "2026-01-01T00:00:00Z",
                "date_registered": "2014-06-05T00:00:00Z",
            }
            report = analyzer.analyze(client, "library/nginx", "latest")
        analyzer.validate(report)

        assert report["available"] is True
        assert report["is_official"] is True
        assert report["pull_count"] > 0
        assert report["star_count"] > 0

    def test_nonexistent_image(self):
        """A 404 from Docker Hub yields an unavailable report (mocked response)."""
        client = MockRegistryClient()
        analyzer = PopularityAnalyzer()
        with patch("requests.get") as m:
            m.return_value = MagicMock(status_code=404)
            report = analyzer.analyze(client, "fakens/nonexistent-xyz", "latest")
        analyzer.validate(report)

        assert report["available"] is False
        assert report["is_official"] is False

    def test_request_failure_is_handled(self):
        """A network exception yields an unavailable report, never raising."""
        client = MockRegistryClient()
        analyzer = PopularityAnalyzer()
        with patch("requests.get", side_effect=Exception("network down")):
            report = analyzer.analyze(client, "library/nginx", "latest")
        analyzer.validate(report)

        assert report["available"] is False
        assert report["is_official"] is True

    @pytest.mark.skipif(
        os.environ.get("REGIS_LIVE_TESTS") != "1",
        reason="Live Docker Hub test; set REGIS_LIVE_TESTS=1 to run.",
    )
    def test_official_image_live(self):
        """Opt-in live test — hits Docker Hub for library/nginx."""
        client = MockRegistryClient()
        analyzer = PopularityAnalyzer()
        report = analyzer.analyze(client, "library/nginx", "latest")
        analyzer.validate(report)

        assert report["available"] is True
        assert report["pull_count"] > 0
        assert report["star_count"] > 0
