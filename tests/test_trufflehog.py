"""Tests for the trufflehog subprocess wrapper."""

import base64
import json
from unittest.mock import MagicMock, patch

import pytest

from regis.analyzers.base import AnalyzerError
from regis.utils.trufflehog import run_trufflehog

# NDJSON: one finding per line, plus a blank line that must be ignored.
_NDJSON = (
    '{"DetectorName": "AWS", "Verified": true, "Redacted": "AKIA...", '
    '"SourceMetadata": {"Data": {"Docker": {"layer": "sha256:abc"}}}}\n'
    "\n"
    '{"DetectorName": "Generic", "Verified": false, "Redacted": "xyz...", '
    '"SourceMetadata": {"Data": {"Docker": {"layer": "sha256:def"}}}}\n'
)


class TestRunTrufflehog:
    @patch("regis.utils.trufflehog.shutil.which")
    def test_not_found(self, mock_which):
        mock_which.return_value = None
        with pytest.raises(AnalyzerError, match="trufflehog executable not found"):
            run_trufflehog("alpine:3.20")

    @patch("regis.utils.trufflehog.shutil.which")
    @patch("regis.utils.trufflehog.subprocess.run")
    def test_parses_ndjson_ignoring_blank_lines(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/trufflehog"
        mock_run.return_value = MagicMock(stdout=_NDJSON, returncode=0)

        findings = run_trufflehog("alpine:3.20")
        assert len(findings) == 2
        assert findings[0]["DetectorName"] == "AWS"

        args = mock_run.call_args[0][0]
        assert args[0] == "/usr/local/bin/trufflehog"
        assert "docker" in args and "--json" in args
        assert "--image" in args

    @patch("regis.utils.trufflehog.shutil.which")
    @patch("regis.utils.trufflehog.subprocess.run")
    def test_nonzero_exit_with_findings_is_not_an_error(self, mock_run, mock_which):
        # trufflehog exits non-zero (e.g. 183) when secrets are found with --fail.
        mock_which.return_value = "/usr/local/bin/trufflehog"
        mock_run.return_value = MagicMock(stdout=_NDJSON, returncode=183)
        findings = run_trufflehog("alpine:3.20")
        assert len(findings) == 2

    @patch("regis.utils.trufflehog.shutil.which")
    @patch("regis.utils.trufflehog.subprocess.run")
    def test_invalid_json_line_raises(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/trufflehog"
        mock_run.return_value = MagicMock(stdout="not-json\n", returncode=0)
        with pytest.raises(AnalyzerError, match="trufflehog produced invalid"):
            run_trufflehog("alpine:3.20")

    @patch("regis.utils.trufflehog.shutil.which")
    @patch("regis.utils.trufflehog.subprocess.run")
    def test_credentials_written_to_temp_docker_config(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/trufflehog"
        captured = {}

        def _capture(*args, **kwargs):
            # Read the temp config the wrapper created before it is cleaned up.
            cfg_dir = kwargs["env"]["DOCKER_CONFIG"]
            with open(f"{cfg_dir}/config.json", encoding="utf-8") as fh:
                captured["config"] = fh.read()
            return MagicMock(stdout="", returncode=0)

        mock_run.side_effect = _capture
        run_trufflehog("ghcr.io/acme/app:1.0", username="u", password="p")

        # Assert on the parsed structure (exact auths key + round-tripped
        # credentials), not a substring of the raw config text.
        config = json.loads(captured["config"])
        assert set(config["auths"]) == {"ghcr.io"}
        auth = config["auths"]["ghcr.io"]["auth"]
        assert base64.b64decode(auth).decode() == "u:p"
