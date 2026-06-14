"""Tests for the secrets analyzer (trufflehog backend)."""

from unittest.mock import MagicMock, patch

import pytest
from json_logic import jsonLogic

from regis.analyzers.secrets import SecretsAnalyzer, _scanner_version
from regis.core.domain.context import AnalysisContext
from regis.core.domain.errors import ToolError
from regis.core.model.image_reference import ImageReference
from tests.fakes import FakeImageInspector, FakeToolRunner

_FINDINGS = [
    {
        "DetectorName": "AWS",
        "Verified": True,
        "Redacted": "AKIA...",
        "SourceMetadata": {"Data": {"Docker": {"layer": "sha256:abc"}}},
    },
    {
        "DetectorName": "Generic",
        "Verified": False,
        "Redacted": "xyz...",
        "SourceMetadata": {"Data": {"Docker": {"layer": "sha256:def"}}},
    },
]


def _secrets_ctx(tools, *, repository="library/nginx", tag="1.27"):
    return AnalysisContext(
        image=ImageReference(registry="docker.io", repository=repository, tag=tag),
        inspector=FakeImageInspector(),
        tools=tools,
    )


@pytest.fixture
def analyzer():
    return SecretsAnalyzer()


class TestSecretsAnalyzer:
    def test_default_criteria_structure(self, analyzer):
        criteria = {r["slug"]: r for r in analyzer.default_criteria()}
        assert set(criteria) == {"verified-secrets", "secret-scan"}
        assert criteria["verified-secrets"]["level"] == "critical"
        assert criteria["secret-scan"]["level"] == "warning"
        # The count threshold parameter is gone — these are pure booleans.
        assert "params" not in criteria["verified-secrets"]
        assert "params" not in criteria["secret-scan"]

    @pytest.mark.parametrize(
        "secrets_count, verified_count, verified_pass, scan_pass",
        [
            (0, 0, True, True),  # clean image: both pass
            (1, 0, True, False),  # unverified only: critical passes, warning fails
            (1, 1, False, False),  # verified secret: both fail
            (3, 2, False, False),  # several, some verified: both fail
        ],
    )
    def test_default_criteria_conditions(
        self, analyzer, secrets_count, verified_count, verified_pass, scan_pass
    ):
        criteria = {r["slug"]: r for r in analyzer.default_criteria()}
        ctx = {
            "results": {
                "secrets": {
                    "secrets_count": secrets_count,
                    "verified_count": verified_count,
                }
            }
        }
        assert (
            bool(jsonLogic(criteria["verified-secrets"]["condition"], ctx))
            is verified_pass
        )
        assert bool(jsonLogic(criteria["secret-scan"]["condition"], ctx)) is scan_pass

    def test_secrets_uses_context(self, analyzer):
        assert SecretsAnalyzer.uses_context is True

    @patch("regis.analyzers.secrets._scanner_version", return_value="3.95.3")
    def test_analyze_counts(self, _mock_ver, analyzer):
        ctx = _secrets_ctx(
            FakeToolRunner(scan_secrets=_FINDINGS),
            repository="library/alpine",
            tag="3.20",
        )
        report = analyzer.analyze(ctx)

        assert report["analyzer"] == "secrets"
        assert report["repository"] == "library/alpine"
        assert report["tag"] == "3.20"
        assert report["scanner_version"] == "3.95.3"
        assert report["secrets_count"] == 2
        assert report["verified_count"] == 1
        assert report["findings"][0]["layer"] == "sha256:abc"
        assert report["findings"][0]["DetectorName"] == "AWS"
        assert report["findings"][0]["Verified"] is True
        assert report["findings"][0]["Redacted"] == "AKIA..."
        analyzer.validate(report)

    @patch("regis.analyzers.secrets._scanner_version", return_value="3.95.3")
    def test_analyze_no_secrets(self, _mock_ver, analyzer):
        ctx = _secrets_ctx(
            FakeToolRunner(scan_secrets=[]), repository="repo", tag="tag"
        )
        report = analyzer.analyze(ctx)
        assert report["repository"] == "repo"
        assert report["tag"] == "tag"
        assert report["secrets_count"] == 0
        assert report["verified_count"] == 0
        assert report["findings"] == []
        analyzer.validate(report)

    def test_analyze_propagates_tool_error(self):
        class _Boom(FakeToolRunner):
            def scan_secrets(self, image):
                raise ToolError("trufflehog down")

        with pytest.raises(ToolError, match="trufflehog down"):
            SecretsAnalyzer().analyze(_secrets_ctx(_Boom()))


class TestScannerVersion:
    @patch("regis.analyzers.secrets.shutil.which", return_value=None)
    def test_missing_binary_returns_unknown(self, _mock_which):
        assert _scanner_version() == "unknown"

    @patch(
        "regis.analyzers.secrets.shutil.which", return_value="/usr/local/bin/trufflehog"
    )
    @patch("regis.analyzers.secrets.subprocess.run")
    def test_parses_first_line_from_stderr(self, mock_run, _mock_which):
        mock_run.return_value = MagicMock(stderr="trufflehog 3.95.3\n", stdout="")
        assert _scanner_version() == "trufflehog 3.95.3"

    @patch(
        "regis.analyzers.secrets.shutil.which", return_value="/usr/local/bin/trufflehog"
    )
    @patch("regis.analyzers.secrets.subprocess.run")
    def test_falls_back_to_stdout_when_no_stderr(self, mock_run, _mock_which):
        mock_run.return_value = MagicMock(stderr="", stdout="trufflehog 3.95.3\n")
        assert _scanner_version() == "trufflehog 3.95.3"

    @patch(
        "regis.analyzers.secrets.shutil.which", return_value="/usr/local/bin/trufflehog"
    )
    @patch("regis.analyzers.secrets.subprocess.run")
    def test_empty_output_returns_unknown(self, mock_run, _mock_which):
        mock_run.return_value = MagicMock(stderr="", stdout="")
        assert _scanner_version() == "unknown"

    @patch(
        "regis.analyzers.secrets.shutil.which", return_value="/usr/local/bin/trufflehog"
    )
    @patch(
        "regis.analyzers.secrets.subprocess.run",
        side_effect=__import__("subprocess").TimeoutExpired("trufflehog", 5),
    )
    def test_timeout_returns_unknown(self, _mock_run, _mock_which):
        assert _scanner_version() == "unknown"
