import json
from unittest.mock import MagicMock, patch

import pytest

from regis_cli.analyzers.base import AnalyzerError
from regis_cli.analyzers.size import SizeAnalyzer, _human_size


class TestSizeAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return SizeAnalyzer()

    def test_human_size_exhaustive(self):
        # coverage for units and fallback (21-22)
        assert "1024.0 TB" in _human_size(1024.0**5)
        assert "1.0 MB" in _human_size(1024.0**2)

    def test_size_exhaustive(self, analyzer):
        cl = MagicMock(registry="registry-1.docker.io")
        # 50 (registry norm), 61-64 (exc), 74 (analyze_single), 122-135 (platform list filter), 144 (variant), 149 (skip), 161 (worker fallback)

        # 1. Single arch (74)
        raw_s = json.dumps(
            {"mediaType": "manifest", "layers": [{"size": 100}], "config": {"size": 50}}
        )
        with patch("subprocess.run", return_value=MagicMock(stdout=raw_s)):
            res = analyzer.analyze(cl, "r", "t")
            assert res["total_compressed_bytes"] == 150

        # 2. Multi arch index with filter and variant (122-135, 144)
        m_list = json.dumps(
            {
                "mediaType": "index",
                "manifests": [
                    {
                        "digest": "s1",
                        "platform": {
                            "os": "linux",
                            "architecture": "arm64",
                            "variant": "v8",
                        },
                    },
                    {
                        "digest": "s2",
                        "platform": {"os": "linux", "architecture": "amd64"},
                    },
                ],
            }
        )
        ins = json.dumps({"layers": [{"size": 50}], "config": {"size": 10}})
        with patch(
            "subprocess.run",
            side_effect=[MagicMock(stdout=m_list), MagicMock(stdout=ins)],
        ):
            res = analyzer.analyze(cl, "r", "t", platform="linux/arm64")
            assert res["platforms"][0]["platform"] == "linux/arm64/v8"
            assert res["total_compressed_bytes"] == 60

        # 3. Aggregation failure (161-164) and Missing digest (149)
        m_list_err = json.dumps(
            {
                "mediaType": "index",
                "manifests": [
                    {
                        "digest": "",
                        "platform": {"os": "linux", "architecture": "amd64"},
                    },  # line 149
                    {
                        "digest": "s1",
                        "platform": {"os": "linux", "architecture": "arm64"},
                        "size": 100,
                    },  # line 162 fallback
                ],
            }
        )
        with patch(
            "subprocess.run",
            side_effect=[MagicMock(stdout=m_list_err), Exception("fail")],
        ):
            res = analyzer.analyze(cl, "r", "t")
            assert res["platforms"][0]["compressed_bytes"] == 100

    def test_size_errors_exhaustive(self, analyzer):
        cl = MagicMock(registry="r")
        # 61-64 exc
        with patch("subprocess.run", side_effect=Exception("parse fail")):
            with pytest.raises(AnalyzerError):
                analyzer.analyze(cl, "r", "t")
        # 192 _empty
        assert analyzer._empty("r", "t")["layer_count"] == 0

        # 135 warning
        m_list = json.dumps(
            {
                "mediaType": "index",
                "manifests": [{"platform": {"os": "l", "architecture": "a"}}],
            }
        )
        with patch("subprocess.run", return_value=MagicMock(stdout=m_list)):
            res = analyzer.analyze(cl, "r", "t", platform="w/x")
            assert len(res["platforms"]) == 0
