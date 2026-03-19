import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from regis_cli.analyzers.base import AnalyzerError
from regis_cli.analyzers.hadolint import HadolintAnalyzer


class TestHadolintAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return HadolintAnalyzer()

    def test_hadolint_logic(self, analyzer):
        cl = MagicMock(registry="registry-1.docker.io")
        # 39 (split), 41 (fallback arch), 96 (shell strip)
        inspect = json.dumps(
            {
                "history": [
                    {"created_by": '/bin/sh -c #(nop) CMD ["python3"]'},
                    {"created_by": "/bin/sh -c RUN echo 1"},
                ]
            }
        )
        hadolint = json.dumps([{"level": "warning", "message": "m"}])

        with patch(
            "subprocess.run",
            side_effect=[MagicMock(stdout=inspect), MagicMock(stdout=hadolint)],
        ):
            res = analyzer.analyze(cl, "repo", "tag", platform="linux/amd64")
            assert 'CMD ["python3"]' in res["dockerfile"]
            assert "RUN echo 1" in res["dockerfile"]

        with patch(
            "subprocess.run",
            side_effect=[MagicMock(stdout=inspect), MagicMock(stdout=hadolint)],
        ):
            res = analyzer.analyze(cl, "repo", "tag", platform="amd64")
            assert res["issues_count"] == 1

    def test_hadolint_errors_exhaustive(self, analyzer):
        cl = MagicMock(registry="reg")
        inspect = json.dumps({"history": [{"created_by": "RUN echo 1"}]})

        # 70 parse fail
        with patch("subprocess.run", return_value=MagicMock(stdout="{invalid}")):
            with pytest.raises(AnalyzerError):
                analyzer.analyze(cl, "r", "t")

        # 114-116 hadolint binary missing
        with patch(
            "subprocess.run", side_effect=[MagicMock(stdout=inspect), FileNotFoundError]
        ):
            with pytest.raises(AnalyzerError):
                analyzer.analyze(cl, "r", "t")

        # 123-126 hadolint output parsing error
        with patch(
            "subprocess.run",
            side_effect=[MagicMock(stdout=inspect), MagicMock(stdout="invalid json")],
        ):
            with pytest.raises(AnalyzerError):
                analyzer.analyze(cl, "r", "t")

        # Command failure but valid output (123-126 check=False)
        m_run = MagicMock(returncode=1, stderr="err", stdout="[]")
        with patch("subprocess.run", side_effect=[MagicMock(stdout=inspect), m_run]):
            res = analyzer.analyze(cl, "r", "t")
            assert res["issues_count"] == 0

        # Subprocess failure (66)
        with patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "s", stderr="e"),
        ):
            with pytest.raises(AnalyzerError):
                analyzer.analyze(cl, "r", "t")

        # Empty history (80)
        inspect_empty = json.dumps({"history": [{"created_by": ""}]})
        with patch(
            "subprocess.run",
            side_effect=[MagicMock(stdout=inspect_empty), MagicMock(stdout="[]")],
        ):
            res = analyzer.analyze(cl, "r", "t")
            assert "FROM scratch" in res["dockerfile"]
