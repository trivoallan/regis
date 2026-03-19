from unittest.mock import MagicMock, patch

import pytest

from regis_cli.analyzers.scorecarddev import (
    ScorecardDevAnalyzer,
    _fetch_scorecard,
    _resolve_source_repo,
    _source_repo_from_dockerhub,
    _source_repo_from_labels,
)

INDEX_TYPE = "application/vnd.oci.image.index.v1+json"
MANIFEST_TYPE = "application/vnd.oci.image.manifest.v1+json"


class TestScorecardAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return ScorecardDevAnalyzer()

    def test_labels_recursion_exhaustive(self):
        cl = MagicMock()
        # 45, 50, 62 recursion loop
        m_list = {"mediaType": INDEX_TYPE, "manifests": [{"digest": "s1"}]}
        m_single = {"mediaType": MANIFEST_TYPE, "config": {"digest": "c1"}}
        cl.get_manifest.side_effect = [
            m_list,
            m_manifest_without_config := {"mediaType": MANIFEST_TYPE},
            m_list,
            m_single,
        ]
        cl.get_blob.return_value = {
            "config": {"Labels": {"org.opencontainers.image.source": "o/r"}}
        }

        # 45 Empty manifests
        m_empty = {"mediaType": INDEX_TYPE, "manifests": []}
        cl.get_manifest.side_effect = [m_empty]
        assert _source_repo_from_labels(cl, "t") is None

        # 50 No config
        cl.get_manifest.side_effect = [m_manifest_without_config]
        assert _source_repo_from_labels(cl, "t") is None

        # 62 Exception
        cl.get_manifest.side_effect = Exception("fail")
        assert _source_repo_from_labels(cl, "t") is None

        # Recursion SUCCESS
        cl.get_manifest.side_effect = [m_list, m_single]
        assert _source_repo_from_labels(cl, "t") == "o/r"

    def test_dockerhub_exhaustive(self):
        # 80-83 (source vs desc)
        with patch("requests.get") as m:
            m.return_value = MagicMock(status_code=200)
            m.return_value.json.return_value = {"source": "github.com/a/b"}
            assert _source_repo_from_dockerhub("r") == "https://github.com/a/b"
            m.return_value.json.return_value = {
                "full_description": "github.com/foo/bar"
            }
            assert _source_repo_from_dockerhub("r") == "https://github.com/foo/bar"

            m.side_effect = Exception("fail")
            assert _source_repo_from_dockerhub("r") is None

    def test_resolve_and_search_exhaustive(self):
        # 99 search logic
        cl = MagicMock()
        with patch(
            "regis_cli.analyzers.scorecarddev._source_repo_from_labels",
            return_value="https://github.com/a/b",
        ):
            assert _resolve_source_repo(cl, "r", "t") == "https://github.com/a/b"

        with patch(
            "regis_cli.analyzers.scorecarddev._source_repo_from_labels",
            return_value=None,
        ):
            with patch(
                "regis_cli.analyzers.scorecarddev._source_repo_from_dockerhub",
                return_value=None,
            ):
                assert _resolve_source_repo(cl, "r", "t") is None

    def test_fetch_errors_exhaustive(self):
        # 111 (git strip), 113 (scheme), 123 (fetch), 126 (404)
        with patch(
            "requests.get", side_effect=[MagicMock(status_code=404), Exception("fail")]
        ):
            assert _fetch_scorecard("gh", "o", "r.git") is None
            assert _fetch_scorecard("gh", "o", "r") is None

    def test_analyze_logic_exhaustive(self, analyzer):
        cl = MagicMock()
        # 147, 158, 171
        with patch(
            "regis_cli.analyzers.scorecarddev._resolve_source_repo",
            side_effect=[None, "https://github.com/o/r"],
        ):
            assert analyzer.analyze(cl, "r", "t")["source_repo"] is None

            with patch(
                "regis_cli.analyzers.scorecarddev._fetch_scorecard",
                return_value={"score": 5},
            ):
                res = analyzer.analyze(cl, "r", "t")
                assert res["score"] == 5
                assert res["checks"] == []
