"""HTTP client for the Docker Registry V2 API."""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Docker Hub authentication endpoint.
_DOCKER_AUTH_URL = "https://auth.docker.io/token"
_DOCKER_AUTH_SERVICE = "registry.docker.io"


class RegistryError(Exception):
    """Raised when a registry API call fails."""


class RegistryClient:
    """Client for interacting with a Docker Registry V2 API.

    Handles token-based authentication transparently.

    Args:
        registry: Registry hostname (e.g. ``registry-1.docker.io``).
        repository: Full repository path (e.g. ``library/nginx``).
        timeout: HTTP request timeout in seconds.
    """

    def __init__(
        self,
        registry: str,
        repository: str,
        *,
        username: str | None = None,
        password: str | None = None,
        timeout: int = 30,
    ) -> None:
        self.registry = registry
        self.repository = repository
        self.username = username
        self.password = password
        self.timeout = timeout
        self._session = requests.Session()
        self._token: str | None = None
        self._base_url = f"https://{registry}/v2"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_tags(self) -> list[str]:
        """Return all tags for the repository.

        Returns:
            Sorted list of tag names.

        Raises:
            RegistryError: If the API call fails.
        """
        data = self._get(f"/{self.repository}/tags/list")
        tags: list[str] = data.get("tags") or []
        return sorted(tags)

    def get_manifest(self, tag: str) -> dict[str, Any]:
        """Fetch the manifest for a given tag.

        Tries the OCI / Docker V2 fat manifest first, then falls back to
        the V2 schema 2 manifest.

        Args:
            tag: The image tag.

        Returns:
            Parsed manifest JSON.
        """
        accept = (
            "application/vnd.oci.image.index.v1+json, "
            "application/vnd.docker.distribution.manifest.list.v2+json, "
            "application/vnd.oci.image.manifest.v1+json, "
            "application/vnd.docker.distribution.manifest.v2+json"
        )
        return self._get(f"/{self.repository}/manifests/{tag}", accept=accept)

    def get_blob(self, digest: str) -> dict[str, Any]:
        """Fetch a blob (typically an image config) by digest.

        Args:
            digest: The blob digest (e.g. ``sha256:abc123...``).

        Returns:
            Parsed blob JSON.
        """
        return self._get(f"/{self.repository}/blobs/{digest}")

    def get_digest(self, tag: str) -> str | None:
        """Fetch the Docker-Content-Digest for a given tag using a HEAD request.

        Args:
            tag: The image tag.

        Returns:
            The digest string (e.g. ``sha256:abc...``), or None if not returned by the registry.

        Raises:
            RegistryError: If the API call fails.
        """
        accept = (
            "application/vnd.oci.image.index.v1+json, "
            "application/vnd.docker.distribution.manifest.list.v2+json, "
            "application/vnd.oci.image.manifest.v1+json, "
            "application/vnd.docker.distribution.manifest.v2+json"
        )
        url = self._base_url + f"/{self.repository}/manifests/{tag}"
        headers = {"Accept": accept}

        # Try without auth first, then authenticate on 401.
        resp = self._request(url, headers, method="HEAD")
        if resp.status_code == 401:
            self._authenticate(resp)
            resp = self._request(url, headers, method="HEAD")

        if resp.status_code != 200:
            raise RegistryError(f"Registry returned {resp.status_code} for HEAD {url}")

        return resp.headers.get("Docker-Content-Digest")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get(
        self,
        path: str,
        *,
        accept: str | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated GET request to the registry."""
        url = self._base_url + path
        headers: dict[str, str] = {}

        if accept:
            headers["Accept"] = accept

        # Try without auth first, then authenticate on 401.
        resp = self._request(url, headers)
        if resp.status_code == 401:
            self._authenticate(resp)
            resp = self._request(url, headers)

        if resp.status_code != 200:
            raise RegistryError(
                f"Registry returned {resp.status_code} for {url}: {resp.text[:200]}"
            )

        return resp.json()  # type: ignore[no-any-return]

    def _request(
        self,
        url: str,
        headers: dict[str, str],
        method: str = "GET",
    ) -> requests.Response:
        """Execute a single HTTP request, attaching the bearer token if available."""
        req_headers = {**headers}
        if self._token:
            req_headers["Authorization"] = f"Bearer {self._token}"

        logger.debug("%s %s", method, url)
        return self._session.request(
            method, url, headers=req_headers, timeout=self.timeout
        )

    def _authenticate(self, response: requests.Response) -> None:
        """Parse a ``WWW-Authenticate`` header and obtain a bearer token."""
        www_auth = response.headers.get("WWW-Authenticate", "")
        params = _parse_www_authenticate(www_auth)

        realm = params.get("realm", _DOCKER_AUTH_URL)
        service = params.get("service", _DOCKER_AUTH_SERVICE)
        scope = params.get("scope", f"repository:{self.repository}:pull")

        logger.debug(
            "Authenticating: realm=%s service=%s scope=%s", realm, service, scope
        )

        auth = None
        if self.username and self.password:
            auth = (self.username, self.password)

        token_resp = self._session.get(
            realm,
            params={"service": service, "scope": scope},
            auth=auth,
            timeout=self.timeout,
        )
        token_resp.raise_for_status()
        self._token = token_resp.json().get("token")


def _parse_www_authenticate(header: str) -> dict[str, str]:
    """Parse a ``Bearer realm=...,service=...,scope=...`` header into a dict."""
    # Strip the "Bearer " prefix.
    if header.lower().startswith("bearer "):
        header = header[7:]

    params: dict[str, str] = {}
    for part in header.split(","):
        part = part.strip()
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        params[key.strip()] = value.strip().strip('"')
    return params
