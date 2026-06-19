from unittest.mock import MagicMock, patch

from regis.core.domain.analyzers.provenance import ProvenanceAnalyzer
from regis.core.domain.analyzers.scorecarddev import (
    _fetch_scorecard,
    _resolve_source_repo,
    _source_repo_from_dockerhub,
)
from regis.core.domain.context import AnalysisContext
from regis.core.model.image_reference import ImageReference
from tests.fakes import FakeToolRunner


def _prov_ctx(inspector, *, repository="r", tag="t"):
    return AnalysisContext(
        image=ImageReference(registry="docker.io", repository=repository, tag=tag),
        inspector=inspector,
        tools=FakeToolRunner(),
    )


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
