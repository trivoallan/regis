"""Skopeo analyzer — provides raw image metadata and platform details using skopeo."""

from __future__ import annotations

import json
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from regis_cli.analyzers.base import AnalyzerError, BaseAnalyzer
from regis_cli.registry.client import RegistryClient

logger = logging.getLogger(__name__)

# Manifest media types indicating a multi-arch manifest list.
_INDEX_TYPES = {
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.index.v1+json",
}

# Default timeout for Skopeo calls (seconds)
DEFAULT_TIMEOUT = 60


class SkopeoAnalyzer(BaseAnalyzer):
    """Fetch metadata for a Docker image using skopeo. Provides raw inspect data and structured platform details."""

    name = "skopeo"
    schema_file = "analyzer/skopeo.schema.json"

    @classmethod
    def default_rules(cls) -> list[dict[str, Any]]:
        return [
            {
                "slug": "skopeo.no-root",
                "description": "Image must not run as root.",
                "level": "critical",
                "tags": ["security"],
                "params": {"forbidden_user": "root"},
                "condition": {
                    "!=": [
                        {"var": "results.skopeo.platforms.0.user"},
                        {"var": "rule.params.forbidden_user"},
                    ]
                },
                "messages": {
                    "pass": "Image does not run as '${rule.params.forbidden_user}'.",  # nosec B105
                    "fail": "Image configured to run as '${rule.params.forbidden_user}'.",
                },
            },
            {
                "slug": "skopeo.max-size",
                "description": "Image size is within limits.",
                "level": "warning",
                "tags": ["hygiene"],
                "params": {"max_mb": 1000},
                "condition": {
                    "<=": [
                        {"var": "results.skopeo.platforms.0.size"},
                        {"*": [{"var": "rule.params.max_mb"}, 1048576]},
                    ]
                },
                "messages": {
                    "pass": "Image size is within limits (${results.skopeo.platforms.0.size} bytes).",  # nosec B105
                    "fail": "Image size exceeds ${rule.params.max_mb} MB (${results.skopeo.platforms.0.size} bytes).",
                },
            },
            {
                "slug": "skopeo.max-layers",
                "description": "Image has an acceptable number of layers.",
                "level": "warning",
                "tags": ["performance"],
                "params": {"max_layers": 30},
                "condition": {
                    "<=": [
                        {"var": "results.skopeo.platforms.0.layers_count"},
                        {"var": "rule.params.max_layers"},
                    ]
                },
                "messages": {
                    "pass": "Image has ${results.skopeo.platforms.0.layers_count} layers.",  # nosec B105
                    "fail": "Image has too many layers (${results.skopeo.platforms.0.layers_count}). Max allowed: ${rule.params.max_layers}.",
                },
            },
            {
                "slug": "skopeo.tag-not-latest",
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
                "slug": "skopeo.multi-arch",
                "description": "Image should support multiple platforms.",
                "level": "info",
                "tags": ["compatibility"],
                "params": {"min_platforms": 2},
                "condition": {
                    ">=": [
                        {
                            "reduce": [
                                {"var": "results.skopeo.platforms"},
                                {"+": [1, {"var": "accumulator"}]},
                                0,
                            ]
                        },
                        {"var": "rule.params.min_platforms"},
                    ]
                },
                "messages": {
                    "pass": "Image supports ${results.skopeo.platforms.length} platforms.",  # nosec B105
                    "fail": "Image only supports ${results.skopeo.platforms.length} platforms (min required: ${rule.params.min_platforms}).",
                },
            },
            {
                "slug": "skopeo.exposed-ports",
                "description": "Image exposes permitted ports.",
                "level": "warning",
                "tags": ["security"],
                "params": {"allowed_ports": ["80", "443"]},
                "condition": {
                    "subset": [
                        {"var": "results.skopeo.platforms.0.exposed_ports"},
                        {"var": "rule.params.allowed_ports"},
                    ]
                },
                "messages": {
                    "pass": "All exposed ports are allowed.",  # nosec B105
                    "fail": "Image exposes unauthorized ports: ${results.skopeo.platforms.0.exposed_ports}.",
                },
            },
            {
                "slug": "skopeo.required-labels",
                "description": "Image must have required OCI labels.",
                "level": "warning",
                "tags": ["metadata"],
                "params": {"labels": ["org.opencontainers.image.source"]},
                "condition": {
                    "contains_all": [
                        {"keys": [{"var": "results.skopeo.platforms.0.labels"}]},
                        {"var": "rule.params.labels"},
                    ]
                },
                "messages": {
                    "pass": "All required labels are present.",  # nosec B105
                    "fail": "Image is missing one or more required labels: ${rule.params.labels}.",
                },
            },
            {
                "slug": "skopeo.forbidden-env",
                "description": "Image must not contain forbidden environment variables.",
                "level": "critical",
                "tags": ["security"],
                "params": {"keys": ["DEBUG", "SECRET_KEY"]},
                "condition": {
                    "!": {
                        "env_contains": [
                            {"var": "results.skopeo.platforms.0.env"},
                            {"var": "rule.params.keys"},
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
        """Return a report with raw skopeo inspect data and per-platform metadata."""
        # 'registry-1.docker.io' -> 'docker.io' for skopeo compatibility
        registry = client.registry
        if registry == "registry-1.docker.io":
            registry = "docker.io"

        target = f"docker://{registry}/{repository}:{tag}"

        # 1. Fetch raw manifest (to see if it's an index)
        try:
            raw_manifest_stdout = self._run_skopeo(client, ["inspect", "--raw", target])
            manifest = json.loads(raw_manifest_stdout)
        except subprocess.CalledProcessError as e:
            msg = f"Skopeo inspect --raw failed for {target}: {e.stderr}"
            logger.error(msg)
            raise AnalyzerError(msg) from e
        except Exception as e:
            msg = f"Failed to fetch raw manifest for {target}: {e}"
            logger.error(msg)
            raise AnalyzerError(msg) from e

        # 2. Resolve platforms
        media_type = manifest.get("mediaType", "")
        platforms: list[dict[str, Any]] = []

        # 3. Handle platform override
        if platform:
            if "/" in platform:
                os_name, arch = platform.split("/", 1)
            else:
                os_name, arch = "linux", platform

            # Find the specific platform in the manifest or assume it exists
            # For brevity and robustness, we explicitly inspect the requested platform.
            detail = self._inspect_platform(
                client, registry, repository, tag, {"os": os_name, "architecture": arch}
            )
            platforms.append(detail)
        elif media_type in _INDEX_TYPES:
            # Multi-arch image — iterate over each platform manifest in parallel.
            entries = manifest.get("manifests", [])
            # Limit workers to avoid overwhelming the system
            max_workers = min(10, len(entries) or 1)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for entry in entries:
                    platform_info = entry.get("platform", {})
                    digest = entry.get("digest", "")
                    futures.append(
                        executor.submit(
                            self._inspect_platform,
                            client,
                            registry,
                            repository,
                            digest,
                            platform_info,
                        )
                    )
                for future in futures:
                    try:
                        platforms.append(future.result())
                    except Exception as e:
                        logger.error("Failed to inspect platform: %s", e)
        else:
            # Single-platform manifest or fallback.
            detail = self._inspect_platform(client, registry, repository, tag, {})
            # If we already have the raw manifest with layers, use it.
            if "layers" in manifest:
                detail["layers_count"] = len(manifest["layers"])
            platforms.append(detail)

        # 4. Fetch primary inspect data (raw metadata) if NOT an index and NO platform override.
        primary_metadata: dict[str, Any] = {}
        if not platform and media_type not in _INDEX_TYPES:
            try:
                primary_inspect_stdout = self._run_skopeo(client, ["inspect", target])
                primary_metadata = json.loads(primary_inspect_stdout)
            except Exception as e:
                logger.warning(
                    "Could not fetch primary inspect data for %s: %s", target, e
                )

        # 4. List tags
        tags: list[str] = []
        try:
            # skopeo list-tags docker://registry/repository
            list_tags_target = f"docker://{registry}/{repository}"
            list_tags_stdout = self._run_skopeo(client, ["list-tags", list_tags_target])
            tags = json.loads(list_tags_stdout).get("Tags", [])
        except Exception as e:
            logger.warning("Could not fetch tag list for %s: %s", repository, e)

        return {
            "analyzer": self.name,
            "repository": repository,
            "tag": tag,
            "platforms": platforms,
            "inspect": primary_metadata,
            "tags": tags,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _run_skopeo(client: RegistryClient, args: list[str]) -> str:
        """Run skopeo with the given arguments, injecting credentials if present."""
        cmd = ["skopeo"] + args
        if client.username and client.password:
            cmd.extend(["--creds", f"{client.username}:{client.password}"])

        logger.debug("Running skopeo: %s", " ".join(cmd))
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=DEFAULT_TIMEOUT,
            )
            return res.stdout
        except subprocess.CalledProcessError as e:
            # Ensure we have stderr in the error message
            raise e from None
        except FileNotFoundError:
            raise AnalyzerError(
                "skopeo not found. Ensure it is installed and in PATH."
            ) from None

    def _inspect_platform(
        self,
        client: RegistryClient,
        registry: str,
        repository: str,
        ref: str,
        platform_info: dict[str, Any],
    ) -> dict[str, Any]:
        """Inspect a single platform by running skopeo inspect."""
        result: dict[str, Any] = {
            "architecture": platform_info.get("architecture", "unknown"),
            "os": platform_info.get("os", "unknown"),
        }

        if ref.startswith("sha256:"):
            result["digest"] = ref
            target = f"docker://{registry}/{repository}@{ref}"
        else:
            target = f"docker://{registry}/{repository}:{ref}"

        if "variant" in platform_info:
            result["variant"] = platform_info["variant"]

        # 1. Run high-level inspect to get Architecture, Os, Labels, Created, and Layers count.
        args = ["inspect"]
        if result["os"] != "unknown":
            args.extend(["--override-os", result["os"]])
        if result["architecture"] != "unknown":
            args.extend(["--override-arch", result["architecture"]])
        args.append(target)

        try:
            inspect_stdout = self._run_skopeo(client, args)
            data = json.loads(inspect_stdout)

            result["created"] = data.get("Created")
            result["labels"] = data.get("Labels") or {}
            result["layers_count"] = len(data.get("Layers", []))
            result["size"] = data.get("Size", 0)

            # Extract exposed ports if available
            # Skopeo inspect sometimes has these in different places depending on version/source
            # Usually in a Config object if present.
            config = data.get("Config", {}) or {}
            result["exposed_ports"] = list((config.get("ExposedPorts") or {}).keys())
            result["env"] = config.get("Env", [])

            if result["architecture"] == "unknown":
                result["architecture"] = data.get("Architecture", "unknown")
            if result["os"] == "unknown":
                result["os"] = data.get("Os", "unknown")
            if "variant" not in result or not result["variant"]:
                result["variant"] = data.get("Variant")
            if "digest" not in result or not result["digest"]:
                result["digest"] = data.get("Digest")

        except subprocess.CalledProcessError as e:
            logger.debug("Skopeo command failed for %s: %s", target, e.stderr)
        except Exception:
            logger.debug("Could not inspect platform %s", target, exc_info=True)

        # 2. Run --config inspect to get the User field
        config_args = ["inspect", "--config"]
        if result["os"] != "unknown":
            config_args.extend(["--override-os", result["os"]])
        if result["architecture"] != "unknown":
            config_args.extend(["--override-arch", result["architecture"]])
        config_args.append(target)

        try:
            config_stdout = self._run_skopeo(client, config_args)
            config_data = json.loads(config_stdout)
            # The User field is usually in the 'config' section of the config blob
            result["user"] = config_data.get("config", {}).get("User", "")
        except Exception:
            logger.debug(
                "Could not fetch config for platform %s", target, exc_info=True
            )
            result["user"] = "unknown"

        return result
