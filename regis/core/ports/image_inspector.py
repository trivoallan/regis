"""ImageInspector port — read-only access to an OCI registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ImageInspector(ABC):
    """Port for inspecting an image in a registry."""

    @abstractmethod
    def list_tags(self) -> list[str]:
        """Return the repository's tags."""

    @abstractmethod
    def get_manifest(self, reference: str) -> dict[str, Any]:
        """Return the manifest for a tag or digest reference."""

    @abstractmethod
    def get_blob(self, digest: str) -> dict[str, Any]:
        """Return the parsed blob (typically an image config) for a digest."""

    @abstractmethod
    def get_digest(self, reference: str) -> str | None:
        """Return the content digest for a reference, or None if the registry omits it."""
