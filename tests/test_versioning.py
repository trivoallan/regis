import json
from unittest.mock import MagicMock, patch

import pytest

from regis_cli.analyzers.versioning import VersioningAnalyzer, _classify_tag

# ---------------------------------------------------------------------------
# Tag classification unit tests
# ---------------------------------------------------------------------------


class TestClassifyTag:
    """Test individual tag classification."""

    @pytest.mark.parametrize(
        "tag,expected",
        [
            ("1.0.0", "semver"),
            ("v1.0.0", "semver"),
            ("2.4.1", "semver"),
            ("0.1.0", "semver"),
        ],
    )
    def test_semver(self, tag, expected):
        assert _classify_tag(tag) == expected

    @pytest.mark.parametrize(
        "tag,expected",
        [
            ("1.0.0-alpha", "semver-prerelease"),
            ("v2.0.0-rc.1", "semver-prerelease"),
            ("1.0.0-beta.2", "semver-prerelease"),
        ],
    )
    def test_semver_prerelease(self, tag, expected):
        assert _classify_tag(tag) == expected

    @pytest.mark.parametrize(
        "tag,expected",
        [
            ("1.88.0-alpine", "semver-variant"),
            ("1.88.0-slim-bookworm", "semver-variant"),
            ("v2.0.0-bullseye", "semver-variant"),
            ("1.91.0-alpine3.21", "semver-variant"),
            ("1.0.0-slim", "semver-variant"),
            ("1.0.0-slim-trixie", "semver-variant"),
        ],
    )
    def test_semver_variant(self, tag, expected):
        assert _classify_tag(tag) == expected

    @pytest.mark.parametrize(
        "tag,expected",
        [
            ("2024.01", "calver"),
            ("2024.12.25", "calver"),
            ("v2024.06", "calver"),
        ],
    )
    def test_calver(self, tag, expected):
        assert _classify_tag(tag) == expected

    @pytest.mark.parametrize(
        "tag,expected",
        [
            ("1", "numeric"),
            ("1.2", "numeric"),
            ("v8", "numeric"),
            ("1.27.4.1", "numeric"),
        ],
    )
    def test_numeric(self, tag, expected):
        assert _classify_tag(tag) == expected

    @pytest.mark.parametrize(
        "tag,expected",
        [
            ("abc1234", "hash"),
            ("deadbeef", "hash"),
            ("a1b2c3d4e5f6", "hash"),
        ],
    )
    def test_hash(self, tag, expected):
        assert _classify_tag(tag) == expected

    @pytest.mark.parametrize(
        "tag,expected",
        [
            ("latest", "named"),
            ("alpine", "named"),
            ("bookworm-slim", "named"),
            ("1-alpine", "named"),
        ],
    )
    def test_named(self, tag, expected):
        assert _classify_tag(tag) == expected


# ---------------------------------------------------------------------------
# Mock client
# ---------------------------------------------------------------------------


class MockRegistryClient:
    """Minimal mock for RegistryClient."""

    def __init__(self):
        self.registry = "registry-1.docker.io"
        self.username = None
        self.password = None


# ---------------------------------------------------------------------------
# Full analyzer tests
# ---------------------------------------------------------------------------


