import json
from unittest.mock import MagicMock, patch

import pytest

from regis_cli.analyzers.base import AnalyzerError
from regis_cli.analyzers.dockle import DockleAnalyzer


class TestDockleAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return DockleAnalyzer()

    def test_dockle_logic(self, analyzer):
        cl = MagicMock(registry="registry-1.docker.io", username=None, password=None)

        dockle_output = json.dumps(
            {
                "summary": {"fatal": 1, "warn": 0, "info": 0, "skip": 0, "pass": 1},
                "details": [
                    {
                        "code": "CIS-DI-0001",
                        "title": "Create a user for the container",
                        "level": "FATAL",
                        "alerts": ["Last user should not be root"],
                    }
                ],
            }
        )

        with patch(
            "subprocess.run",
            return_value=MagicMock(stdout=dockle_output, stderr="", returncode=1),
        ):
            res = analyzer.analyze(cl, "repo", "tag")
            assert res["issues_count"] == 1
            assert res["passed"] is False
            assert res["issues_by_level"]["FATAL"] == 1
            assert len(res["issues"]) == 1
            assert res["issues"][0]["code"] == "CIS-DI-0001"

    def test_dockle_pass(self, analyzer):
        cl = MagicMock(registry="reg", username="user", password="pwd")

        dockle_output = json.dumps(
            {
                "summary": {"fatal": 0, "warn": 0, "info": 0, "skip": 0, "pass": 5},
                "details": [
                    {
                        "code": "CIS-DI-0005",
                        "title": "Enable Content trust for Docker",
                        "level": "PASS",
                        "alerts": [],
                    }
                ],
            }
        )

        with patch(
            "subprocess.run",
            return_value=MagicMock(stdout=dockle_output, stderr="", returncode=0),
        ):
            res = analyzer.analyze(cl, "repo", "tag")
            assert res["passed"] is True
            assert res["issues_count"] == 0
            assert res["issues_by_level"]["PASS"] == 1

    def test_dockle_errors(self, analyzer):
        cl = MagicMock(registry="reg")

        # Command failure completely
        with patch("subprocess.run", side_effect=Exception("binary missing")):
            with pytest.raises(AnalyzerError, match="Dockle execution failed"):
                analyzer.analyze(cl, "r", "t")

        # Empty output
        with patch("subprocess.run", return_value=MagicMock(stdout="", stderr="err")):
            with pytest.raises(AnalyzerError, match="Dockle produced no output"):
                analyzer.analyze(cl, "r", "t")

        # Invalid json output
        with patch(
            "subprocess.run", return_value=MagicMock(stdout="invalid json", stderr="")
        ):
            with pytest.raises(AnalyzerError, match="Failed to parse dockle output"):
                analyzer.analyze(cl, "r", "t")
