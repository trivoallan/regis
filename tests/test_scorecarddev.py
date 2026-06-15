"""Tests for the scorecard analyzer."""

from regis.analyzers.scorecarddev import (
    ScorecardDevAnalyzer,
    _parse_git_url,
)
from regis.core.domain.context import AnalysisContext
from regis.core.model.image_reference import ImageReference
from tests.fakes import FakeImageInspector, FakeToolRunner


def _ctx(inspector, *, repository="library/nginx", tag="latest"):
    return AnalysisContext(
        image=ImageReference(registry="docker.io", repository=repository, tag=tag),
        inspector=inspector,
        tools=FakeToolRunner(),
    )


# ---------------------------------------------------------------------------
# Git URL parsing tests
# ---------------------------------------------------------------------------


class TestParseGitUrl:
    """Test git URL parsing."""

    def test_github_https(self):
        result = _parse_git_url("https://github.com/nginx/docker-nginx")
        assert result == ("github.com", "nginx", "docker-nginx")

    def test_github_no_scheme(self):
        result = _parse_git_url("github.com/nginxinc/docker-nginx")
        assert result == ("github.com", "nginxinc", "docker-nginx")

    def test_gitlab(self):
        result = _parse_git_url("https://gitlab.com/myorg/myrepo")
        assert result == ("gitlab.com", "myorg", "myrepo")

    def test_with_trailing_git(self):
        result = _parse_git_url("https://github.com/nginx/docker-nginx.git")
        assert result == ("github.com", "nginx", "docker-nginx")

    def test_invalid_url(self):
        result = _parse_git_url("https://example.com/not-a-repo")
        assert result is None


# ---------------------------------------------------------------------------
# Mock client
# ---------------------------------------------------------------------------


class MockRegistryClient:
    """Minimal mock for RegistryClient."""

    def __init__(self, manifest=None, blobs=None):
        self._manifest = manifest or {}
        self._blobs = blobs or {}

    def list_tags(self):
        return []

    def get_manifest(self, tag):
        if tag.startswith("sha256:"):
            return self._blobs.get(f"manifest:{tag}", self._manifest)
        return self._manifest

    def get_blob(self, digest):
        return self._blobs.get(digest, {})


# ---------------------------------------------------------------------------
# Analyzer tests with mocked data
# ---------------------------------------------------------------------------


class TestScorecardAnalyzerNoSource:
    """Test behavior when source repo cannot be resolved."""

    def test_no_source_repo(self):
        """When no labels and no Docker Hub info, report scorecard_available=False."""
        manifest = {
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "config": {"digest": "sha256:cfg1"},
            "layers": [],
        }
        config = {
            "config": {"Labels": {}},
        }
        inspector = MockRegistryClient(
            manifest=manifest,
            blobs={"sha256:cfg1": config},
        )
        analyzer = ScorecardDevAnalyzer()
        report = analyzer.analyze(
            _ctx(inspector, repository="fakens/nonexistent-image-xyz", tag="latest")
        )
        analyzer.validate(report)

        assert report["analyzer"] == "scorecarddev"
        assert report["scorecard_available"] is False
        assert report["source_repo"] is None
        assert report["score"] is None
        assert report["checks"] == []


class TestScorecardAnalyzerWithSource:
    """Test that source repo is resolved from labels."""

    def test_extracts_source_from_labels(self):
        """Verify that the analyzer extracts source_repo from OCI labels."""
        manifest = {
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "config": {"digest": "sha256:cfg1"},
            "layers": [],
        }
        config = {
            "config": {
                "Labels": {
                    "org.opencontainers.image.source": "https://github.com/nginx/docker-nginx",
                }
            },
        }
        inspector = MockRegistryClient(
            manifest=manifest,
            blobs={"sha256:cfg1": config},
        )
        analyzer = ScorecardDevAnalyzer()
        report = analyzer.analyze(
            _ctx(inspector, repository="library/nginx", tag="latest")
        )
        analyzer.validate(report)

        assert report["source_repo"] == "https://github.com/nginx/docker-nginx"
        # scorecard_available depends on the actual API call, which may succeed
        # or fail in tests — we just verify the report schema is valid.


# ---------------------------------------------------------------------------
# Source metadata tests
# ---------------------------------------------------------------------------


def test_scorecard_source_extracted_from_raw(monkeypatch):
    """Success path: source block is populated from the raw API response."""
    from regis.analyzers import scorecarddev as mod

    raw = {
        "date": "2026-06-01T00:00:00Z",
        "scorecard": {"version": "v5.0.0"},
        "score": 7.5,
        "checks": [],
    }
    monkeypatch.setattr(mod, "_fetch_scorecard", lambda *a, **k: raw)
    monkeypatch.setattr(
        mod,
        "_resolve_source_repo",
        lambda *a, **k: "https://github.com/owner/repo",
    )

    analyzer = mod.ScorecardDevAnalyzer()
    result = analyzer.analyze(
        _ctx(FakeImageInspector(), repository="library/nginx", tag="latest")
    )

    assert result["scorecard_available"] is True
    assert result["source"]["built_at"] == "2026-06-01T00:00:00Z"
    assert result["source"]["version"] == "v5.0.0"
    assert isinstance(result["source"]["fetched_at"], str)


