import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from regis_cli.analyzers.base import AnalyzerError
from regis_cli.analyzers.skopeo import SkopeoAnalyzer

OCI_INDEX = "application/vnd.oci.image.index.v1+json"


class TestSkopeoAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return SkopeoAnalyzer()

    def test_exhaustive_skopeo_flow(self, analyzer):
        cl = MagicMock(registry="registry-1.docker.io")

        m_list = json.dumps(
            {
                "mediaType": OCI_INDEX,
                "manifests": [
                    {
                        "digest": "s1",
                        "platform": {
                            "os": "linux",
                            "architecture": "amd64",
                            "variant": "v8",
                        },
                    },
                    {
                        "digest": "s2",
                        "platform": {"os": "darwin", "architecture": "arm64"},
                    },
                ],
            }
        )
        tags = json.dumps({"Tags": ["v1"]})
        ins = json.dumps(
            {
                "Os": "linux",
                "Architecture": "amd64",
                "Layers": [{"digest": "l1"}],
                "Digest": "s1",
                "Variant": "v8",
            }
        )
        cfg = json.dumps({"config": {"User": "root"}})

        def dispatcher(cmd, **k):
            s = " ".join(cmd)
            if "FAIL_TAGS" in s and "list-tags" in s:
                raise Exception("tags fail")
            if "FAIL_RAW" in s and "--raw" in s:
                raise Exception("raw fail")
            if (
                "FAIL_PRIM" in s
                and "--raw" not in s
                and "--config" not in s
                and "list-tags" not in s
            ):
                raise Exception("prim fail")

            if "--raw" in s:
                return MagicMock(stdout=m_list)
            if "list-tags" in s:
                return MagicMock(stdout=tags)
            if "--config" in s:
                return MagicMock(stdout=cfg)
            return MagicMock(stdout=ins)

        with patch("subprocess.run", side_effect=dispatcher):
            # 1. Multi-arch loop (hits line 79-103)
            res = analyzer.analyze(cl, "repo", "tag")
            assert len(res["platforms"]) == 2

            # 2. Platform split override (66-76)
            res_ov = analyzer.analyze(cl, "r", "t", platform="linux/amd64")
            assert len(res_ov["platforms"]) == 1

            # 3. Fallbacks
            assert analyzer.analyze(cl, "FAIL_TAGS", "t")["tags"] == []
            assert analyzer.analyze(cl, "FAIL_PRIM", "t")["inspect"] == {}
            with pytest.raises(AnalyzerError):
                analyzer.analyze(cl, "FAIL_RAW", "t")

    def test_skopeo_surgical_bits(self, analyzer):
        cl = MagicMock(registry="reg")
        # Single platform manifest (105-110)
        ins_single = json.dumps({"layers": [{"digest": "l1"}], "Architecture": "amd64"})

        def disp_single(cmd, **k):
            s = " ".join(cmd)
            if "--raw" in s:
                return MagicMock(stdout=ins_single)
            if "--config" in s:
                return MagicMock(stdout='{"config":{}}')
            if "list-tags" in s:
                return MagicMock(stdout='{"Tags":[]}')
            return MagicMock(stdout=ins_single)

        with patch("subprocess.run", side_effect=disp_single):
            res = analyzer.analyze(cl, "r", "t")
            assert res["platforms"][0]["layers_count"] == 1

        # 224-225 (inspect fail), 241-244 (config fail), 189 (sha)
        with patch(
            "subprocess.run",
            side_effect=[
                subprocess.CalledProcessError(1, "c", stderr="e"),
                Exception("cfg"),
            ],
        ):
            res = analyzer._inspect_platform(cl, "reg", "r", "sha256:123", {})
            assert res["user"] == "unknown"

        # 170
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(AnalyzerError):
                analyzer._run_skopeo(cl, ["v"])
