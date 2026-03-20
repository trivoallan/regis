"""End-of-life analyzer — fetches lifecycle data from endoflife.date."""

from __future__ import annotations

import logging
import re
from typing import Any

import requests

from regis_cli.analyzers.base import BaseAnalyzer
from regis_cli.registry.client import RegistryClient

logger = logging.getLogger(__name__)

_EOL_API = "https://endoflife.date/api"

# Known mappings from Docker image names to endoflife.date product slugs.
# When not in this map, the analyzer tries the image short name directly.
_IMAGE_TO_PRODUCT: dict[str, str] = {
    "nginx": "nginx",
    "node": "nodejs",
    "python": "python",
    "golang": "go",
    "ruby": "ruby",
    "php": "php",
    "postgres": "postgresql",
    "mysql": "mysql",
    "mariadb": "mariadb",
    "redis": "redis",
    "mongo": "mongodb",
    "elasticsearch": "elasticsearch",
    "traefik": "traefik",
    "haproxy": "haproxy",
    "httpd": "apache-http-server",
    "alpine": "alpine",
    "ubuntu": "ubuntu",
    "debian": "debian",
    "amazoncorretto": "amazon-corretto",
    "eclipse-temurin": "eclipse-temurin",
    "rust": "rust",
    "dotnet/sdk": "dotnet",
    "dotnet/runtime": "dotnet",
    "openjdk": "java",
    "gradle": "gradle",
    "maven": "maven",
    "tomcat": "tomcat",
    "rabbitmq": "rabbitmq",
    "memcached": "memcached",
    "consul": "consul",
    "vault": "hashicorp-vault",
    "gitlab/gitlab-ce": "gitlab",
    "gitlab/gitlab-ee": "gitlab",
    "jenkins/jenkins": "jenkins",
    "nextcloud": "nextcloud",
    "wordpress": "wordpress",
    "drupal": "drupal",
    "ghost": "ghost",
}


def _image_to_product(repository: str) -> str:
    """Map a Docker image repository to an endoflife.date product slug.

    Tries the full repository minus ``library/``, then the short image name.
    """
    # Strip "library/" prefix for official images.
    name = repository.removeprefix("library/")

    if name in _IMAGE_TO_PRODUCT:
        return _IMAGE_TO_PRODUCT[name]

    # Try just the short image name (last path segment).
    short = name.rsplit("/", 1)[-1]
    if short in _IMAGE_TO_PRODUCT:
        return _IMAGE_TO_PRODUCT[short]

    # Fallback: use the short name as the product slug directly.
    return short


def _extract_version(tag: str) -> str | None:
    """Extract a major.minor version prefix from a tag.

    Examples:
        ``3.19.1`` → ``3.19``
        ``1.27-alpine`` → ``1.27``
        ``22.04`` → ``22.04``
        ``latest`` → ``None``
    """
    match = re.match(r"v?(\d+(?:\.\d+)?)", tag)
    if match:
        return match.group(1)
    return None


def _fetch_cycles(product: str) -> list[dict[str, Any]] | None:
    """Fetch all release cycles for a product from endoflife.date."""
    url = f"{_EOL_API}/{product}.json"
    logger.debug("Fetching EOL data: %s", url)
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()  # type: ignore[no-any-return]
        logger.info("endoflife.date returned %d for %s", resp.status_code, url)
    except Exception:
        logger.debug("endoflife.date request failed", exc_info=True)
    return None


def _match_cycle(
    version: str,
    cycles: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Find the best matching cycle for a version string."""
    for cycle in cycles:
        cycle_id = str(cycle.get("cycle", ""))
        if cycle_id == version:
            return cycle
    # Try matching just major version.
    major = version.split(".")[0]
    for cycle in cycles:
        cycle_id = str(cycle.get("cycle", ""))
        if cycle_id == major:
            return cycle
    return None


class EndOfLifeAnalyzer(BaseAnalyzer):
    """Check end-of-life status for the image product via endoflife.date."""

    name = "endoflife"
    schema_file = "analyzer/endoflife.schema.json"

    def analyze(
        self,
        client: RegistryClient,
        repository: str,
        tag: str,
        platform: str | None = None,
    ) -> dict[str, Any]:
        """Fetch lifecycle data and match against the image tag."""
        product = _image_to_product(repository)
        cycles = _fetch_cycles(product)

        if cycles is None:
            return {
                "analyzer": self.name,
                "repository": repository,
                "product": product,
                "product_found": False,
                "tag": tag,
                "matched_cycle": None,
                "is_eol": None,
                "active_cycles_count": None,
                "eol_cycles_count": None,
            }

        # Count active vs EOL cycles.
        active = [c for c in cycles if c.get("eol") is False]
        eol = [c for c in cycles if c.get("eol") not in (False, None)]

        # Try to match the tag to a specific cycle.
        version = _extract_version(tag)
        matched = _match_cycle(version, cycles) if version else None

        matched_info: dict[str, Any] | None = None
        is_eol: bool | None = None

        if matched:
            eol_value = matched.get("eol")
            if eol_value is False:
                is_eol = False
            elif isinstance(eol_value, str):
                is_eol = True  # Has an EOL date → already EOL.
            else:
                is_eol = bool(eol_value)

            matched_info = {
                "cycle": str(matched.get("cycle", "")),
                "release_date": matched.get("releaseDate"),
                "eol": str(eol_value) if eol_value is not False else False,
                "latest": matched.get("latest"),
                "latest_release_date": matched.get("latestReleaseDate"),
                "lts": matched.get("lts", False),
            }

        return {
            "analyzer": self.name,
            "repository": repository,
            "product": product,
            "product_found": True,
            "tag": tag,
            "matched_cycle": matched_info,
            "is_eol": is_eol,
            "active_cycles_count": len(active),
            "eol_cycles_count": len(eol),
        }
