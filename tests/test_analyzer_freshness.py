"""Tests for the freshness analyzer — edge cases."""

from regis.core.domain.analyzers.freshness import FreshnessAnalyzer, _get_created_date

from .fakes import FakeImageInspector, make_ctx


class TestFreshnessAnalyzer:
    def test_get_created_date_happy_path(self):
        """_get_created_date returns the created field from the config blob."""
        inspector = FakeImageInspector(
            manifest={"mediaType": "single", "config": {"digest": "sha256:c"}},
            blob={"created": "2024-01-01T00:00:00Z"},
        )
        date = _get_created_date(inspector, "repo:tag")
        assert date == "2024-01-01T00:00:00Z"

    def test_get_created_date_failure(self):
        """_get_created_date returns None when the manifest has no config digest."""
        # A manifest with no config → get_image_config raises RegistryError → None
        inspector = FakeImageInspector(
            manifest={"mediaType": "single"},  # no "config" key
        )
        date = _get_created_date(inspector, "repo:tag")
        assert date is None

    def test_analyze_datetime_errors(self):
        """Age computation is skipped when the created value is not a valid ISO timestamp."""
        # tag "tag" → invalid date; "latest" → valid date
        inspector = FakeImageInspector(
            manifests={
                "tag": {"mediaType": "single", "config": {"digest": "sha256:t"}},
                "latest": {"mediaType": "single", "config": {"digest": "sha256:l"}},
            },
            blobs={
                "sha256:t": {"created": "invalid-date"},
                "sha256:l": {"created": "2024-01-01T00:00:00Z"},
            },
        )
        ctx = make_ctx(inspector=inspector, repository="repo", tag="tag")
        analyzer = FreshnessAnalyzer()
        report = analyzer.analyze(ctx)
        assert report["age_days"] is None
        assert report["behind_latest_days"] is None

    def test_analyze_negative_behind(self):
        """behind_latest_days is clamped to 0 when the tag is newer than latest."""
        inspector = FakeImageInspector(
            manifests={
                "tag": {"mediaType": "single", "config": {"digest": "sha256:t"}},
                "latest": {"mediaType": "single", "config": {"digest": "sha256:l"}},
            },
            blobs={
                "sha256:t": {"created": "2024-02-01T00:00:00Z"},
                "sha256:l": {"created": "2024-01-01T00:00:00Z"},
            },
        )
        ctx = make_ctx(inspector=inspector, repository="repo", tag="tag")
        analyzer = FreshnessAnalyzer()
        report = analyzer.analyze(ctx)
        assert report["behind_latest_days"] == 0
        assert report["is_latest"] is True
