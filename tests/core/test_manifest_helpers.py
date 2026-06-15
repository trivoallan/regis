"""Tests for the domain index-traversal helpers."""

from __future__ import annotations

import pytest

from regis.core.domain.errors import RegistryError
from regis.core.domain.manifest import (
    filter_real_platforms,
    get_image_config,
    pick_platform_digest,
    resolve_platform_manifest,
)
from tests.fakes import FakeImageInspector

_INDEX = {
    "mediaType": "application/vnd.oci.image.index.v1+json",
    "manifests": [
        {"digest": "sha256:amd", "platform": {"os": "linux", "architecture": "amd64"}},
        {
            "digest": "sha256:arm",
            "platform": {"os": "linux", "architecture": "arm64", "variant": "v8"},
        },
        {
            "digest": "sha256:att",
            "platform": {"os": "unknown", "architecture": "unknown"},
        },
    ],
}
_PLAT_MANIFEST = {
    "mediaType": "single",
    "config": {"digest": "sha256:cfg", "size": 7},
    "layers": [{"size": 10}],
}
_CONFIG = {"created": "2024-01-01T00:00:00Z", "config": {"Labels": {"k": "v"}}}


def test_pick_platform_digest_matches_os_arch_variant():
    assert pick_platform_digest(_INDEX, "linux", "amd64") == "sha256:amd"
    assert pick_platform_digest(_INDEX, "linux", "arm64", "v8") == "sha256:arm"


def test_pick_platform_digest_missing_raises():
    with pytest.raises(RegistryError, match="windows/amd64"):
        pick_platform_digest(_INDEX, "windows", "amd64")


def test_resolve_platform_manifest_traverses_index():
    insp = FakeImageInspector(
        manifests={"the-tag": _INDEX, "sha256:amd": _PLAT_MANIFEST}
    )
    assert (
        resolve_platform_manifest(insp, "the-tag", "linux", "amd64") == _PLAT_MANIFEST
    )


def test_resolve_platform_manifest_passthrough_single():
    insp = FakeImageInspector(manifests={"the-tag": _PLAT_MANIFEST})
    assert (
        resolve_platform_manifest(insp, "the-tag", "linux", "amd64") == _PLAT_MANIFEST
    )


def test_get_image_config_fetches_config_blob():
    insp = FakeImageInspector(
        manifests={"the-tag": _INDEX, "sha256:amd": _PLAT_MANIFEST},
        blobs={"sha256:cfg": _CONFIG},
    )
    assert get_image_config(insp, "the-tag", "linux", "amd64") == _CONFIG


def test_filter_real_platforms_drops_attestations():
    out = filter_real_platforms(_INDEX["manifests"])
    assert [e["digest"] for e in out] == ["sha256:amd", "sha256:arm"]


def test_filter_real_platforms_drops_unknown_os():
    entries = [
        {"digest": "sha256:ok", "platform": {"os": "linux", "architecture": "amd64"}},
        {
            "digest": "sha256:bad",
            "platform": {"os": "unknown", "architecture": "amd64"},
        },
    ]
    out = filter_real_platforms(entries)
    assert [e["digest"] for e in out] == ["sha256:ok"]


def test_get_image_config_raises_when_no_config_digest():
    manifest_no_cfg = {"mediaType": "single", "layers": [{"size": 10}]}
    insp = FakeImageInspector(manifests={"the-tag": manifest_no_cfg})
    with pytest.raises(RegistryError, match="No config digest"):
        get_image_config(insp, "the-tag")
