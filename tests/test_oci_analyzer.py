"""Tests for the oci analyzer — using FakeImageInspector + make_ctx (hexagonal P3c)."""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

import jsonschema

from regis.analyzers.oci import OciAnalyzer, _platforms_supported
from regis.rules.evaluator import evaluate_rules
from tests.fakes import FakeImageInspector, make_ctx

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

# The real platform entries from the alpine index fixture (8 platforms).
_INDEX_REAL_ENTRIES: list[dict[str, Any]] = [
    {
        "digest": "sha256:c64c687cbea9300178b30c95835354e34c4e4febc4badfe27102879de0483b5e",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "platform": {"architecture": "amd64", "os": "linux"},
        "size": 1023,
    },
    {
        "digest": "sha256:37753b2965043543542cd9d48cba044151052ca14fa72e6cbec4edf2a1490599",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "platform": {"architecture": "arm", "os": "linux", "variant": "v6"},
        "size": 1024,
    },
    {
        "digest": "sha256:bd05c4d38cbeb5cfb34883906276560353a6b0282fb5c4b9dd3bd40f5143d7c3",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "platform": {"architecture": "arm", "os": "linux", "variant": "v7"},
        "size": 1024,
    },
    {
        "digest": "sha256:45e09956dc667c5eff3583c9d94830261fb1ca0be10a0a7db36266edf5de9e1d",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "platform": {"architecture": "arm64", "os": "linux", "variant": "v8"},
        "size": 1026,
    },
    {
        "digest": "sha256:4ec3ead63e75e791660b5abc4dc3bd85ebb6fc24a10d649ba05991bf34b5e80e",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "platform": {"architecture": "386", "os": "linux"},
        "size": 1019,
    },
    {
        "digest": "sha256:80529c2d621d6271966cfa680d104ca55349a3b1fc7a567bc7e25349a1f2f6cb",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "platform": {"architecture": "ppc64le", "os": "linux"},
        "size": 1026,
    },
    {
        "digest": "sha256:c47cbcc0d9c7f68d8e19c8e4eb50252ff9722e504108d69e8c36d510e921fc26",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "platform": {"architecture": "riscv64", "os": "linux"},
        "size": 1026,
    },
    {
        "digest": "sha256:856b20bf4946b5c8f43fc5b2ce46f39109914d9213a2832eb24cc01c76f27bbe",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "platform": {"architecture": "s390x", "os": "linux"},
        "size": 1022,
    },
]

# The 8 attestation entries (os/arch == unknown) — must be filtered out.
_INDEX_ATTESTATION_ENTRIES: list[dict[str, Any]] = [
    {
        "digest": "sha256:6243dec9286873e0392f0527f96c394684dc6fa12661f0bd19253dcd5561e70a",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "platform": {"architecture": "unknown", "os": "unknown"},
        "size": 838,
    },
    {
        "digest": "sha256:91f7e880a3f5e530a270a967c469f3e4c1e2aa410de3198b25a3bdb9d151ccc7",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "platform": {"architecture": "unknown", "os": "unknown"},
        "size": 566,
    },
    {
        "digest": "sha256:9ba6eec5a5535ea0bb7b3349150c33362479fa18027e38e4539bedeb2ff273b6",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "platform": {"architecture": "unknown", "os": "unknown"},
        "size": 838,
    },
    {
        "digest": "sha256:1db32a7978cab674f63e3f771e00e092017d50892822fbba4f338fefdd9ecb05",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "platform": {"architecture": "unknown", "os": "unknown"},
        "size": 838,
    },
    {
        "digest": "sha256:dca9fc0bda3467e7497cfd580f3719254ec841421a0d7ca90453efb0bea65140",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "platform": {"architecture": "unknown", "os": "unknown"},
        "size": 838,
    },
    {
        "digest": "sha256:53afc103e0e4333e074f7e9e998727e352cace15d15ded1c2f2bb1b053e8f849",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "platform": {"architecture": "unknown", "os": "unknown"},
        "size": 838,
    },
    {
        "digest": "sha256:d2e5111150653eec466eb4abfffb4c2865a83e5c40abf67b1f8d2b63b8c8473e",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "platform": {"architecture": "unknown", "os": "unknown"},
        "size": 838,
    },
    {
        "digest": "sha256:ba51d55642345137ba4ebf1a15623cbd26493c258e4215391f608667387247aa",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "platform": {"architecture": "unknown", "os": "unknown"},
        "size": 838,
    },
]

