"""Tests for the size analyzer."""

from regis.analyzers.size import SizeAnalyzer, _human_size

from .fakes import FakeImageInspector, make_ctx


class TestHumanSize:
    def test_bytes(self):
        assert _human_size(500) == "500.0 B"

    def test_kb(self):
        assert _human_size(2048) == "2.0 KB"

    def test_mb(self):
        assert _human_size(5 * 1024 * 1024) == "5.0 MB"


# --------------------------------------------------------------------------- #
#  Single-arch path                                                             #
# --------------------------------------------------------------------------- #


class TestSizeAnalyzer:
    def test_size_uses_context(self):
        assert SizeAnalyzer.uses_context is True

    def test_single_manifest(self):
        single_manifest = {
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "config": {"digest": "sha256:cfg1", "size": 1500},
            "layers": [
                {"size": 10000, "digest": "sha256:l1"},
                {"size": 20000, "digest": "sha256:l2"},
            ],
        }
        inspector = FakeImageInspector(manifests={"1.0": single_manifest})
        ctx = make_ctx(inspector=inspector)
        analyzer = SizeAnalyzer()
        report = analyzer.analyze(ctx)
        analyzer.validate(report)

        assert report["multi_arch"] is False
        assert report["total_compressed_bytes"] == 31500
        assert report["layer_count"] == 2
        assert len(report["layers"]) == 2

    # ----------------------------------------------------------------------- #
    #  Multi-arch path                                                          #
    # ----------------------------------------------------------------------- #

    def test_multi_arch_manifest(self):
        index = {
            "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
            "manifests": [
                {
                    "digest": "sha256:amd64digest",
                    "size": 1500,  # fallback size if per-platform fetch fails
                    "platform": {"architecture": "amd64", "os": "linux"},
                },
                {
                    "digest": "sha256:arm64digest",
                    "platform": {"architecture": "arm64", "os": "linux"},
                },
            ],
        }
        amd64_manifest = {
            "config": {"size": 500},
            "layers": [{"size": 1000}],
        }
        arm64_manifest = {
            "config": {"size": 500},
            "layers": [{"size": 1000}, {"size": 2000}],
        }
        inspector = FakeImageInspector(
            manifests={
                "1.0": index,
                "sha256:amd64digest": amd64_manifest,
                "sha256:arm64digest": arm64_manifest,
            }
        )
        ctx = make_ctx(inspector=inspector)
        analyzer = SizeAnalyzer()
        report = analyzer.analyze(ctx)
        analyzer.validate(report)

        assert report["multi_arch"] is True
        assert report["layer_count"] == 1  # From amd64 variant
        assert report["total_compressed_bytes"] == 1500
        assert len(report["platforms"]) == 2

    def test_multi_arch_filters_attestation_manifests(self):
        index = {
            "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
            "manifests": [
                {
                    "digest": "sha256:amd64digest",
                    "platform": {"architecture": "amd64", "os": "linux"},
                },
                {
                    "digest": "sha256:arm64digest",
                    "platform": {"architecture": "arm64", "os": "linux"},
                },
                {
                    "digest": "sha256:attestdigest",
                    "platform": {"architecture": "unknown", "os": "unknown"},
                },
            ],
        }
        amd64_manifest = {"config": {"size": 500}, "layers": [{"size": 1000}]}
        arm64_manifest = {
            "config": {"size": 500},
            "layers": [{"size": 1000}, {"size": 2000}],
        }

        class _NoAttestInspector(FakeImageInspector):
            def get_manifest(self, reference: str) -> dict:
                if reference == "sha256:attestdigest":
                    raise AssertionError(
                        "SizeAnalyzer must not fetch attestation manifest digest"
                    )
                return super().get_manifest(reference)

        inspector = _NoAttestInspector(
            manifests={
                "1.0": index,
                "sha256:amd64digest": amd64_manifest,
                "sha256:arm64digest": arm64_manifest,
            }
        )
        ctx = make_ctx(inspector=inspector)
        analyzer = SizeAnalyzer()
        report = analyzer.analyze(ctx)
        analyzer.validate(report)

        assert report["multi_arch"] is True
        assert len(report["platforms"]) == 2
        for plat in report["platforms"]:
            assert "unknown" not in plat["platform"]

    def test_empty_manifest(self):
        inspector = FakeImageInspector(manifests={"1.0": {}})
        ctx = make_ctx(inspector=inspector)
        analyzer = SizeAnalyzer()
        report = analyzer.analyze(ctx)
        analyzer.validate(report)

        assert report["layer_count"] == 0

    # ----------------------------------------------------------------------- #
    #  Platform-override path                                                   #
    # ----------------------------------------------------------------------- #

    def test_platform_override_returns_only_matching_platform(self):
        index = {
            "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
            "manifests": [
                {
                    "digest": "sha256:amd64digest",
                    "platform": {"architecture": "amd64", "os": "linux"},
                },
                {
                    "digest": "sha256:arm64digest",
                    "platform": {
                        "architecture": "arm64",
                        "os": "linux",
                        "variant": "v8",
                    },
                },
            ],
        }
        amd64_manifest = {"config": {"size": 200}, "layers": [{"size": 800}]}
        arm64_manifest = {"config": {"size": 300}, "layers": [{"size": 700}]}
        inspector = FakeImageInspector(
            manifests={
                "1.0": index,
                "sha256:amd64digest": amd64_manifest,
                "sha256:arm64digest": arm64_manifest,
            }
        )
        ctx = make_ctx(inspector=inspector, platform="linux/arm64")
        analyzer = SizeAnalyzer()
        report = analyzer.analyze(ctx)
        analyzer.validate(report)

        assert report["multi_arch"] is True
        assert len(report["platforms"]) == 1
        # variant is included in the platform label
        assert report["platforms"][0]["platform"] == "linux/arm64/v8"
        assert report["platforms"][0]["compressed_bytes"] == 1000

    def test_platform_override_no_slash_defaults_os_to_linux(self):
        """platform="arm64" (no slash) should be treated as linux/arm64."""
        index = {
            "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
            "manifests": [
                {
                    "digest": "sha256:amd64digest",
                    "platform": {"architecture": "amd64", "os": "linux"},
                },
                {
                    "digest": "sha256:arm64digest",
                    "platform": {
                        "architecture": "arm64",
                        "os": "linux",
                        "variant": "v8",
                    },
                },
            ],
        }
        amd64_manifest = {"config": {"size": 200}, "layers": [{"size": 800}]}
        arm64_manifest = {"config": {"size": 300}, "layers": [{"size": 700}]}
        inspector = FakeImageInspector(
            manifests={
                "1.0": index,
                "sha256:amd64digest": amd64_manifest,
                "sha256:arm64digest": arm64_manifest,
            }
        )
        # No slash — "arm64" implies os="linux"
        ctx = make_ctx(inspector=inspector, platform="arm64")
        analyzer = SizeAnalyzer()
        report = analyzer.analyze(ctx)
        analyzer.validate(report)

        assert report["multi_arch"] is True
        assert len(report["platforms"]) == 1
        assert report["platforms"][0]["platform"] == "linux/arm64/v8"
        assert report["platforms"][0]["compressed_bytes"] == 1000

    # ----------------------------------------------------------------------- #
    #  Fetch-failure fallback — entry.get("size", 0)                           #
    # ----------------------------------------------------------------------- #

    def test_per_platform_fetch_failure_falls_back_to_entry_size(self):
        index = {
            "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
            "manifests": [
                {
                    "digest": "sha256:ok",
                    "size": 9999,
                    "platform": {"architecture": "amd64", "os": "linux"},
                },
                {
                    "digest": "sha256:broken",
                    "size": 4242,
                    "platform": {"architecture": "arm64", "os": "linux"},
                },
            ],
        }
        ok_manifest = {"config": {"size": 100}, "layers": [{"size": 900}]}

        class _BrokenInspector(FakeImageInspector):
            def get_manifest(self, reference: str) -> dict:
                if reference == "sha256:broken":
                    raise OSError("network error")
                return super().get_manifest(reference)

        inspector = _BrokenInspector(
            manifests={
                "1.0": index,
                "sha256:ok": ok_manifest,
            }
        )
        ctx = make_ctx(inspector=inspector)
        analyzer = SizeAnalyzer()
        report = analyzer.analyze(ctx)
        analyzer.validate(report)

        assert report["multi_arch"] is True
        assert len(report["platforms"]) == 2
        # amd64 — real fetch worked
        amd64 = next(p for p in report["platforms"] if "amd64" in p["platform"])
        assert amd64["compressed_bytes"] == 1000
        # arm64 — fallback to entry["size"]
        arm64 = next(p for p in report["platforms"] if "arm64" in p["platform"])
        assert arm64["compressed_bytes"] == 4242
        assert arm64["layer_count"] == 0
