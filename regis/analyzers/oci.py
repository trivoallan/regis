"""OCI analyzer — per-platform image metadata and tag listing via ImageInspector."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from regis.analyzers.base import BaseAnalyzer
from regis.core.domain.context import AnalysisContext
from regis.core.domain.manifest import filter_real_platforms, pick_platform_digest
from regis.core.ports.image_inspector import ImageInspector

logger = logging.getLogger(__name__)

# Manifest media types indicating a multi-arch manifest list.
_INDEX_TYPES = {
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.index.v1+json",
}


def _platforms_supported(platforms: list[dict[str, Any]]) -> list[str]:
    """Project platform objects into canonical ``os/arch[/variant]`` strings.

    Skips entries whose ``os`` or ``architecture`` is missing or ``"unknown"``.
    Deduplicates while preserving first-seen order.
    """
    names: list[str] = []
    for platform in platforms:
        os_name = platform.get("os")
        arch = platform.get("architecture")
        if not os_name or not arch or os_name == "unknown" or arch == "unknown":
            continue
        name = f"{os_name}/{arch}"
        variant = platform.get("variant")
        if variant:
            name = f"{name}/{variant}"
        names.append(name)
    return list(dict.fromkeys(names))


class OciAnalyzer(BaseAnalyzer):
    """Fetch OCI metadata for an image using the ImageInspector port."""

    name = "oci"
    schema_file = "analyzer/oci.schema.json"
    uses_context = True

    @classmethod
    def default_criteria(cls) -> list[dict[str, Any]]:
        return [
            {
                "slug": "user-blacklist",
                "description": "Image must not run as root.",
                "level": "critical",
                "tags": ["security"],
                "params": {"forbidden_user": "root"},
                "condition": {
                    "!=": [
                        {"var": "results.oci.platforms.0.user"},
                        {"var": "criterion.params.forbidden_user"},
                    ]
                },
                "messages": {
                    "pass": "Image does not run as '${criterion.params.forbidden_user}'.",  # nosec B105
                    "fail": "Image configured to run as '${criterion.params.forbidden_user}'.",
                },
            },
            {
                "slug": "max-size",
                "description": "Image size is within limits.",
                "level": "warning",
                "tags": ["hygiene"],
                "params": {"max_mb": 1000},
                "condition": {
                    "<=": [
                        {"var": "results.oci.platforms.0.size"},
                        {"*": [{"var": "criterion.params.max_mb"}, 1048576]},
                    ]
                },
                "messages": {
                    "pass": "Image size is within limits (${results.oci.platforms.0.size} bytes).",  # nosec B105
                    "fail": "Image size exceeds ${criterion.params.max_mb} MB (${results.oci.platforms.0.size} bytes).",
                },
            },
            {
                "slug": "layers-count",
                "description": "Image has an acceptable number of layers.",
                "level": "warning",
                "tags": ["performance"],
                "params": {"max_layers": 30},
                "condition": {
                    "<=": [
                        {"var": "results.oci.platforms.0.layers_count"},
                        {"var": "criterion.params.max_layers"},
                    ]
                },
                "messages": {
                    "pass": "Image has ${results.oci.platforms.0.layers_count} layers.",  # nosec B105
                    "fail": "Image has too many layers (${results.oci.platforms.0.layers_count}). Max allowed: ${criterion.params.max_layers}.",
                },
            },
            {
                "slug": "tag-blacklist",
                "description": "Image tag should not be 'latest'.",
                "level": "warning",
                "tags": ["lifecycle"],
                "condition": {"!=": [{"var": "request.tag"}, "latest"]},
                "messages": {
                    "pass": "Image tag is not 'latest'.",  # nosec B105
                    "fail": "Image is using the 'latest' tag. Use immutable version tags instead.",
                },
            },
            {
                "slug": "platforms-count",
                "description": "Image should support multiple platforms.",
                "level": "info",
                "tags": ["compatibility"],
                "params": {"min_platforms": 2},
                "condition": {
                    ">=": [
                        {
                            "reduce": [
                                {"var": "results.oci.platforms"},
                                {"+": [1, {"var": "accumulator"}]},
                                0,
                            ]
                        },
                        {"var": "criterion.params.min_platforms"},
                    ]
                },
                "messages": {
                    "pass": "Image supports ${results.oci.platforms.length} platforms.",  # nosec B105
                    "fail": "Image only supports ${results.oci.platforms.length} platforms (min required: ${criterion.params.min_platforms}).",
                },
            },
            {
                "slug": "platforms-required",
                "enable": False,
                "description": "Image must support a required set of platforms.",
                "level": "warning",
                "tags": ["compatibility"],
                "params": {"platforms": ["linux/amd64", "linux/arm64"]},
                "condition": {
                    "contains_all": [
                        {"var": "results.oci.platforms_supported"},
                        {"var": "criterion.params.platforms"},
                    ]
                },
                "messages": {
                    "pass": "Image supports all required platforms.",  # nosec B105
                    "fail": "Image is missing required platforms (supported: ${results.oci.platforms_supported}; required: ${criterion.params.platforms}).",
                },
            },
            {
                "slug": "platforms-whitelist",
                "enable": False,
                "description": "Image must only support allowed platforms.",
                "level": "warning",
                "tags": ["compatibility"],
                "params": {"platforms": ["linux/amd64", "linux/arm64"]},
                "condition": {
                    "subset": [
                        {"var": "results.oci.platforms_supported"},
                        {"var": "criterion.params.platforms"},
                    ]
                },
                "messages": {
                    "pass": "All supported platforms are allowed.",  # nosec B105
                    "fail": "Image supports disallowed platforms: ${results.oci.platforms_supported} (allowed: ${criterion.params.platforms}).",
                },
            },
            {
                "slug": "platforms-blacklist",
                "enable": False,
                "description": "Image must not support forbidden platforms.",
                "level": "warning",
                "tags": ["compatibility"],
                "params": {"platforms": ["windows/amd64"]},
                "condition": {
                    "!": {
                        "intersects": [
                            {"var": "results.oci.platforms_supported"},
                            {"var": "criterion.params.platforms"},
                        ]
                    }
                },
                "messages": {
                    "pass": "Image supports no forbidden platforms.",  # nosec B105
                    "fail": "Image supports forbidden platforms: ${results.oci.platforms_supported} (forbidden: ${criterion.params.platforms}).",
                },
            },
            {
                "slug": "exposed-ports-whitelist",
                "description": "Image exposes permitted ports.",
                "level": "warning",
                "tags": ["security"],
                "params": {"allowed_ports": ["80", "443"]},
                "condition": {
                    "subset": [
                        {"var": "results.oci.platforms.0.exposed_ports"},
                        {"var": "criterion.params.allowed_ports"},
                    ]
                },
                "messages": {
                    "pass": "All exposed ports are allowed.",  # nosec B105
                    "fail": "Image exposes unauthorized ports: ${results.oci.platforms.0.exposed_ports}.",
                },
            },
            {
                "slug": "required-labels",
                "description": "Image must have required OCI labels.",
                "level": "warning",
                "tags": ["metadata"],
                "params": {"labels": ["org.opencontainers.image.source"]},
                "condition": {
                    "contains_all": [
                        {"keys": [{"var": "results.oci.platforms.0.labels"}]},
                        {"var": "criterion.params.labels"},
                    ]
                },
                "messages": {
                    "pass": "All required labels are present.",  # nosec B105
                    "fail": "Image is missing one or more required labels: ${criterion.params.labels}.",
                },
            },
            {
                "slug": "env-blacklist",
                "description": "Image must not contain forbidden environment variables.",
                "level": "critical",
                "tags": ["security"],
                "params": {"keys": ["DEBUG", "SECRET_KEY"]},
                "condition": {
                    "!": {
                        "env_contains": [
                            {"var": "results.oci.platforms.0.env"},
                            {"var": "criterion.params.keys"},
                        ]
                    }
                },
                "messages": {
                    "pass": "No forbidden environment variables found.",  # nosec B105
                    "fail": "Image contains one or more forbidden environment variables.",
                },
            },
        ]

    def analyze(  # type: ignore[override]
        self,
        ctx: AnalysisContext,
    ) -> dict[str, Any]:
        """Return per-platform OCI metadata and the repository tag list."""
        tag = ctx.image.tag
        repository = ctx.image.repository
        platform_override = ctx.image.platform

        top = ctx.inspector.get_manifest(tag)
        media_type = top.get("mediaType", "")
        platforms: list[dict[str, Any]] = []

        if platform_override:
            os_name, arch = (
                platform_override.split("/", 1)
                if "/" in platform_override
                else ("linux", platform_override)
            )
            platforms.append(
                self._inspect_platform(
                    ctx.inspector,
                    tag,
                    {"os": os_name, "architecture": arch},
                )
            )
        elif media_type in _INDEX_TYPES:
            entries = filter_real_platforms(top.get("manifests", []))
            max_workers = min(10, len(entries) or 1)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(
                        self._inspect_platform,
                        ctx.inspector,
                        e.get("digest", ""),
                        e.get("platform", {}),
                    )
                    for e in entries
                ]
                for future in futures:
                    try:
                        platforms.append(future.result())
                    except Exception as exc:
                        logger.error("Failed to inspect platform: %s", exc)
        else:
            platforms.append(self._inspect_platform(ctx.inspector, tag, {}))

        tags: list[str] = []
        try:
            tags = [t for t in ctx.inspector.list_tags() if t.strip()]
        except Exception as exc:
            logger.warning("Could not fetch tag list for %s: %s", repository, exc)

        return {
            "analyzer": self.name,
            "repository": repository,
            "tag": tag,
            "platforms": platforms,
            "platforms_supported": _platforms_supported(platforms),
            "tags": tags,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _inspect_platform(
        self,
        inspector: ImageInspector,
        ref: str,
        platform_info: dict[str, Any],
    ) -> dict[str, Any]:
        """Inspect one platform: config blob + manifest."""
        result: dict[str, Any] = {
            "architecture": platform_info.get("architecture", "unknown"),
            "os": platform_info.get("os", "unknown"),
        }
        if "variant" in platform_info:
            result["variant"] = platform_info["variant"]

        # 1. Config blob: created, labels, user, env, exposed_ports, arch, os.
        try:
            m = inspector.get_manifest(ref)
            # If the ref resolved to an index (tag + platform override path),
            # pick the matching platform entry and fetch its manifest.
            if m.get("mediaType", "") in _INDEX_TYPES:
                platform_digest = pick_platform_digest(
                    m,
                    result["os"],
                    result["architecture"],
                )
                ref = platform_digest
                m = inspector.get_manifest(ref)

            cfg_digest = (m.get("config") or {}).get("digest", "")
            cfg_blob = inspector.get_blob(cfg_digest) if cfg_digest else {}
            cfg = cfg_blob.get("config", {}) or {}
            result["created"] = cfg_blob.get("created")
            result["labels"] = cfg.get("Labels") or {}
            result["user"] = cfg.get("User", "") or ""
            result["env"] = cfg.get("Env", []) or []
            result["exposed_ports"] = list((cfg.get("ExposedPorts") or {}).keys())
            if result["architecture"] == "unknown":
                result["architecture"] = cfg_blob.get("architecture", "unknown")
            if result["os"] == "unknown":
                result["os"] = cfg_blob.get("os", "unknown")
        except Exception:
            logger.debug(
                "inspector get_blob/get_manifest failed for %s", ref, exc_info=True
            )
            result.setdefault("labels", {})
            result.setdefault("user", "unknown")
            result.setdefault("env", [])
            result.setdefault("exposed_ports", [])

        # 2. Manifest: layers_count, size.
        try:
            manifest = inspector.get_manifest(ref)
            layers = manifest.get("layers", [])
            result["layers_count"] = len(layers)
            config_size = (manifest.get("config", {}) or {}).get("size", 0)
            result["size"] = config_size + sum(layer.get("size", 0) for layer in layers)
        except Exception:
            logger.debug(
                "inspector get_manifest (layers) failed for %s", ref, exc_info=True
            )
            result.setdefault("layers_count", 0)
            result.setdefault("size", 0)

        # 3. Digest: use the ref directly when it is already a digest; otherwise
        #    fetch it via get_digest so single-arch images are not left with
        #    an empty digest.
        if not result.get("digest"):
            if ref.startswith("sha256:"):
                result["digest"] = ref
            else:
                try:
                    result["digest"] = inspector.get_digest(ref) or ""
                except Exception:
                    logger.debug(
                        "inspector get_digest failed for %s", ref, exc_info=True
                    )
                    result["digest"] = ""

        return result
