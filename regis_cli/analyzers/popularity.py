"""Popularity analyzer — fetches Docker Hub statistics."""

from __future__ import annotations

import logging
from typing import Any

import requests

from regis_cli.analyzers.base import BaseAnalyzer
from regis_cli.registry.client import RegistryClient

logger = logging.getLogger(__name__)

_DOCKERHUB_API = "https://hub.docker.com/v2/repositories"


class PopularityAnalyzer(BaseAnalyzer):
    """Fetch download count, star count, and metadata from Docker Hub."""

    name = "popularity"
    schema_file = "analyzer/popularity.schema.json"

    def analyze(
        self,
        client: RegistryClient,
        repository: str,
        tag: str,
        platform: str | None = None,
    ) -> dict[str, Any]:
        url = f"{_DOCKERHUB_API}/{repository}"
        logger.debug("Fetching Docker Hub stats: %s", url)

        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                logger.info("Docker Hub returned %d for %s", resp.status_code, url)
                return self._empty(repository)
            data = resp.json()
        except Exception:
            logger.debug("Docker Hub request failed", exc_info=True)
            return self._empty(repository)

        return {
            "analyzer": self.name,
            "repository": repository,
            "available": True,
            "pull_count": data.get("pull_count", 0),
            "star_count": data.get("star_count", 0),
            "description": data.get("description", ""),
            "last_updated": data.get("last_updated"),
            "date_registered": data.get("date_registered"),
            "is_official": repository.startswith("library/"),
        }

    def _empty(self, repository: str) -> dict[str, Any]:
        return {
            "analyzer": self.name,
            "repository": repository,
            "available": False,
            "pull_count": None,
            "star_count": None,
            "description": None,
            "last_updated": None,
            "date_registered": None,
            "is_official": repository.startswith("library/"),
        }