# The full OCI index manifest (index_raw.json equivalent).
_INDEX_MANIFEST: dict[str, Any] = {
    "mediaType": "application/vnd.oci.image.index.v1+json",
    "schemaVersion": 2,
    "manifests": _INDEX_REAL_ENTRIES + _INDEX_ATTESTATION_ENTRIES,
}

# Shared per-platform manifest (like manifest_amd64_raw.json).
# config.size = 612, one layer of size 3630321 → total size = 3630933.
_CFG_DIGEST = "sha256:bf8527eb54c3680e728d5b4b383a8ba730d72dae7236fbc8dff97ed6b224a731"
_PLATFORM_MANIFEST: dict[str, Any] = {
    "schemaVersion": 2,
    "mediaType": "application/vnd.oci.image.manifest.v1+json",
    "config": {
        "mediaType": "application/vnd.oci.image.config.v1+json",
        "digest": _CFG_DIGEST,
        "size": 612,
    },
    "layers": [
        {
            "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
            "digest": "sha256:25f1d6b1951ac8eb3740558fe94cb83d377bdadf95fd9f98b50d2e1b96130471",
            "size": 3630321,
        }
    ],
}

# Config blob (like image_inspect_amd64.json, but without Labels/User/ExposedPorts).
_CONFIG_BLOB: dict[str, Any] = {
    "architecture": "amd64",
    "os": "linux",
    "created": "2026-04-16T23:53:26.803599608Z",
    "config": {
        "Env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
        "Cmd": ["/bin/sh"],
        "WorkingDir": "/",
    },
}

# Tags from tag_ls.txt.
_TAGS = ["3.20.10", "3.21.0", "latest", "edge"]


def _make_multiarch_inspector() -> FakeImageInspector:
    """Build a FakeImageInspector for the multi-arch alpine 3.20.10 index scenario."""
    tag = "3.20.10"
    manifests: dict[str, Any] = {tag: _INDEX_MANIFEST}
    blobs: dict[str, Any] = {_CFG_DIGEST: _CONFIG_BLOB}
    # Each real platform digest → the shared per-platform manifest.
    for entry in _INDEX_REAL_ENTRIES:
        manifests[entry["digest"]] = _PLATFORM_MANIFEST
    return FakeImageInspector(manifests=manifests, blobs=blobs, tags=_TAGS)


def _make_single_arch_inspector(
    *,
    tag: str = "1.27",
    digest: str | None = "sha256:deadbeef",
    config_blob: dict[str, Any] | None = None,
) -> FakeImageInspector:
    """Build a FakeImageInspector for a single-arch (non-index) image."""
    cfg = config_blob or {
        "architecture": "amd64",
        "os": "linux",
        "created": "2025-04-16T14:50:31Z",
        "config": {
            "ExposedPorts": {"80/tcp": {}},
            "Env": [
                "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
            ],
            "Labels": {"maintainer": "NGINX Docker Maintainers"},
        },
    }
    # Non-index manifest keyed by tag.
    manifest: dict[str, Any] = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {
            "mediaType": "application/vnd.oci.image.config.v1+json",
            "digest": _CFG_DIGEST,
            "size": 612,
        },
        "layers": [
            {
                "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "digest": "sha256:25f1d6b1951ac8eb3740558fe94cb83d377bdadf95fd9f98b50d2e1b96130471",
                "size": 3630321,
            }
        ],
    }
    return FakeImageInspector(
        manifests={tag: manifest},
        blobs={_CFG_DIGEST: cfg},
        tags=_TAGS,
        digest=digest,
    )


# ---------------------------------------------------------------------------
# Schema / metadata
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Single-arch (non-index) image
# ---------------------------------------------------------------------------


def test_oci_single_platform_report_validates():
    inspector = _make_single_arch_inspector()
    ctx = make_ctx(inspector=inspector, repository="library/nginx", tag="1.27")
    analyzer = OciAnalyzer()
    report = analyzer.analyze(ctx)

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

    # Tags from FakeImageInspector.
    assert "latest" in report["tags"]
    assert "3.20.10" in report["tags"]
    assert report["tags"] == [t for t in report["tags"] if t.strip()]


def test_oci_single_arch_digest_populated_via_get_digest():
    """Single-arch images (tag ref) must have digest populated via inspector.get_digest."""
    inspector = _make_single_arch_inspector(digest="sha256:deadbeef")
    ctx = make_ctx(inspector=inspector, repository="library/nginx", tag="1.27")
    analyzer = OciAnalyzer()
    report = analyzer.analyze(ctx)

    platform = report["platforms"][0]
    assert platform["digest"] == "sha256:deadbeef"


