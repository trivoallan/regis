"""Tests for the popularity analyzer."""

from regis_cli.analyzers.popularity import PopularityAnalyzer


class MockRegistryClient:
    def list_tags(self):
        return []

    def get_manifest(self, tag):
        return {}

    def get_blob(self, digest):
        return {}


class TestPopularityAnalyzer:
    def test_official_image(self):
        """Live test — Docker Hub should respond for library/nginx."""
        client = MockRegistryClient()
        analyzer = PopularityAnalyzer()
        report = analyzer.analyze(client, "library/nginx", "latest")
        analyzer.validate(report)

        assert report["available"] is True
        assert report["is_official"] is True
        assert report["pull_count"] > 0
        assert report["star_count"] > 0

    def test_nonexistent_image(self):
        client = MockRegistryClient()
        analyzer = PopularityAnalyzer()
        report = analyzer.analyze(client, "fakens/nonexistent-xyz", "latest")
        analyzer.validate(report)

        assert report["available"] is False
