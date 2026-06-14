"""RegctlImageInspector — ImageInspector backed by the regctl CLI."""

from __future__ import annotations

import json
import subprocess  # nosec B404
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from regis.core.domain.errors import AnalyzerError, RegistryError
from regis.core.ports.image_inspector import ImageInspector
from regis.registry.client import RegistryClient
from regis.utils.regctl import image_ref, run_regctl


@contextmanager
def _as_registry_error() -> Iterator[None]:
    """Translate legacy regctl failures into the core RegistryError."""
    try:
        yield
    except (AnalyzerError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        raise RegistryError(str(exc)) from exc


class RegctlImageInspector(ImageInspector):
    """Adapts the regctl CLI to the ImageInspector port.

    A second ImageInspector implementation alongside RegistryImageInspector
    (which uses the HTTP API). Credentials and coordinates live in the injected
    RegistryClient. Per-platform index traversal that ``regctl --platform`` does
    in one call becomes analyzer domain logic in P3; this adapter exposes only the
    four reference/digest-based primitives. Not yet consumed by analyzers.
    """

    def __init__(self, client: RegistryClient) -> None:
        self._client = client

    def _repo_ref(self) -> str:
        registry = self._client.registry
        if registry == "registry-1.docker.io":
            registry = "docker.io"
        return f"{registry}/{self._client.repository}"

    def _ref(self, reference: str) -> str:
        return image_ref(self._client.registry, self._client.repository, reference)

    def list_tags(self) -> list[str]:
        with _as_registry_error():
            out = run_regctl(self._client, ["tag", "ls", self._repo_ref()])
        return [tag for tag in out.splitlines() if tag.strip()]

    def get_manifest(self, reference: str) -> dict[str, Any]:
        with _as_registry_error():
            out = run_regctl(
                self._client,
                ["manifest", "get", self._ref(reference), "--format", "raw-body"],
            )
            manifest: dict[str, Any] = json.loads(out)
        return manifest

    def get_blob(self, digest: str) -> dict[str, Any]:
        with _as_registry_error():
            out = run_regctl(self._client, ["blob", "get", self._repo_ref(), digest])
            blob: dict[str, Any] = json.loads(out)
        return blob

    def get_digest(self, reference: str) -> str | None:
        with _as_registry_error():
            out = run_regctl(self._client, ["manifest", "head", self._ref(reference)])
        return out.strip() or None