def test_oci_single_arch_digest_populated_when_get_digest_returns_none():
    """When get_digest returns None (registry omits it), digest is empty string."""
    inspector = _make_single_arch_inspector(digest=None)
    ctx = make_ctx(inspector=inspector, repository="library/nginx", tag="1.27")
    analyzer = OciAnalyzer()
    report = analyzer.analyze(ctx)

    platform = report["platforms"][0]
    assert platform["digest"] == ""


# ---------------------------------------------------------------------------
# Multi-arch index image
# ---------------------------------------------------------------------------


def test_oci_multiarch_filters_attestation_manifests():
    inspector = _make_multiarch_inspector()
    ctx = make_ctx(inspector=inspector, repository="library/alpine", tag="3.20.10")
    analyzer = OciAnalyzer()
    report = analyzer.analyze(ctx)

    analyzer.validate(report)

    # The index has 16 entries: 8 real + 8 attestation (unknown/unknown).
    assert len(report["platforms"]) == 8
    for platform in report["platforms"]:
        assert platform["architecture"] != "unknown"
        assert platform["os"] != "unknown"

    architectures = {p["architecture"] for p in report["platforms"]}
    assert "amd64" in architectures
    assert "arm64" in architectures


def test_oci_multiarch_platform_digests_used_directly():
    """Per-platform refs in an index are already digests — get_digest must not be called."""
    call_log: list[str] = []

    class SpyInspector(FakeImageInspector):
        def get_digest(self, reference: str) -> str | None:
            call_log.append(reference)
            return super().get_digest(reference)

    base = _make_multiarch_inspector()
    inspector = SpyInspector(
        manifests=base._manifests,
        blobs=base._blobs,
        tags=base._tags,
    )
    ctx = make_ctx(inspector=inspector, repository="library/alpine", tag="3.20.10")
    OciAnalyzer().analyze(ctx)

    # Multi-arch per-platform refs start with sha256: — get_digest must not be called.
    assert call_log == [], f"unexpected get_digest calls: {call_log}"


def test_oci_multiarch_correct_per_platform_fields():
    """Each inspected platform carries correct fields from the manifest + blob."""
    inspector = _make_multiarch_inspector()
    ctx = make_ctx(inspector=inspector, repository="library/alpine", tag="3.20.10")
    report = OciAnalyzer().analyze(ctx)

    for platform in report["platforms"]:
        # From per-platform manifest (_PLATFORM_MANIFEST).
        assert platform["size"] == 612 + 3630321
        assert platform["layers_count"] == 1
        # From config blob (_CONFIG_BLOB).
        assert platform["created"] == "2026-04-16T23:53:26.803599608Z"
        assert isinstance(platform["env"], list)
        assert isinstance(platform["labels"], dict)
        assert isinstance(platform["exposed_ports"], list)
        # Digest = the platform entry digest (starts with sha256:).
        assert platform["digest"].startswith("sha256:")


# ---------------------------------------------------------------------------
# Platform override
# ---------------------------------------------------------------------------


def test_oci_platform_override_single_inspect():
    """With platform= on a non-index image, only one platform is inspected."""
    inspector = _make_single_arch_inspector()
    ctx = make_ctx(
        inspector=inspector,
        repository="library/nginx",
        tag="1.27",
        platform="linux/amd64",
    )
    analyzer = OciAnalyzer()
    report = analyzer.analyze(ctx)

    analyzer.validate(report)
    assert len(report["platforms"]) == 1
    assert report["platforms"][0]["architecture"] == "amd64"
    assert report["platforms"][0]["os"] == "linux"


def test_oci_platform_override_on_index_resolves_single_platform():
    """With platform= override on an index, pick_platform_digest resolves one entry."""
    inspector = _make_multiarch_inspector()
    ctx = make_ctx(
        inspector=inspector,
        repository="library/alpine",
        tag="3.20.10",
        platform="linux/amd64",
    )
    report = OciAnalyzer().analyze(ctx)

    assert len(report["platforms"]) == 1
    assert report["platforms"][0]["architecture"] == "amd64"
    assert report["platforms"][0]["os"] == "linux"
    assert report["platforms"][0]["digest"] == (
        "sha256:c64c687cbea9300178b30c95835354e34c4e4febc4badfe27102879de0483b5e"
    )


# ---------------------------------------------------------------------------
# Failure / resilience paths
# ---------------------------------------------------------------------------


