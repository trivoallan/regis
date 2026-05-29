import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from regis.analyzers.base import AnalyzerError
from regis.analyzers.hadolint import HadolintAnalyzer


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

        with (
            patch("regis.analyzers.hadolint.run_regctl", return_value=inspect),
            patch(
                "regis.analyzers.hadolint.subprocess.run",
                return_value=MagicMock(stdout=hadolint),
            ),
        ):
            res = analyzer.analyze(cl, "repo", "tag", platform="linux/amd64")
            assert 'CMD ["python3"]' in res["dockerfile"]
            assert "RUN echo 1" in res["dockerfile"]

        with (
            patch("regis.analyzers.hadolint.run_regctl", return_value=inspect),
            patch(
                "regis.analyzers.hadolint.subprocess.run",
                return_value=MagicMock(stdout=hadolint),
            ),
        ):
            res = analyzer.analyze(cl, "repo", "tag", platform="amd64")
            assert res["issues_count"] == 1

    def test_hadolint_errors_exhaustive(self, analyzer):
        cl = MagicMock(registry="reg")
        inspect = json.dumps({"history": [{"created_by": "RUN echo 1"}]})

        # Config parse failure: regctl returns invalid JSON.
        with patch("regis.analyzers.hadolint.run_regctl", return_value="{invalid}"):
            with pytest.raises(AnalyzerError):
                analyzer.analyze(cl, "r", "t")

        # Hadolint binary missing.
        with (
            patch("regis.analyzers.hadolint.run_regctl", return_value=inspect),
            patch(
                "regis.analyzers.hadolint.subprocess.run", side_effect=FileNotFoundError
            ),
        ):
            with pytest.raises(AnalyzerError):
                analyzer.analyze(cl, "r", "t")

        # Hadolint output parsing error.
        with (
            patch("regis.analyzers.hadolint.run_regctl", return_value=inspect),
            patch(
                "regis.analyzers.hadolint.subprocess.run",
                return_value=MagicMock(stdout="invalid json"),
            ),
        ):
            with pytest.raises(AnalyzerError):
                analyzer.analyze(cl, "r", "t")

        # Hadolint command failure but valid output (check=False).
        m_run = MagicMock(returncode=1, stderr="err", stdout="[]")
        with (
            patch("regis.analyzers.hadolint.run_regctl", return_value=inspect),
            patch("regis.analyzers.hadolint.subprocess.run", return_value=m_run),
        ):
            res = analyzer.analyze(cl, "r", "t")
            assert res["issues_count"] == 0

        # Config fetch failure: regctl exits non-zero.
        with patch(
            "regis.analyzers.hadolint.run_regctl",
            side_effect=subprocess.CalledProcessError(1, "s", stderr="e"),
        ):
            with pytest.raises(AnalyzerError):
                analyzer.analyze(cl, "r", "t")

        # Empty history.
        inspect_empty = json.dumps({"history": [{"created_by": ""}]})
        with (
            patch("regis.analyzers.hadolint.run_regctl", return_value=inspect_empty),
            patch(
                "regis.analyzers.hadolint.subprocess.run",
                return_value=MagicMock(stdout="[]"),
            ),
        ):
            res = analyzer.analyze(cl, "r", "t")
            assert "FROM scratch" in res["dockerfile"]
