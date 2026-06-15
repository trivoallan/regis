"""Tests for the freshness analyzer."""

from regis.analyzers.freshness import FreshnessAnalyzer

from .fakes import FakeImageInspector, make_ctx


class TestFreshnessAnalyzer:
    def test_with_created_date(self):
        # tag "1.0.0" → sha256:t (created 2025-01-01)
        # "latest"   → sha256:l (created 2025-01-02)
        inspector = FakeImageInspector(
            manifests={
                "1.0.0": {"mediaType": "single", "config": {"digest": "sha256:t"}},
                "latest": {"mediaType": "single", "config": {"digest": "sha256:l"}},
            },
            blobs={
                "sha256:t": {"created": "2025-01-01T00:00:00Z"},
                "sha256:l": {"created": "2025-01-02T00:00:00Z"},
            },
        )
        ctx = make_ctx(inspector=inspector, repository="library/test", tag="1.0.0")
        analyzer = FreshnessAnalyzer()
        report = analyzer.analyze(ctx)
        analyzer.validate(report)

        assert report["tag_created"] == "2025-01-01T00:00:00Z"
        assert report["latest_created"] == "2025-01-02T00:00:00Z"
        assert report["age_days"] is not None
        assert report["behind_latest_days"] == 1
        assert report["is_latest"] is False
