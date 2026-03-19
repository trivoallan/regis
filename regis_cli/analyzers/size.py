"""Size analyzer — reports image size breakdown from manifest."""

from __future__ import annotations

import json
import logging
import subprocess
from typing import Any

from regis_cli.analyzers.base import AnalyzerError, BaseAnalyzer
from regis_cli.registry.client import RegistryClient

logger = logging.getLogger(__name__)


def _human_size(size_bytes: int) -> str:
    """Convert bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024  # type: ignore[assignment]
    return f"{size_bytes:.1f} TB"


class SizeAnalyzer(BaseAnalyzer):
    """Analyze compressed image size from manifest layers."""

    name = "size"
    schema_file = "size.schema.json"

    @staticmethod
    def _run_skopeo(client: RegistryClient, args: list[str]) -> str:
        """Run skopeo with the given arguments, injecting credentials if present."""
        cmd = ["skopeo"] + args
        if client.username and client.password:
            cmd.extend(["--creds", f"{client.username}:{client.password}"])

        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout

    def analyze(
        self,
        client: RegistryClient,
        repository: str,
        tag: str,
        platform: str | None = None,
    ) -> dict[str, Any]:
        registry = client.registry
        if registry == "registry-1.docker.io":
            registry = "docker.io"

        target = f"docker://{registry}/{repository}:{tag}"

        try:
            raw_stdout = self._run_skopeo(client, ["inspect", "--raw", target])
            manifest = json.loads(raw_stdout)
        except subprocess.CalledProcessError as e:
            msg = f"Skopeo inspect failed for {target}: {e.stderr}"
            logger.error(msg)
            raise AnalyzerError(msg) from e
        except Exception as e:
            msg = f"Failed to parse skopeo output for {target}: {e}"
            logger.error(msg)
            raise AnalyzerError(msg) from e

        media_type = manifest.get("mediaType", "")

        # Handle manifest list / OCI index.
        if "list" in media_type or "index" in media_type:
            return self._analyze_multiarch(
                client, registry, repository, tag, manifest, platform=platform
            )

        return self._analyze_single(repository, tag, manifest)

    def _analyze_single(
        self,
        repository: str,
        tag: str,
        manifest: dict[str, Any],
    ) -> dict[str, Any]:
        layers = manifest.get("layers", [])
        config_size = manifest.get("config", {}).get("size", 0)

        layer_sizes = [layer.get("size", 0) for layer in layers]
        total_compressed = sum(layer_sizes) + config_size

        return {
            "analyzer": self.name,
            "repository": repository,
            "tag": tag,
            "multi_arch": False,
            "total_compressed_bytes": total_compressed,
            "total_compressed_human": _human_size(total_compressed),
            "layer_count": len(layers),
            "config_size_bytes": config_size,
            "layers": [
                {
                    "index": i,
                    "digest": layer.get("digest", ""),
                    "size_bytes": s,
                    "size_human": _human_size(s),
                }
                for i, (s, layer) in enumerate(zip(layer_sizes, layers, strict=True))
            ],
            "platforms": None,
        }

    def _analyze_multiarch(
        self,
        client: RegistryClient,
        registry: str,
        repository: str,
        tag: str,
        manifest_list: dict[str, Any],
        platform: str | None = None,
    ) -> dict[str, Any]:
        entries = manifest_list.get("manifests", [])
        platforms = []

        # Filter platforms if override is provided
        if platform:
            if "/" in platform:
                os_override, arch_override = platform.split("/", 1)
            else:
                os_override, arch_override = "linux", platform

            # Filter entries to find matching platform
            entries = [
                e
                for e in entries
                if e.get("platform", {}).get("os") == os_override
                and e.get("platform", {}).get("architecture") == arch_override
            ]
            if not entries:
                logger.warning(f"Platform {platform} not found in manifest index")

        for entry in entries:
            if not isinstance(entry, dict):
                continue
            plat_info = entry.get("platform")
            if not isinstance(plat_info, dict):
                plat_info = {}

            arch = plat_info.get("architecture", "unknown")
            os_name = plat_info.get("os", "unknown")
            variant = plat_info.get("variant", "")
            platform_label = f"{os_name}/{arch}"
            if variant:
                platform_label += f"/{variant}"

            # Fetch size for this platform.
            digest = entry.get("digest")
            if not digest:
                continue

            target = f"docker://{registry}/{repository}@{digest}"

            try:
                raw_stdout = self._run_skopeo(client, ["inspect", "--raw", target])
                plat_manifest = json.loads(raw_stdout)

                plat_layers = plat_manifest.get("layers", [])
                plat_config_size = plat_manifest.get("config", {}).get("size", 0)
                plat_layer_sizes = [layer.get("size", 0) for layer in plat_layers]
                plat_total = sum(plat_layer_sizes) + plat_config_size
            except Exception:
                plat_total = entry.get("size", 0)
                plat_layer_sizes = []
                plat_config_size = 0

            platforms.append(
                {
                    "platform": platform_label,
                    "compressed_bytes": plat_total,
                    "compressed_human": _human_size(plat_total),
                    "layer_count": len(plat_layer_sizes),
                }
            )

        # Use first platform as representative total.
        total = platforms[0]["compressed_bytes"] if platforms else 0

        return {
            "analyzer": self.name,
            "repository": repository,
            "tag": tag,
            "multi_arch": True,
            "total_compressed_bytes": total,
            "total_compressed_human": _human_size(total),
            "layer_count": platforms[0]["layer_count"] if platforms else 0,
            "config_size_bytes": 0,
            "layers": [],
            "platforms": platforms,
        }

    def _empty(self, repository: str, tag: str) -> dict[str, Any]:
        return {
            "analyzer": self.name,
            "repository": repository,
            "tag": tag,
            "multi_arch": False,
            "total_compressed_bytes": 0,
            "total_compressed_human": "0.0 B",
            "layer_count": 0,
            "config_size_bytes": 0,
            "layers": [],
            "platforms": None,
        }
