# trunk-ignore-all(bandit/B101)
import pytest
import requests
import responses

from regis_cli.analyzers.popularity import PopularityAnalyzer


class TestPopularityAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return PopularityAnalyzer()

    @responses.activate
    def test_analyze_success(self, analyzer):
        responses.add(
            responses.GET,
            "https://hub.docker.com/v2/repositories/library/nginx",
            json={"pull_count": 1000, "star_count": 50, "description": "some desc"},
            status=200,
        )
        report = analyzer.analyze(None, "library/nginx", "latest")
        assert report["pull_count"] == 1000
        assert report["star_count"] == 50
        assert report["available"] is True
        assert report["is_official"] is True

    @responses.activate
    def test_analyze_not_found(self, analyzer):
        responses.add(
            responses.GET,
            "https://hub.docker.com/v2/repositories/private/repo",
            status=404,
        )
        report = analyzer.analyze(None, "private/repo", "latest")
        assert report["available"] is False
        assert report["pull_count"] is None
        assert report["is_official"] is False

    @responses.activate
    def test_analyze_timeout(self, analyzer):
        # Trigger the except Exception block (line 40-42)
        responses.add(
            responses.GET,
            "https://hub.docker.com/v2/repositories/timeout/repo",
            body=requests.exceptions.Timeout("Timeout"),
        )
        report = analyzer.analyze(None, "timeout/repo", "latest")
        assert report["available"] is False
