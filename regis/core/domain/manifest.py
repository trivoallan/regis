"""Domain helpers for OCI index traversal over the ImageInspector port.

regctl's ``image inspect --platform`` resolves a platform from an index and
returns its image config in one call. The ImageInspector port exposes only the
reference/digest primitives, so that resolution lives here as domain logic
(P3). These helpers are pure given an injected ``ImageInspector``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from regis.core.domain.errors import RegistryError
from regis.core.ports.image_inspector import ImageInspector


def _is_index(manifest: Mapping[str, Any]) -> bool:
    media_type = manifest.get("mediaType", "")
    return "index" in media_type or "list" in media_type


def filter_real_platforms(
    entries: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Drop attestation/unknown entries (os/arch == 'unknown' or missing)."""
    real: list[dict[str, Any]] = []
    for entry in entries:
        plat = entry.get("platform", {})
        if plat.get("architecture") in (None, "unknown"):
            continue
        if plat.get("os") in (None, "unknown"):
            continue
        real.append(dict(entry))
    return real


def pick_platform_digest(
    index: Mapping[str, Any], os_name: str, arch: str, variant: str = ""
) -> str:
    """Return the digest of the index entry matching (os, arch[, variant])."""
    for entry in index.get("manifests", []):
        plat = entry.get("platform", {})
        if plat.get("os") == os_name and plat.get("architecture") == arch:
            if not variant or plat.get("variant", "") == variant:
                digest = entry.get("digest")
                if digest:
                    return str(digest)
    raise RegistryError(f"Platform {os_name}/{arch} not found in image index")


def resolve_platform_manifest(
    inspector: ImageInspector, reference: str, os_name: str, arch: str
) -> dict[str, Any]:
    """Return the single-platform manifest for *reference*.

    If *reference* is an index, pick the (os, arch) entry and fetch it; if it is
    already a single manifest, return it unchanged.
    """
    manifest = inspector.get_manifest(reference)
    if _is_index(manifest):
        digest = pick_platform_digest(manifest, os_name, arch)
        return inspector.get_manifest(digest)
    return manifest


def get_image_config(
    inspector: ImageInspector,
    reference: str,
    os_name: str = "linux",
    arch: str = "amd64",
) -> dict[str, Any]:
    """Return the OCI image config blob for *reference* (index-aware).

    Equivalent to ``regctl image inspect --platform os/arch``.
    """
    manifest = resolve_platform_manifest(inspector, reference, os_name, arch)
    config_digest = manifest.get("config", {}).get("digest")
    if not config_digest:
        raise RegistryError(f"No config digest in manifest for {reference}")
    return inspector.get_blob(str(config_digest))