class TestVersioningAnalyzer:
    """Test the versioning analyzer end-to-end."""

    @patch("regis_cli.analyzers.versioning.subprocess.run")
    def test_semver_dominant(self, mock_run):
        tags = ["1.0.0", "1.1.0", "1.2.0", "2.0.0", "2.0.0-rc.1", "latest"]
        mock_run.return_value.stdout = json.dumps({"Tags": tags})
        client = MockRegistryClient()
        analyzer = VersioningAnalyzer()
        report = analyzer.analyze(client, "library/myapp", "latest")
        analyzer.validate(report)

        assert report["dominant_pattern"] == "semver"
        assert report["total_tags"] == 6
        # 4 semver + 1 prerelease = 5/6 ≈ 83.3%
        assert report["semver_compliant_percentage"] == pytest.approx(83.3, abs=0.1)

    @patch("regis_cli.analyzers.versioning.subprocess.run")
    def test_named_dominant(self, mock_run):
        tags = ["latest", "alpine", "bookworm", "slim"]
        mock_run.return_value.stdout = json.dumps({"Tags": tags})
        client = MockRegistryClient()
        analyzer = VersioningAnalyzer()
        report = analyzer.analyze(client, "library/python", "latest")
        analyzer.validate(report)

        assert report["dominant_pattern"] == "named"
        assert report["semver_compliant_percentage"] == 0

    @patch("regis_cli.analyzers.versioning.subprocess.run")
    def test_mixed_patterns(self, mock_run):
        tags = ["1.0.0", "1.1.0", "latest", "alpine", "2024.01", "abc1234"]
        mock_run.return_value.stdout = json.dumps({"Tags": tags})
        client = MockRegistryClient()
        analyzer = VersioningAnalyzer()
        report = analyzer.analyze(client, "test/app", "latest")
        analyzer.validate(report)

        pattern_names = {p["pattern"] for p in report["patterns"]}
        assert "semver" in pattern_names
        assert "named" in pattern_names
        assert "calver" in pattern_names
        assert "hash" in pattern_names

    @patch("regis_cli.analyzers.versioning.subprocess.run")
    def test_empty_tags(self, mock_run):
        mock_run.return_value.stdout = json.dumps({"Tags": []})
        client = MockRegistryClient()
        analyzer = VersioningAnalyzer()
        report = analyzer.analyze(client, "test/empty", "latest")
        analyzer.validate(report)

        assert report["total_tags"] == 0
        assert report["dominant_pattern"] == "unknown"
        assert report["patterns"] == []

    @patch("regis_cli.analyzers.versioning.subprocess.run")
    def test_variant_detection(self, mock_run):
        """Test detection and counting of variants."""
        tags = [
            "1.0.0-alpine",
            "1.0.1-alpine",
            "1.0.1-alpine3.18",
            "1.0.2-slim",
            "1.0.3-slim-bookworm",
            "latest",
        ]
        mock_run.return_value.stdout = json.dumps({"Tags": tags})
        client = MockRegistryClient()
        analyzer = VersioningAnalyzer()
        report = analyzer.analyze(client, "library/test", "latest")
        analyzer.validate(report)

        variants = report["variants"]
        assert len(variants) > 0

        v_map = {v["name"]: v["count"] for v in variants}
        assert v_map["alpine"] == 2
        assert v_map["slim"] == 2
        assert v_map["alpine3.18"] == 1
        assert v_map["bookworm"] == 1

        # Check examples
        alpine_entry = next(v for v in variants if v["name"] == "alpine")
        assert "1.0.0-alpine" in alpine_entry["examples"]

    @patch("regis_cli.analyzers.versioning.subprocess.run")
    def test_subvariant_detection(self, mock_run):
        """Test detection of subvariants like cli, fpm, apache."""
        tags = [
            "8.1-fpm-alpine",
            "8.1-cli-alpine",
            "8.1-apache-buster",
            "8.1-zts-bullseye",
            "latest",
        ]
        mock_run.return_value.stdout = json.dumps({"Tags": tags})
        client = MockRegistryClient()
        analyzer = VersioningAnalyzer()
        report = analyzer.analyze(client, "library/php", "latest")
        analyzer.validate(report)

        variants = report["variants"]
        v_map = {v["name"]: v["count"] for v in variants}

        assert v_map["fpm"] == 1
        assert v_map["cli"] == 1
        assert v_map["apache"] == 1
        assert v_map["zts"] == 1
        assert v_map["alpine"] == 2
        assert v_map["buster"] == 1
        assert v_map["bullseye"] == 1

    @patch("regis_cli.analyzers.versioning.subprocess.run")
    def test_ubi_detection(self, mock_run):
        """Test detection of RedHat UBI images."""
        tags = [
            "8.5-ubi8",
            "8.5-ubi8-minimal",
            "9.0-ubi9-micro",
            "latest-ubi",
            "7-rhel",
            "8-ubi-init",
        ]
        mock_run.return_value.stdout = json.dumps({"Tags": tags})
        client = MockRegistryClient()
        analyzer = VersioningAnalyzer()
        report = analyzer.analyze(client, "library/redhat", "latest")
        analyzer.validate(report)

        variants = report["variants"]
        v_map = {v["name"]: v["count"] for v in variants}

        assert v_map["ubi8"] == 2
        assert v_map["ubi9"] == 1
        assert v_map["ubi"] == 2
        assert v_map["minimal"] == 1
        assert v_map["micro"] == 1
        assert v_map["init"] == 1
        assert v_map["rhel"] == 1

    @patch("regis_cli.analyzers.versioning.subprocess.run")
    def test_release_line_detection_for_alias(self, mock_run):
        """Test detection of release_line for alias tags."""
        # mock_run will be called twice:
        # 1. skopeo list-tags
        # 2. skopeo inspect
        mock_list_tags = MagicMock()
        mock_list_tags.stdout = json.dumps({"Tags": ["1", "1.10", "1.10.4", "latest"]})

        mock_inspect = MagicMock()
        mock_inspect.stdout = json.dumps(
            {"RepoTags": ["1", "1.10", "1.10.4", "latest"]}
        )

        mock_run.side_effect = [mock_list_tags, mock_inspect]

        client = MockRegistryClient()
        analyzer = VersioningAnalyzer()
        report = analyzer.analyze(client, "library/test", "1")
        analyzer.validate(report)

        assert "release_lines" in report
        assert report["release_lines"] == ["1", "1.10", "1.10.4"]
        assert "release_line" not in report
        assert mock_run.call_count == 2
