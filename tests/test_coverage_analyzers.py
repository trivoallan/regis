import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from regis_cli.analyzers.base import AnalyzerError
from regis_cli.analyzers.hadolint import HadolintAnalyzer
from regis_cli.analyzers.provenance import ProvenanceAnalyzer
from regis_cli.analyzers.scorecarddev import (
    _fetch_scorecard,
    _resolve_source_repo,
    _source_repo_from_dockerhub,
)
from regis_cli.analyzers.size import SizeAnalyzer, _human_size
from regis_cli.analyzers.skopeo import SkopeoAnalyzer


class TestSkopeoCoverage:
    @pytest.fixture
    def analyzer(self):
        return SkopeoAnalyzer()

    def test_skopeo_all(self, analyzer):
        cl = MagicMock(registry="registry-1.docker.io", username="u", password="p")
        raw = json.dumps({"mediaType": "manifest", "layers": [1]})
        ins = json.dumps(
            {"Os": "linux", "Architecture": "amd64", "Created": "c", "Layers": [1]}
        )
        tags = json.dumps({"Tags": ["v1"]})

        def run_mock(cmd, **k):
            s = " ".join(cmd)
            if "--raw" in s:
                return MagicMock(stdout=raw)
            if "list-tags" in s:
                return MagicMock(stdout=tags)
            return MagicMock(stdout=ins)

        with patch("subprocess.run", side_effect=run_mock):
            r = analyzer.analyze(cl, "r", "t")
            assert r["tags"] == ["v1"]
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(AnalyzerError):
                analyzer._run_skopeo(cl, ["v"])

    def test_multiarch(self, analyzer):
        cl = MagicMock(registry="r", username=None)
        m_list = json.dumps(
            {
                "mediaType": "index",
                "manifests": [
                    {
                        "digest": "sha256:1",
                        "platform": {"os": "linux", "architecture": "amd64"},
                    }
                ],
            }
        )
        ins = json.dumps(
            {"Os": "linux", "Architecture": "amd64", "Created": "c", "Layers": [1]}
        )
        cfg = json.dumps({"config": {"User": "root"}})

        def run_mock(cmd, **k):
            s = " ".join(cmd)
            if "--raw" in s:
                return MagicMock(stdout=m_list)
            if "list-tags" in s:
                return MagicMock(stdout='{"Tags":[]}')
            if "--config" in s:
                return MagicMock(stdout=cfg)
            return MagicMock(stdout=ins)

        with patch("subprocess.run", side_effect=run_mock):
            r = analyzer.analyze(cl, "r", "t")
            assert r["platforms"][0]["user"] == "root"


class TestHadolintCoverage:
    def test_hadolint_full(self):
        a = HadolintAnalyzer()
        cl = MagicMock(registry="r", username="u", password="p")
        sk = json.dumps({"history": [{"created_by": "RUN echo 1"}]})
        ha = json.dumps([{"level": "warning", "message": "m"}])
        with patch("subprocess.run") as m:
            m.side_effect = [MagicMock(stdout=sk), MagicMock(stdout=ha)]
            r = a.analyze(cl, "r", "t")
            assert r["issues_by_level"]["warning"] == 1
            m.side_effect = subprocess.CalledProcessError(1, "s")
            with pytest.raises(AnalyzerError):
                a.analyze(cl, "r", "t")


class TestScorecardCoverage:
    def test_flow(self):
        cl = MagicMock()
        cl.get_manifest.side_effect = [
            {"mediaType": "index", "manifests": [{"digest": "s:1"}]},
            {"mediaType": "manifest", "config": {"digest": "s:2"}},
        ]
        cl.get_blob.return_value = {
            "config": {
                "Labels": {"org.opencontainers.image.source": "https://github.com/a/b"}
            }
        }
        assert _resolve_source_repo(cl, "r", "tag") == "https://github.com/a/b"
        with patch("requests.get") as g:
            g.return_value = MagicMock(status_code=200)
            g.return_value.json.return_value = {
                "full_description": "Git at https://github.com/f/b"
            }
            assert "f/b" in _source_repo_from_dockerhub("r")
            g.return_value.status_code = 401
            assert _fetch_scorecard("gh", "o", "r") is None


class TestSizeCoverage:
    def test_size_all(self):
        a = SizeAnalyzer()
        cl = MagicMock(registry="r")
        m_list = json.dumps(
            {
                "mediaType": "index",
                "manifests": [
                    {
                        "digest": "s:1",
                        "platform": {"os": "linux", "architecture": "arm64"},
                    }
                ],
            }
        )
        raw = json.dumps({"layers": [{"size": 10}], "config": {"size": 5}})
        with patch("subprocess.run") as m:
            m.side_effect = [MagicMock(stdout=m_list), MagicMock(stdout=raw)]
            r = a.analyze(cl, "r", "t", platform="linux/arm64")
            assert r["total_compressed_bytes"] == 15
        assert a._empty("r", "t")["layer_count"] == 0
        assert "TB" in _human_size(10**13)


class TestProvenanceCoverage:
    def test_prov_all(self):
        a = ProvenanceAnalyzer()
        cl = MagicMock()
        cl.get_manifest.side_effect = [
            {"mediaType": "index", "manifests": [{"digest": "s:1"}]},
            {"mediaType": "manifest", "config": {"digest": "cfg"}},
            {"layers": [1]},
            {"mediaType": "index", "manifests": []},
            Exception("f"),
        ]
        cl.get_blob.return_value = {
            "config": {"Labels": {"org.opencontainers.image.source": "s"}}
        }
        r = a.analyze(cl, "r", "t")
        assert r["indicators_count"] == 2
        assert a.analyze(cl, "r", "t")["indicators_count"] == 0
        a.analyze(cl, "r", "t")
