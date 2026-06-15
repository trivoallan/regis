import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from regis.analyzers.base import AnalyzerError
from regis.analyzers.hadolint import HadolintAnalyzer
from regis.analyzers.oci import OciAnalyzer
from regis.analyzers.provenance import ProvenanceAnalyzer
from regis.analyzers.scorecarddev import (
    _fetch_scorecard,
    _resolve_source_repo,
    _source_repo_from_dockerhub,
)
from regis.analyzers.size import SizeAnalyzer, _human_size
from regis.core.domain.context import AnalysisContext
from regis.core.model.image_reference import ImageReference
from regis.utils.regctl import run_regctl
from tests.fakes import FakeToolRunner


def _prov_ctx(inspector, *, repository="r", tag="t"):
    return AnalysisContext(
        image=ImageReference(registry="docker.io", repository=repository, tag=tag),
        inspector=inspector,
        tools=FakeToolRunner(),
    )


class TestOciCoverage:
    @pytest.fixture
    def analyzer(self):
        return OciAnalyzer()

    def test_oci_all(self, analyzer):
        """Single-arch analyze() happy path: tags parsed from regctl output."""
        cl = MagicMock(registry="registry-1.docker.io", username="u", password="p")
        single_manifest = json.dumps(
            {
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "config": {"size": 5},
                "layers": [{"size": 10}],
            }
        )
        inspect = json.dumps(
            {
                "architecture": "amd64",
                "os": "linux",
                "created": "c",
                "config": {},
            }
        )

        def regctl_mock(client, args, **k):
            sub = args[0:2]
            if sub == ["manifest", "get"]:
                return single_manifest
            if sub == ["manifest", "head"]:
                return "sha256:abc\n"
            if sub == ["image", "inspect"]:
                return inspect
            if sub == ["tag", "ls"]:
                return "v1\nv2\n"
            raise AssertionError(f"Unexpected regctl call: {args}")

        with patch("regis.analyzers.oci.run_regctl", side_effect=regctl_mock):
            r = analyzer.analyze(cl, "r", "t")
        assert r["tags"] == ["v1", "v2"]
        assert r["platforms"][0]["size"] == 15
        assert r["platforms"][0]["digest"] == "sha256:abc"

    def test_multiarch(self, analyzer):
        """Multi-arch index: per-platform config blob exposes the User."""
        cl = MagicMock(registry="r", username=None)
        index = json.dumps(
            {
                "mediaType": "application/vnd.oci.image.index.v1+json",
                "manifests": [
                    {
                        "digest": "sha256:1",
                        "platform": {"os": "linux", "architecture": "amd64"},
                    }
                ],
            }
        )
        per_platform_manifest = json.dumps(
            {"config": {"size": 5}, "layers": [{"size": 10}]}
        )
        inspect = json.dumps(
            {
                "architecture": "amd64",
                "os": "linux",
                "created": "c",
                "config": {"User": "root"},
            }
        )

        def regctl_mock(client, args, **k):
            sub = args[0:2]
            if sub == ["manifest", "get"]:
                return per_platform_manifest if "--platform" in args else index
            if sub == ["image", "inspect"]:
                return inspect
            if sub == ["tag", "ls"]:
                return ""
            raise AssertionError(f"Unexpected regctl call: {args}")

        with patch("regis.analyzers.oci.run_regctl", side_effect=regctl_mock):
            r = analyzer.analyze(cl, "r", "t")
        assert r["platforms"][0]["user"] == "root"

    def test_run_regctl_missing_binary_raises(self):
        """run_regctl raises AnalyzerError when regctl is not on PATH."""
        cl = MagicMock(registry="r", username=None, password=None)
        with patch("regis.utils.regctl.subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(AnalyzerError):
                run_regctl(cl, ["v"])


class TestHadolintCoverage:
    def test_hadolint_full(self):
        a = HadolintAnalyzer()
        cl = MagicMock(registry="r", username="u", password="p")
        sk = json.dumps({"history": [{"created_by": "RUN echo 1"}]})
        ha = json.dumps([{"level": "warning", "message": "m"}])
        with patch(
            "regis.analyzers.hadolint.ensure_tool", return_value="/usr/bin/hadolint"
        ), patch("subprocess.run") as m:
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
        r = a.analyze(_prov_ctx(cl))
        assert r["indicators_count"] == 2
        assert a.analyze(_prov_ctx(cl))["indicators_count"] == 0
        a.analyze(_prov_ctx(cl))
