"""Tests for the oci analyzer (formerly skopeo)."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from unittest.mock import MagicMock, patch

import jsonschema

from regis.analyzers.oci import OciAnalyzer, _platforms_supported

_FIXTURES = Path(__file__).parent / "fixtures" / "regctl"


def _fixture(name: str) -> str:
    return (_FIXTURES / name).read_text()


def _client(registry: str = "docker.io") -> MagicMock:
    client = MagicMock()
    client.registry = registry
    client.username = None
    client.password = None
    return client


def _has_platform_flag(args: list[str]) -> bool:
    return "--platform" in args


def test_oci_schema_is_valid_draft7():
    schema_text = (
        resources.files("regis.schemas")
        .joinpath("analyzer/oci.schema.json")
        .read_text()
    )
    schema = json.loads(schema_text)
    jsonschema.Draft7Validator.check_schema(schema)
    assert schema["properties"]["analyzer"]["const"] == "oci"


def test_oci_name_and_schema():
    analyzer = OciAnalyzer()
    assert analyzer.name == "oci"
    assert analyzer.schema_file == "analyzer/oci.schema.json"


def test_oci_default_criteria_use_oci_paths():
    serialized = json.dumps(OciAnalyzer.default_criteria())
    assert "results.oci." in serialized
    assert "results.skopeo." not in serialized
    # Criterion-bound params use the new namespace, not the legacy `rule.`.
    assert "criterion.params." in serialized
    assert "rule.params." not in serialized


def _single_platform_dispatcher(_client_arg: object, args: list[str]) -> str:
    """Route regctl calls for a single (non-index) image to nginx fixtures."""
    sub = args[0:2]
    if sub == ["manifest", "get"]:
        # Single manifest (no index) for layers/size.
        return _fixture("manifest_amd64_raw.json")
    if sub == ["manifest", "head"]:
        # Digest lookup for single-arch images whose ref is a tag, not a digest.
        return "sha256:aabbccdd\n"
    if sub == ["image", "inspect"]:
        return _fixture("image_inspect_nginx_amd64.json")
    if sub == ["tag", "ls"]:
        return _fixture("tag_ls.txt")
    raise AssertionError(f"Unexpected regctl call: {args}")


def test_oci_single_platform_report_validates():
    with patch(
        "regis.analyzers.oci.run_regctl", side_effect=_single_platform_dispatcher
    ):
        analyzer = OciAnalyzer()
        report = analyzer.analyze(_client(), "library/nginx", "1.27")

    # Report conforms to the oci schema.
    analyzer.validate(report)

    assert report["analyzer"] == "oci"
    assert report["repository"] == "library/nginx"
    assert report["tag"] == "1.27"
    assert len(report["platforms"]) == 1

    platform = report["platforms"][0]
    assert isinstance(platform["size"], int)
    assert isinstance(platform["layers_count"], int)
    assert isinstance(platform["env"], list)
    assert isinstance(platform["exposed_ports"], list)
    assert "80/tcp" in platform["exposed_ports"]
    # size = config.size (612) + sum(layer sizes) (3630321)
    assert platform["size"] == 612 + 3630321
    assert platform["layers_count"] == 1

    # Tags parsed from newline-separated output.
    assert "latest" in report["tags"]
    assert "3.20.10" in report["tags"]
    assert report["tags"] == [t for t in report["tags"] if t.strip()]


def test_oci_single_arch_digest_populated_via_manifest_head():
    """Single-arch images (tag ref) must have digest populated via manifest head."""
    manifest_head_called: list[list[str]] = []

    def dispatcher(_client_arg: object, args: list[str]) -> str:
        sub = args[0:2]
        if sub == ["manifest", "head"]:
            manifest_head_called.append(args)
            return "sha256:deadbeef\n"
        return _single_platform_dispatcher(_client_arg, args)

    with patch("regis.analyzers.oci.run_regctl", side_effect=dispatcher):
        analyzer = OciAnalyzer()
        report = analyzer.analyze(_client(), "library/nginx", "1.27")

    platform = report["platforms"][0]
    # Digest must be the stripped value returned by manifest head.
    assert platform["digest"] == "sha256:deadbeef"
    # manifest head was called exactly once (for the single-arch platform).
    assert len(manifest_head_called) == 1


def _multiarch_dispatcher(_client_arg: object, args: list[str]) -> str:
    """Route regctl calls for a multi-arch index."""
    sub = args[0:2]
    if sub == ["manifest", "get"]:
        if _has_platform_flag(args):
            # Per-platform manifest (digest ref) -> layers/size.
            return _fixture("manifest_amd64_raw.json")
        # Top-level index lookup by tag.
        return _fixture("index_raw.json")
    if sub == ["image", "inspect"]:
        return _fixture("image_inspect_amd64.json")
    if sub == ["tag", "ls"]:
        return _fixture("tag_ls.txt")
    # Multi-arch per-platform refs are already digests, so manifest head must
    # never be called here.
    raise AssertionError(f"Unexpected regctl call: {args}")


def test_oci_multiarch_filters_attestation_manifests():
    with patch("regis.analyzers.oci.run_regctl", side_effect=_multiarch_dispatcher):
        analyzer = OciAnalyzer()
        report = analyzer.analyze(_client(), "library/alpine", "3.20.10")

    analyzer.validate(report)

    # The index fixture has 16 manifests: 8 real + 8 attestation (unknown/unknown).
    assert len(report["platforms"]) == 8
    for platform in report["platforms"]:
        assert platform["architecture"] != "unknown"
        assert platform["os"] != "unknown"

    architectures = {p["architecture"] for p in report["platforms"]}
    assert "amd64" in architectures
    assert "arm64" in architectures


def test_oci_platform_override_single_inspect():
    captured: list[list[str]] = []

    def dispatcher(client_arg: object, args: list[str]) -> str:
        captured.append(args)
        return _single_platform_dispatcher(client_arg, args)

    with patch("regis.analyzers.oci.run_regctl", side_effect=dispatcher):
        analyzer = OciAnalyzer()
        report = analyzer.analyze(
            _client(), "library/nginx", "1.27", platform="linux/amd64"
        )

    analyzer.validate(report)
    assert len(report["platforms"]) == 1
    assert report["platforms"][0]["architecture"] == "amd64"
    assert report["platforms"][0]["os"] == "linux"
    # The platform flag is threaded through to regctl for the override.
    assert any(_has_platform_flag(a) for a in captured)


def test_oci_inspect_platform_handles_failures():
    """When both per-platform regctl calls fail, _inspect_platform falls back gracefully."""
    state = {"manifest_calls": 0}

    def dispatcher(_client_arg: object, args: list[str]) -> str:
        if args[0:2] == ["tag", "ls"]:
            return _fixture("tag_ls.txt")
        if args[0:2] == ["manifest", "get"]:
            state["manifest_calls"] += 1
            # First manifest fetch resolves media type (non-index, single manifest);
            # the per-platform fetch (second call) fails.
            if state["manifest_calls"] == 1:
                return _fixture("manifest_amd64_raw.json")
            raise RuntimeError("regctl boom")
        # image inspect fails.
        raise RuntimeError("regctl boom")

    with patch("regis.analyzers.oci.run_regctl", side_effect=dispatcher):
        analyzer = OciAnalyzer()
        report = analyzer.analyze(_client(), "library/nginx", "1.27")

    analyzer.validate(report)
    platform = report["platforms"][0]
    assert platform["layers_count"] == 0
    assert platform["size"] == 0
    assert platform["labels"] == {}
    assert platform["env"] == []
    assert platform["exposed_ports"] == []


def test_oci_tag_list_failure_is_non_fatal():
    def dispatcher(client_arg: object, args: list[str]) -> str:
        if args[0:2] == ["tag", "ls"]:
            raise RuntimeError("tag ls failed")
        return _single_platform_dispatcher(client_arg, args)

    with patch("regis.analyzers.oci.run_regctl", side_effect=dispatcher):
        analyzer = OciAnalyzer()
        report = analyzer.analyze(_client(), "library/nginx", "1.27")

    analyzer.validate(report)
    assert report["tags"] == []


def test_oci_docker_hub_registry_normalized_in_tag_ls():
    captured: list[list[str]] = []

    def dispatcher(client_arg: object, args: list[str]) -> str:
        captured.append(args)
        return _single_platform_dispatcher(client_arg, args)

    with patch("regis.analyzers.oci.run_regctl", side_effect=dispatcher):
        analyzer = OciAnalyzer()
        analyzer.analyze(_client("registry-1.docker.io"), "library/nginx", "1.27")

    tag_calls = [a for a in captured if a[0:2] == ["tag", "ls"]]
    assert tag_calls, "expected a tag ls call"
    # registry-1.docker.io must be normalized to docker.io.
    assert tag_calls[0][2] == "docker.io/library/nginx"


def test_platforms_supported_dedup_and_order():
    platforms = [
        {"os": "linux", "architecture": "amd64"},
        {"os": "linux", "architecture": "arm64"},
        {"os": "linux", "architecture": "amd64"},  # duplicate
    ]
    assert _platforms_supported(platforms) == ["linux/amd64", "linux/arm64"]


def test_platforms_supported_includes_variant():
    platforms = [
        {"os": "linux", "architecture": "arm64", "variant": "v8"},
        {"os": "linux", "architecture": "arm", "variant": "v7"},
    ]
    assert _platforms_supported(platforms) == ["linux/arm64/v8", "linux/arm/v7"]


def test_platforms_supported_skips_unknown_and_missing():
    platforms = [
        {"os": "unknown", "architecture": "unknown"},
        {"os": "linux", "architecture": "unknown"},
        {"os": "linux"},  # missing architecture
        {"architecture": "amd64"},  # missing os
        {"os": "linux", "architecture": "amd64"},
    ]
    assert _platforms_supported(platforms) == ["linux/amd64"]


def test_platforms_supported_empty():
    assert _platforms_supported([]) == []
