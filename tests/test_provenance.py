"""Tests for the provenance analyzer."""

from regis.core.domain.analyzers.provenance import ProvenanceAnalyzer
from regis.core.domain.context import AnalysisContext
from regis.core.model.image_reference import ImageReference
from tests.fakes import FakeToolRunner


class MockRegistryClient:
    def __init__(self, manifest=None, blobs=None):
        self._manifest = manifest or {}
        self._blobs = blobs or {}

    def list_tags(self):
        return []

    def get_manifest(self, tag):
        if tag.startswith("sha256:"):
            return self._blobs.get(f"manifest:{tag}", self._manifest)
        return self._manifest

    def get_blob(self, digest):
        return self._blobs.get(digest, {})


def _ctx(inspector, *, repository="my-repo", tag="latest"):
    return AnalysisContext(
        image=ImageReference(registry="docker.io", repository=repository, tag=tag),
        inspector=inspector,
        tools=FakeToolRunner(),
    )


class TestProvenanceAnalyzer:
    def test_with_oci_labels(self):
        manifest = {
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "config": {"digest": "sha256:cfg1"},
        }
        config = {
            "config": {
                "Labels": {
                    "org.opencontainers.image.source": "https://github.com/test/repo",
                    "org.opencontainers.image.revision": "abc1234",
                }
            },
        }
        client = MockRegistryClient(manifest=manifest, blobs={"sha256:cfg1": config})
        analyzer = ProvenanceAnalyzer()
        report = analyzer.analyze(_ctx(client, repository="library/test", tag="latest"))
        analyzer.validate(report)

        assert report["has_provenance"] is True
        assert report["source_tracked"] is True
        assert report["indicators_count"] >= 2

    def test_no_labels(self):
        manifest = {
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "config": {"digest": "sha256:cfg1"},
        }
        config = {"config": {"Labels": {}}}
        client = MockRegistryClient(manifest=manifest, blobs={"sha256:cfg1": config})
        analyzer = ProvenanceAnalyzer()
        report = analyzer.analyze(
            _ctx(client, repository="fakens/noinfo", tag="latest")
        )
        analyzer.validate(report)

        assert report["has_provenance"] is False
        assert report["indicators_count"] == 0
