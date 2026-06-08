"""Tests for the hadolint analyzer."""

import json
from unittest.mock import MagicMock, patch

from regis.analyzers.hadolint import HadolintAnalyzer


class MockRegistryClient:
    def __init__(self, username=None, password=None):
        self.registry = "registry-1.docker.io"
        self.username = username
        self.password = password


class TestHadolintAnalyzer:
    @patch("regis.analyzers.hadolint.ensure_tool", return_value="/usr/bin/hadolint")
    @patch("regis.analyzers.hadolint.subprocess.run")
    @patch("regis.analyzers.hadolint.run_regctl")
    def test_hadolint_passes(self, mock_regctl, mock_run, mock_ensure_tool):
        # The config fetch goes through regctl; the linter stays on subprocess.run.
        mock_regctl.return_value = json.dumps(
            {
                "history": [
                    {"created_by": '/bin/sh -c #(nop)  CMD ["python3"]'},
                    {"created_by": "bazel build //common:rootfs"},
                ]
            }
        )
        # Hadolint linter returns an empty array for no violations.
        mock_run.return_value = MagicMock(stdout="[]")

        client = MockRegistryClient()
        analyzer = HadolintAnalyzer()
        report = analyzer.analyze(client, "library/python", "latest")

        analyzer.validate(report)
        assert report["passed"] is True
        assert report["issues_count"] == 0
        assert report["issues_by_level"]["error"] == 0
        assert report["issues_by_level"]["warning"] == 0

    @patch("regis.analyzers.hadolint.ensure_tool", return_value="/usr/bin/hadolint")
    @patch("regis.analyzers.hadolint.subprocess.run")
    @patch("regis.analyzers.hadolint.run_regctl")
    def test_hadolint_fails(self, mock_regctl, mock_run, mock_ensure_tool):
        mock_regctl.return_value = json.dumps(
            {
                "history": [
                    {"created_by": "apt-get install curl"},
                ]
            }
        )
        # Hadolint linter returns 1 violation (DL3008 for apt-get).
        mock_run.return_value = MagicMock(
            stdout=json.dumps(
                [
                    {
                        "code": "DL3008",
                        "column": 1,
                        "file": "-",
                        "level": "warning",
                        "line": 2,
                        "message": "Pin versions in apt get install.",
                    }
                ]
            )
        )

        client = MockRegistryClient()
        analyzer = HadolintAnalyzer()
        report = analyzer.analyze(client, "library/python", "latest")

        analyzer.validate(report)
        assert report["passed"] is False
        assert report["issues_count"] == 1
        assert report["issues_by_level"]["warning"] == 1
        assert report["issues_by_level"]["error"] == 0
        assert report["issues"][0]["code"] == "DL3008"
        assert report["issues"][0]["level"] == "warning"
