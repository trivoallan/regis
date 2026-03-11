# trunk-ignore-all(bandit/B101)
"""Tests for the end-of-life analyzer."""

from regis_cli.analyzers.endoflife import (
    EndOfLifeAnalyzer,
    _extract_version,
    _image_to_product,
    _match_cycle,
)

# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------


class TestImageToProduct:
    """Test Docker image → product slug mapping."""

    def test_official_nginx(self):
        assert _image_to_product("library/nginx") == "nginx"

    def test_node(self):
        assert _image_to_product("library/node") == "nodejs"

    def test_postgres(self):
        assert _image_to_product("library/postgres") == "postgresql"

    def test_unknown_image(self):
        assert _image_to_product("library/myapp") == "myapp"

    def test_user_image(self):
        assert _image_to_product("myorg/myapp") == "myapp"

    def test_golang(self):
        assert _image_to_product("library/golang") == "go"


class TestExtractVersion:
    """Test version extraction from tags."""

    def test_semver(self):
        assert _extract_version("1.27.1") == "1.27"

    def test_short(self):
        assert _extract_version("1.27") == "1.27"

    def test_with_suffix(self):
        assert _extract_version("1.27-alpine") == "1.27"

    def test_v_prefix(self):
        assert _extract_version("v3.19") == "3.19"

    def test_major_only(self):
        assert _extract_version("22") == "22"

    def test_named_tag(self):
        assert _extract_version("latest") is None

    def test_alpine_tag(self):
        assert _extract_version("alpine") is None


class TestMatchCycle:
    """Test cycle matching."""

    CYCLES = [
        {"cycle": "1.27", "eol": False, "latest": "1.27.5"},
        {"cycle": "1.26", "eol": "2025-04-23", "latest": "1.26.3"},
        {"cycle": "1.25", "eol": "2024-05-29", "latest": "1.25.5"},
    ]

    def test_exact_match(self):
        result = _match_cycle("1.27", self.CYCLES)
        assert result is not None
        assert result["cycle"] == "1.27"

    def test_major_fallback(self):
        # No cycle "1" exists but shouldn't match either — major fallback
        result = _match_cycle("1", self.CYCLES)
        assert result is None

    def test_no_match(self):
        result = _match_cycle("2.0", self.CYCLES)
        assert result is None


# ---------------------------------------------------------------------------
# Mock client
# ---------------------------------------------------------------------------


class MockRegistryClient:
    """Minimal mock for RegistryClient."""

    def list_tags(self):
        return []

    def get_manifest(self, tag):
        return {}

    def get_blob(self, digest):
        return {}


# ---------------------------------------------------------------------------
# Full analyzer tests
# ---------------------------------------------------------------------------


class TestEndOfLifeAnalyzer:
    """Test the end-of-life analyzer end-to-end (calls live API)."""

    def test_known_product(self):
        """Test with nginx which is known on endoflife.date."""
        client = MockRegistryClient()
        analyzer = EndOfLifeAnalyzer()
        report = analyzer.analyze(client, "library/nginx", "1.27")
        analyzer.validate(report)

        assert report["analyzer"] == "endoflife"
        assert report["product"] == "nginx"
        assert report["product_found"] is True
        assert report["matched_cycle"] is not None
        assert report["matched_cycle"]["cycle"] == "1.27"

    def test_unknown_product(self):
        """Test with a product not on endoflife.date."""
        client = MockRegistryClient()
        analyzer = EndOfLifeAnalyzer()
        report = analyzer.analyze(client, "library/nonexistent-xyz", "latest")
        analyzer.validate(report)

        assert report["product_found"] is False
        assert report["matched_cycle"] is None
        assert report["is_eol"] is None

    def test_named_tag_no_match(self):
        """Named tags like 'latest' cannot match a cycle."""
        client = MockRegistryClient()
        analyzer = EndOfLifeAnalyzer()
        report = analyzer.analyze(client, "library/nginx", "latest")
        analyzer.validate(report)

        assert report["product_found"] is True
        assert report["matched_cycle"] is None
        assert report["is_eol"] is None