def test_oci_inspect_platform_handles_failures():
    """When both per-platform inspector calls fail, _inspect_platform falls back gracefully."""

    class FailingInspector(FakeImageInspector):
        def __init__(self) -> None:
            # Non-index manifest for the top-level call.
            non_index = {
                "schemaVersion": 2,
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "config": {"digest": _CFG_DIGEST, "size": 0},
                "layers": [],
            }
            super().__init__(manifests={"1.27": non_index}, tags=list(_TAGS))

        def get_blob(self, digest: str) -> dict[str, Any]:
            raise RuntimeError("blob boom")

    inspector = FailingInspector()
    ctx = make_ctx(inspector=inspector, repository="library/nginx", tag="1.27")
    analyzer = OciAnalyzer()
    report = analyzer.analyze(ctx)

    analyzer.validate(report)
    platform = report["platforms"][0]
    assert platform["layers_count"] == 0
    assert platform["size"] == 0
    assert platform["labels"] == {}
    assert platform["env"] == []
    assert platform["exposed_ports"] == []


def test_oci_inspect_platform_layers_manifest_failure_uses_defaults():
    """When the second get_manifest call (layers/size, lines 371-376) raises,
    layers_count and size fall back to 0; other fields from section 1 are intact.

    Call order for a single-arch tag "1.27":
      1. analyze() line 258: get_manifest("1.27")        -> top-level media-type check
      2. _inspect_platform section 1: get_manifest("1.27") -> config blob path (succeeds)
      3. _inspect_platform section 2: get_manifest("1.27") -> layers path (must raise)

    Raise on the 3rd call to get_manifest("1.27") to hit the layers except block.
    """
    from regis.core.domain.errors import RegistryError

    _call_count: list[int] = [0]

    class ThirdManifestCallFailsInspector(FakeImageInspector):
        def get_manifest(self, reference: str) -> dict[str, Any]:
            if reference == "1.27":
                _call_count[0] += 1
                # 1st call: analyze() top-level check — succeeds.
                # 2nd call: _inspect_platform section 1 config blob — succeeds.
                # 3rd call: _inspect_platform section 2 layers — raise.
                if _call_count[0] >= 3:
                    raise RegistryError("injected manifest failure on layers fetch")
            return super().get_manifest(reference)

    inspector = ThirdManifestCallFailsInspector(
        manifests={"1.27": _PLATFORM_MANIFEST},
        blobs={_CFG_DIGEST: _CONFIG_BLOB},
        tags=list(_TAGS),
    )
    ctx = make_ctx(inspector=inspector, repository="library/nginx", tag="1.27")
    analyzer = OciAnalyzer()
    report = analyzer.analyze(ctx)

    analyzer.validate(report)
    platform = report["platforms"][0]
    # Section 2 fallback values (layers_count and size default to 0).
    assert platform["layers_count"] == 0
    assert platform["size"] == 0
    # Section 1 succeeded before section 2 failed — config fields are populated.
    assert platform["architecture"] == "amd64"
    assert platform["os"] == "linux"


def test_oci_inspect_platform_get_digest_failure_uses_empty_string():
    """When get_digest raises for a non-sha256 ref (lines 387-391), digest is set to ''.

    This path fires only when the ref is NOT a sha256: digest (single-arch tag path)
    and get_digest raises a RegistryError.
    """
    from regis.core.domain.errors import RegistryError

    class DigestFailsInspector(FakeImageInspector):
        def get_digest(self, reference: str) -> str | None:
            raise RegistryError("injected get_digest failure")

    inspector = DigestFailsInspector(
        manifests={"1.27": _PLATFORM_MANIFEST},
        blobs={_CFG_DIGEST: _CONFIG_BLOB},
        tags=list(_TAGS),
    )
    ctx = make_ctx(inspector=inspector, repository="library/nginx", tag="1.27")
    analyzer = OciAnalyzer()
    report = analyzer.analyze(ctx)

    analyzer.validate(report)
    platform = report["platforms"][0]
    # The fallback from the except block is an empty string.
    assert platform["digest"] == ""


def test_oci_tag_list_failure_is_non_fatal():
    class FailTagInspector(FakeImageInspector):
        def list_tags(self) -> list[str]:
            raise RuntimeError("tag ls failed")

    inspector = FailTagInspector(
        manifests={"1.27": _make_single_arch_inspector()._manifests.get("1.27", {})},
        blobs={_CFG_DIGEST: _CONFIG_BLOB},
    )
    ctx = make_ctx(inspector=inspector, repository="library/nginx", tag="1.27")
    analyzer = OciAnalyzer()
    report = analyzer.analyze(ctx)

    analyzer.validate(report)
    assert report["tags"] == []


# ---------------------------------------------------------------------------
# platforms_supported
# ---------------------------------------------------------------------------


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


