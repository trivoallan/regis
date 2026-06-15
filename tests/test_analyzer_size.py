import pytest

from regis.analyzers.base import AnalyzerError
from regis.analyzers.size import SizeAnalyzer, _human_size

from .fakes import FakeImageInspector, make_ctx


class TestSizeAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return SizeAnalyzer()

    def test_human_size_exhaustive(self):
        # coverage for units and fallback
        assert "1024.0 TB" in _human_size(1024.0**5)
        assert "1.0 MB" in _human_size(1024.0**2)

    def test_size_exhaustive(self, analyzer):
        # 1. Single arch
        single = {
            "mediaType": "manifest",
            "layers": [{"size": 100}],
            "config": {"size": 50},
        }
        ctx = make_ctx(inspector=FakeImageInspector(manifests={"1.0": single}))
        res = analyzer.analyze(ctx)
        assert res["total_compressed_bytes"] == 150

        # 2. Multi arch index with filter and variant
        index = {
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
        arm64_manifest = {"layers": [{"size": 50}], "config": {"size": 10}}
        inspector = FakeImageInspector(manifests={"1.0": index, "s1": arm64_manifest})
        ctx = make_ctx(inspector=inspector, platform="linux/arm64")
        res = analyzer.analyze(ctx)
        assert res["platforms"][0]["platform"] == "linux/arm64/v8"
        assert res["total_compressed_bytes"] == 60

        # 3. Aggregation failure (fallback) and Missing digest (skip)
        index_err = {
            "mediaType": "index",
            "manifests": [
                {
                    "digest": "",  # empty digest → skip
                    "platform": {"os": "linux", "architecture": "amd64"},
                },
                {
                    "digest": "s1",
                    "platform": {"os": "linux", "architecture": "arm64"},
                    "size": 100,  # entry-level fallback
                },
            ],
        }

        class _BrokenInspector(FakeImageInspector):
            def get_manifest(self, reference: str) -> dict:
                if reference == "s1":
                    raise OSError("fail")
                return super().get_manifest(reference)

        ctx = make_ctx(
            inspector=_BrokenInspector(manifests={"1.0": index_err}),
        )
        res = analyzer.analyze(ctx)
        assert res["platforms"][0]["compressed_bytes"] == 100

    def test_size_errors_exhaustive(self, analyzer):
        # Inspector raises on get_manifest → AnalyzerError

        class _RaisingInspector(FakeImageInspector):
            def get_manifest(self, reference: str) -> dict:
                raise OSError("parse fail")

        ctx = make_ctx(inspector=_RaisingInspector())
        with pytest.raises(AnalyzerError):
            analyzer.analyze(ctx)

        # Platform override with no matching platform → empty platforms list
        index = {
            "mediaType": "index",
            "manifests": [{"platform": {"os": "l", "architecture": "a"}}],
        }
        ctx = make_ctx(
            inspector=FakeImageInspector(manifests={"1.0": index}),
            platform="w/x",
        )
        res = analyzer.analyze(ctx)
        assert len(res["platforms"]) == 0
