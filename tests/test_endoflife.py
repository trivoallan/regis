"""Tests for the end-of-life analyzer."""

from unittest.mock import MagicMock, patch

import requests

from regis.analyzers.endoflife import (
    EndOfLifeAnalyzer,
    _extract_version,
    _fetch_cycles,
    _image_to_product,
    _match_cycle,
)
from regis.core.domain.context import AnalysisContext
from regis.core.model.image_reference import ImageReference
from tests.fakes import FakeImageInspector, FakeToolRunner


def _eol_ctx(*, repository="library/nginx", tag="latest"):
    return AnalysisContext(
        image=ImageReference(registry="docker.io", repository=repository, tag=tag),
        inspector=FakeImageInspector(),
        tools=FakeToolRunner(),
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

    def test_short_name_fallback_via_org_prefix(self):
        """Short name (last path segment) resolves to a known product slug."""
        # "myorg/node" → full name not in map, short name "node" IS in map → "nodejs"
        assert _image_to_product("myorg/node") == "nodejs"


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

    def test_major_version_fallback_matches(self):
        """When exact version misses, major component matches a cycle with that id."""
        cycles = [{"cycle": "1", "eol": False, "latest": "1.5.0"}]
        result = _match_cycle("1.5", cycles)
        assert result is not None
        assert result["cycle"] == "1"


# ---------------------------------------------------------------------------
# Full analyzer tests
# ---------------------------------------------------------------------------


class TestEndOfLifeAnalyzer:
    """Test the end-of-life analyzer end-to-end (mocked API)."""

    MOCK_CYCLES = [
        {
            "cycle": "1.27",
            "releaseDate": "2024-05-28",
            "eol": "2025-06-24",
            "latest": "1.27.5",
        },
        {
            "cycle": "1.26",
            "releaseDate": "2024-04-23",
            "eol": "2025-04-23",
            "latest": "1.26.3",
        },
    ]

    @patch("regis.analyzers.endoflife._fetch_cycles")
    def test_known_product(self, mock_fetch):
        """Test with nginx which is known on endoflife.date."""
        mock_fetch.return_value = self.MOCK_CYCLES
        analyzer = EndOfLifeAnalyzer()
        report = analyzer.analyze(_eol_ctx(repository="library/nginx", tag="1.27"))
        analyzer.validate(report)

        assert report["analyzer"] == "endoflife"
        assert report["product"] == "nginx"
        assert report["product_found"] is True
        assert report["matched_cycle"] is not None
        assert report["matched_cycle"]["cycle"] == "1.27"

    @patch("regis.analyzers.endoflife._fetch_cycles")
    def test_unknown_product(self, mock_fetch):
        """Test with a product not on endoflife.date."""
        mock_fetch.return_value = None
        analyzer = EndOfLifeAnalyzer()
        report = analyzer.analyze(
            _eol_ctx(repository="library/nonexistent-xyz", tag="latest")
        )
        analyzer.validate(report)

        assert report["product_found"] is False
        assert report["matched_cycle"] is None
        assert report["is_eol"] is None

    @patch("regis.analyzers.endoflife._fetch_cycles")
    def test_named_tag_no_match(self, mock_fetch):
        """Named tags like 'latest' cannot match a cycle."""
        mock_fetch.return_value = self.MOCK_CYCLES
        analyzer = EndOfLifeAnalyzer()
        report = analyzer.analyze(_eol_ctx(repository="library/nginx", tag="latest"))
        analyzer.validate(report)

        assert report["product_found"] is True
        assert report["matched_cycle"] is None
        assert report["is_eol"] is None

    @patch("regis.analyzers.endoflife._fetch_cycles")
    def test_eol_false_is_not_eol(self, mock_fetch):
        """Cycle with eol=False → is_eol is False (not None)."""
        mock_fetch.return_value = [
            {
                "cycle": "1.27",
                "releaseDate": "2024-01-01",
                "eol": False,
                "latest": "1.27.5",
            }
        ]
        analyzer = EndOfLifeAnalyzer()
        report = analyzer.analyze(_eol_ctx(repository="library/nginx", tag="1.27"))
        analyzer.validate(report)

        assert report["product_found"] is True
        assert report["matched_cycle"] is not None
        assert report["is_eol"] is False

    @patch("regis.analyzers.endoflife._fetch_cycles")
    def test_eol_bool_true_is_eol(self, mock_fetch):
        """Cycle with eol=True (boolean) → is_eol is True."""
        mock_fetch.return_value = [
            {
                "cycle": "1.25",
                "releaseDate": "2023-01-01",
                "eol": True,
                "latest": "1.25.5",
            }
        ]
        analyzer = EndOfLifeAnalyzer()
        report = analyzer.analyze(_eol_ctx(repository="library/nginx", tag="1.25"))
        analyzer.validate(report)

        assert report["product_found"] is True
        assert report["matched_cycle"] is not None
        assert report["is_eol"] is True


# ---------------------------------------------------------------------------
# _fetch_cycles HTTP error handling
# ---------------------------------------------------------------------------


class TestFetchCycles:
    """Test _fetch_cycles HTTP error handling (patches requests.get directly)."""

    @patch("regis.analyzers.endoflife.requests.get")
    def test_200_returns_cycle_list(self, mock_get):
        """A 200 response should return the parsed JSON list."""
        cycles = [{"cycle": "1.27", "eol": False}]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = cycles
        mock_get.return_value = mock_resp

        result = _fetch_cycles("nginx")

        assert result == cycles

    @patch("regis.analyzers.endoflife.requests.get")
    def test_non_200_returns_none(self, mock_get):
        """A 404 response should return None."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        result = _fetch_cycles("nonexistent-product")

        assert result is None

    @patch("regis.analyzers.endoflife.requests.get")
    def test_request_exception_returns_none(self, mock_get):
        """A network/timeout error should return None."""
        mock_get.side_effect = requests.exceptions.ConnectionError("network error")

        result = _fetch_cycles("someproduct")

        assert result is None