def test_oci_report_includes_platforms_supported():
    inspector = _make_multiarch_inspector()
    ctx = make_ctx(inspector=inspector, repository="library/alpine", tag="3.20.10")
    analyzer = OciAnalyzer()
    report = analyzer.analyze(ctx)

    # New field is present and schema-valid.
    analyzer.validate(report)
    assert "platforms_supported" in report
    supported = report["platforms_supported"]
    assert isinstance(supported, list)
    assert all(isinstance(name, str) for name in supported)
    # Multi-arch index resolves at least amd64 and arm64 linux platforms.
    assert "linux/amd64" in supported
    # arm64 entry carries variant "v8", so expect the full form.
    assert any(name.startswith("linux/arm64") for name in supported)
    # No "unknown" platforms leak into the projection.
    assert all("unknown" not in name for name in supported)
    # The fixture resolves exactly 8 real platforms.
    assert len(supported) == 8


# ---------------------------------------------------------------------------
# Rule / criterion evaluation helpers
# ---------------------------------------------------------------------------


def _oci_report(supported: list[str]) -> dict[str, Any]:
    return {
        "request": {"registry": "docker.io", "analyzers": ["oci"]},
        "results": {"oci": {"platforms_supported": supported}},
    }


def _eval_oci_criterion(
    supported: list[str], criterion: str, platforms: list[str]
) -> dict[str, Any]:
    rules_def = {
        "rules": [
            {
                "provider": "oci",
                "criterion": criterion,
                "slug": "under-test",
                "options": {"platforms": platforms},
            }
        ]
    }
    res = evaluate_rules(_oci_report(supported), rules_def)
    return next(r for r in res["rules"] if r["slug"] == "under-test")


def test_platforms_required_pass_and_fail():
    # All required platforms are supported (extras allowed) -> pass.
    passed = _eval_oci_criterion(
        ["linux/amd64", "linux/arm64", "windows/amd64"],
        "platforms-required",
        ["linux/amd64", "linux/arm64"],
    )
    assert passed["passed"] is True

    # A required platform is missing -> fail.
    failed = _eval_oci_criterion(
        ["linux/amd64"],
        "platforms-required",
        ["linux/amd64", "linux/arm64"],
    )
    assert failed["passed"] is False


def test_platforms_whitelist_pass_and_fail():
    # Every supported platform is allowed -> pass.
    passed = _eval_oci_criterion(
        ["linux/amd64", "linux/arm64"],
        "platforms-whitelist",
        ["linux/amd64", "linux/arm64", "windows/amd64"],
    )
    assert passed["passed"] is True

    # A supported platform is not in the allowed set -> fail.
    failed = _eval_oci_criterion(
        ["linux/amd64", "linux/arm64"],
        "platforms-whitelist",
        ["linux/amd64"],
    )
    assert failed["passed"] is False


def test_platforms_blacklist_pass_and_fail():
    # No forbidden platform is supported -> pass.
    passed = _eval_oci_criterion(
        ["linux/amd64", "linux/arm64"],
        "platforms-blacklist",
        ["windows/amd64"],
    )
    assert passed["passed"] is True

    # A forbidden platform is supported -> fail.
    failed = _eval_oci_criterion(
        ["linux/amd64", "linux/arm64"],
        "platforms-blacklist",
        ["linux/arm64"],
    )
    assert failed["passed"] is False


def test_platforms_required_fails_when_none_supported():
    # Empty projection cannot satisfy a required platform -> fail.
    failed = _eval_oci_criterion([], "platforms-required", ["linux/amd64"])
    assert failed["passed"] is False


def test_platform_criteria_are_opt_in_by_default():
    # No implicit inheritance: with no playbook rules, nothing is evaluated.
    # The three platform-identity criteria (shipped with enable: False) require
    # an explicit binding -- and so does every other OCI criterion now, since
    # analyzer defaults are no longer auto-injected.
    report = _oci_report(["linux/amd64"])
    res = evaluate_rules(report)  # no rules_def -> nothing evaluated
    slugs = {r["slug"] for r in res["rules"]}
    assert "platforms-required" not in slugs
    assert "platforms-whitelist" not in slugs
    assert "platforms-blacklist" not in slugs
    # platforms-count is no longer auto-active either; it must be declared.
    assert "platforms-count" not in slugs


def test_platforms_binding_can_be_explicitly_disabled():
    rules_def = {
        "rules": [
            {
                "provider": "oci",
                "criterion": "platforms-required",
                "slug": "under-test",
                "enable": False,
                "options": {"platforms": ["linux/amd64"]},
            }
        ]
    }
    res = evaluate_rules(_oci_report(["linux/amd64"]), rules_def)
    assert not any(r["slug"] == "under-test" for r in res["rules"])
