"""RegistryImageInspector — ImageInspector backed by the OCI RegistryClient."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from regis.core.domain.errors import RegistryError
from regis.core.ports.image_inspector import ImageInspector
from regis.registry.client import RegistryClient
from regis.registry.client import RegistryError as _ClientRegistryError


@contextmanager
def _as_core_registry_error() -> Iterator[None]:
    """Translate the legacy client RegistryError into the core RegistryError."""
    try:
        yield
    except _ClientRegistryError as exc:
        raise RegistryError(str(exc)) from exc


class RegistryImageInspector(ImageInspector):
    """Adapts the concrete :class:`RegistryClient` to the ImageInspector port.

    Credentials and connection state live in the injected client, not in the
    core. The per-thread factory that builds these lives in the composition
    root (P3). The client's ``tag`` parameter accepts a tag *or* a digest
    reference (the registry ``/manifests/<ref>`` endpoint handles both), so the
    port's wider ``reference`` contract is honored by positional pass-through.
    """

    def __init__(self, client: RegistryClient) -> None:
        self._client = client

    def list_tags(self) -> list[str]:
        with _as_core_registry_error():
            return self._client.list_tags()

    def get_manifest(self, reference: str) -> dict[str, Any]:
        with _as_core_registry_error():
            return self._client.get_manifest(reference)

    def get_blob(self, digest: str) -> dict[str, Any]:
        with _as_core_registry_error():
            return self._client.get_blob(digest)

    def get_digest(self, reference: str) -> str | None:
        with _as_core_registry_error():
            return self._client.get_digest(reference)
