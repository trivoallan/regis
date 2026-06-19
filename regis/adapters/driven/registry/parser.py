"""Parse Docker image URLs into registry components."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class RegistryRef:
    """Parsed reference to a Docker image on a registry.

    Attributes:
        registry: Registry hostname (e.g. ``registry-1.docker.io``).
        repository: Full repository path (e.g. ``library/nginx``).
        tag: Optional tag (defaults to ``latest``).
    """

    registry: str
    repository: str
    tag: str = "latest"

    @property
    def image_name(self) -> str:
        """Return the short image name (last segment of the repository path)."""
        return self.repository.rsplit("/", 1)[-1]


# Mapping of well-known web UIs to their actual registry API hosts.
_REGISTRY_MAP: dict[str, str] = {
    "hub.docker.com": "registry-1.docker.io",
}

# Pattern for a Docker Hub URL like hub.docker.com/r/nginxinc/nginx-unprivileged
# or hub.docker.com/library/nginx  (official images, no /r/ prefix)
_DOCKERHUB_PATH_RE = re.compile(
    r"^/?(?:r/)?(?P<repo>[a-z0-9._/-]+?)(?::(?P<tag>[a-zA-Z0-9._-]+))?$"
)


def parse_image_url(url: str) -> RegistryRef:
    """Parse a Docker image URL or reference into a :class:`RegistryRef`.

    Supported formats:

    * ``https://hub.docker.com/r/nginxinc/nginx-unprivileged``
    * ``https://hub.docker.com/library/nginx``
    * ``https://hub.docker.com/_/nginx``  (official shorthand)
    * ``myregistry.example.com/myorg/myimage:mytag``
    * ``nginx:latest``  (bare image name, assumes Docker Hub)

    Args:
        url: The image URL or reference string.

    Returns:
        A :class:`RegistryRef` with the parsed components.

    Raises:
        ValueError: If the URL cannot be parsed.
    """
    # If it looks like a URL (has a scheme), parse with urllib.
    if "://" in url:
        return _parse_full_url(url)

    # Bare reference like "nginx:latest" or "myregistry.com/org/image:tag"
    return _parse_bare_reference(url)


def _parse_full_url(url: str) -> RegistryRef:
    """Parse a full URL with scheme."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    path = parsed.path.strip("/")

    # Docker Hub web UI
    if host in _REGISTRY_MAP:
        return _parse_dockerhub_path(path)

    # Generic V2 registry
    if not path:
        raise ValueError(f"Cannot extract repository from URL: {url}")

    # Split path into repo and optional tag
    repo, tag = _split_tag(path)
    return RegistryRef(registry=host, repository=repo, tag=tag)


def _parse_dockerhub_path(path: str) -> RegistryRef:
    """Parse the path component of a Docker Hub URL."""
    match = _DOCKERHUB_PATH_RE.match(path)
    if not match:
        raise ValueError(f"Cannot parse Docker Hub path: /{path}")

    repo = match.group("repo")
    tag = match.group("tag") or "latest"

    # Handle official images: "_/nginx" or bare "nginx" → "library/nginx"
    if repo.startswith("_/"):
        repo = "library/" + repo[2:]
    elif "/" not in repo:
        repo = "library/" + repo

    return RegistryRef(
        registry="registry-1.docker.io",
        repository=repo,
        tag=tag,
    )


def _parse_bare_reference(ref: str) -> RegistryRef:
    """Parse a bare image reference like ``nginx:latest`` or ``myregistry/org/img:tag``."""
    repo, tag = _split_tag(ref)

    # Heuristic: if the first segment contains a dot or colon it's a registry host.
    parts = repo.split("/", 1)
    if len(parts) == 2 and ("." in parts[0] or ":" in parts[0]):
        return RegistryRef(registry=parts[0], repository=parts[1], tag=tag)

    # Otherwise assume Docker Hub.
    if "/" not in repo:
        repo = "library/" + repo
    return RegistryRef(
        registry="registry-1.docker.io",
        repository=repo,
        tag=tag,
    )


def _split_tag(ref: str) -> tuple[str, str]:
    """Split ``repo:tag`` into a ``(repo, tag)`` tuple."""
    if ":" in ref:
        repo, tag = ref.rsplit(":", 1)
        return repo, tag
    return ref, "latest"
