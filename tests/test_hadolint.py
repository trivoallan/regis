"""Tests for the hadolint analyzer."""

import json
from unittest.mock import MagicMock, patch

from regis_cli.analyzers.hadolint import HadolintAnalyzer


class MockRegistryClient:
    def __init__(self, username=None, password=None):
        self.registry = "registry-1.docker.io"
        self.username = username
        self.password = password


class TestHadolintAnalyzer:
    @patch("regis_cli.analyzers.hadolint.subprocess.run")
    def test_hadolint_passes(self, mock_run):
        # We need two mock returns for the two subprocess.run calls
        # 1. skopeo inspect
        # 2. hadolint

        def side_effect(cmd, **kwargs):
            if cmd[0] == "skopeo":
                return MagicMock(
                    stdout=json.dumps(
                        {
                            "history": [
                                {"created_by": '/bin/sh -c #(nop)  CMD ["python3"]'},
                                {"created_by": "bazel build //common:rootfs"},
                            ]
                        }
                    )
                )
            elif cmd[0] == "hadolint":
                # Returns empty array for no violations
                return MagicMock(stdout="[]")

        mock_run.side_effect = side_effect

        client = MockRegistryClient()
        analyzer = HadolintAnalyzer()
        report = analyzer.analyze(client, "library/python", "latest")

        analyzer.validate(report)
        assert report["passed"] is True
        assert report["issues_count"] == 0
        assert report["issues_by_level"]["error"] == 0
        assert report["issues_by_level"]["warning"] == 0

    @patch("regis_cli.analyzers.hadolint.subprocess.run")
    def test_hadolint_fails(self, mock_run):
        def side_effect(cmd, **kwargs):
            if cmd[0] == "skopeo":
                return MagicMock(
                    stdout=json.dumps(
                        {
                            "history": [
                                {"created_by": "apt-get install curl"},
                            ]
                        }
                    )
                )
            elif cmd[0] == "hadolint":
                # Returns 1 violation (DL3008 for apt-get)
                # Note: `kwargs.get('input')` can be checked if we want to assert the drafted Dockerfile
                return MagicMock(
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

        mock_run.side_effect = side_effect

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
