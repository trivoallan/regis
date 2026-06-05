"""OCI analyzer — per-platform image metadata and tag listing using regctl."""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from regis.analyzers.base import BaseAnalyzer
from regis.registry.client import RegistryClient
from regis.utils.regctl import image_ref, run_regctl

logger = logging.getLogger(__name__)

# Manifest media types indicating a multi-arch manifest list.
_INDEX_TYPES = {
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.index.v1+json",
}


def _norm(registry: str) -> str:
    """Normalize the Docker Hub API host to its canonical name."""
    return "docker.io" if registry == "registry-1.docker.io" else registry


class OciAnalyzer(BaseAnalyzer):
    """Fetch OCI metadata for an image using regctl: per-platform details and tags."""

    name = "oci"
    schema_file = "analyzer/oci.schema.json"

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

    def analyze(
        self,
        client: RegistryClient,
        repository: str,
        tag: str,
        platform: str | None = None,
    ) -> dict[str, Any]:
        """Return per-platform OCI metadata and the repository tag list."""
        registry = client.registry
        raw = run_regctl(
            client,
            [
                "manifest",
                "get",
                image_ref(registry, repository, tag),
                "--format",
                "raw-body",
            ],
        )
        manifest = json.loads(raw)
        media_type = manifest.get("mediaType", "")
        platforms: list[dict[str, Any]] = []

        if platform:
            os_name, arch = (
                platform.split("/", 1) if "/" in platform else ("linux", platform)
            )
            platforms.append(
                self._inspect_platform(
                    client,
                    registry,
                    repository,
                    tag,
                    {"os": os_name, "architecture": arch},
                )
            )
        elif media_type in _INDEX_TYPES:
            # Skip buildkit attestation manifests (platform os/arch == "unknown").
            entries = [
                e
                for e in manifest.get("manifests", [])
                if e.get("platform", {}).get("architecture") not in (None, "unknown")
                and e.get("platform", {}).get("os") not in (None, "unknown")
            ]
            max_workers = min(10, len(entries) or 1)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(
                        self._inspect_platform,
                        client,
                        registry,
                        repository,
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
            platforms.append(
                self._inspect_platform(client, registry, repository, tag, {})
            )

        tags: list[str] = []
        try:
            tags_out = run_regctl(
                client, ["tag", "ls", f"{_norm(registry)}/{repository}"]
            )
            tags = [t for t in tags_out.splitlines() if t.strip()]
        except Exception as exc:
            logger.warning("Could not fetch tag list for %s: %s", repository, exc)

        return {
            "analyzer": self.name,
            "repository": repository,
            "tag": tag,
            "platforms": platforms,
            "tags": tags,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _inspect_platform(
        self,
        client: RegistryClient,
        registry: str,
        repository: str,
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

        image_reference = image_ref(registry, repository, ref)
        plat: str | None = None
        if result["architecture"] != "unknown" and result["os"] != "unknown":
            plat = f"{result['os']}/{result['architecture']}"
            if result.get("variant"):
                plat = f"{plat}/{result['variant']}"

        # 1. Config blob: created, labels, user, env, exposed_ports, arch, os.
        try:
            args = ["image", "inspect", image_reference]  # default output is JSON
            if plat:
                args += ["--platform", plat]
            config = json.loads(run_regctl(client, args))
            cfg = config.get("config", {}) or {}
            result["created"] = config.get("created")
            result["labels"] = cfg.get("Labels") or {}
            result["user"] = cfg.get("User", "") or ""
            result["env"] = cfg.get("Env", []) or []
            result["exposed_ports"] = list((cfg.get("ExposedPorts") or {}).keys())
            if result["architecture"] == "unknown":
                result["architecture"] = config.get("architecture", "unknown")
            if result["os"] == "unknown":
                result["os"] = config.get("os", "unknown")
        except Exception:
            logger.debug(
                "regctl image inspect failed for %s", image_reference, exc_info=True
            )
            result.setdefault("labels", {})
            result.setdefault("user", "unknown")
            result.setdefault("env", [])
            result.setdefault("exposed_ports", [])

        # 2. Manifest: layers_count, size, digest.
        try:
            m_args = ["manifest", "get", image_reference, "--format", "raw-body"]
            if plat:
                m_args += ["--platform", plat]
            manifest = json.loads(run_regctl(client, m_args))
            layers = manifest.get("layers", [])
            result["layers_count"] = len(layers)
            config_size = (manifest.get("config", {}) or {}).get("size", 0)
            result["size"] = config_size + sum(layer.get("size", 0) for layer in layers)
        except Exception:
            logger.debug(
                "regctl manifest get failed for %s", image_reference, exc_info=True
            )
            result.setdefault("layers_count", 0)
            result.setdefault("size", 0)

        # 3. Digest: use the ref directly when it is already a digest; otherwise
        #    fetch it via `manifest head` so single-arch images are not left with
        #    an empty digest (raw manifest body has no top-level "digest" field).
        if not result.get("digest"):
            if ref.startswith("sha256:"):
                result["digest"] = ref
            else:
                try:
                    head_args = ["manifest", "head", image_reference]
                    if plat:
                        head_args += ["--platform", plat]
                    result["digest"] = run_regctl(client, head_args).strip()
                except Exception:
                    logger.debug(
                        "regctl manifest head failed for %s",
                        image_reference,
                        exc_info=True,
                    )
                    result["digest"] = ""

        return result
