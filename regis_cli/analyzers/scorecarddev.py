"""Scorecard analyzer — fetches OpenSSF Scorecard data for the image source repo."""

from __future__ import annotations

import logging
import re
from typing import Any

import requests

from regis_cli.analyzers.base import BaseAnalyzer
from regis_cli.registry.client import RegistryClient

logger = logging.getLogger(__name__)

_SCORECARD_API = "https://api.securityscorecards.dev"

# Docker Hub API for repository metadata (source repo URL).
_DOCKERHUB_API = "https://hub.docker.com/v2/repositories"

# Regex to extract a GitHub/GitLab repo path from a URL.
_GIT_REPO_RE = re.compile(
    r"(?:https?://)?(?P<platform>github\.com|gitlab\.com)/(?P<owner>[a-zA-Z0-9._-]+)/(?P<repo>[a-zA-Z0-9._-]+)"
)


def _source_repo_from_labels(
    client: RegistryClient,
    tag: str,
) -> str | None:
    """Try to extract the source repository from OCI image labels.

    Looks for standard labels:
    - ``org.opencontainers.image.source``
    - ``org.label-schema.vcs-url``
    """
    try:
        manifest = client.get_manifest(tag)
        media_type = manifest.get("mediaType", "")

        # If it's a manifest list, pick the first platform manifest.
        if "list" in media_type or "index" in media_type:
            entries = manifest.get("manifests", [])
            if not entries:
                return None
            manifest = client.get_manifest(entries[0]["digest"])

        config_digest = manifest.get("config", {}).get("digest")
        if not config_digest:
            return None

        config = client.get_blob(config_digest)
        labels: dict[str, str] = config.get("config", {}).get("Labels") or {}

        for label_key in (
            "org.opencontainers.image.source",
            "org.label-schema.vcs-url",
        ):
            url = labels.get(label_key, "")
            if url:
                return url
    except Exception:
        logger.debug("Could not extract source repo from image labels", exc_info=True)

    return None


def _source_repo_from_dockerhub(repository: str) -> str | None:
    """Try to get the source repo URL from the Docker Hub API."""
    try:
        resp = requests.get(f"{_DOCKERHUB_API}/{repository}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # Docker Hub may expose full_description or a source link.
            for field in ("source", "full_description"):
                text = data.get(field, "") or ""
                match = _GIT_REPO_RE.search(text)
                if match:
                    return f"https://{match.group('platform')}/{match.group('owner')}/{match.group('repo')}"
    except Exception:
        logger.debug("Could not query Docker Hub API", exc_info=True)

    return None


def _resolve_source_repo(
    client: RegistryClient,
    repository: str,
    tag: str,
) -> str | None:
    """Resolve the source code repository for a Docker image.

    Tries, in order:
    1. OCI image labels (org.opencontainers.image.source)
    2. Docker Hub API metadata
    """
    url = _source_repo_from_labels(client, tag)
    if url:
        return url

    return _source_repo_from_dockerhub(repository)


def _parse_git_url(url: str) -> tuple[str, str, str] | None:
    """Parse a git URL into ``(platform, owner, repo)``."""
    match = _GIT_REPO_RE.search(url)
    if match:
        repo = match.group("repo")
        # Strip .git suffix if present.
        if repo.endswith(".git"):
            repo = repo[:-4]
        return match.group("platform"), match.group("owner"), repo
    return None


def _fetch_scorecard(platform: str, owner: str, repo: str) -> dict[str, Any] | None:
    """Call the OpenSSF Scorecard API and return the raw response."""
    url = f"{_SCORECARD_API}/projects/{platform}/{owner}/{repo}"
    logger.debug("Fetching scorecard: %s", url)
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            return resp.json()  # type: ignore[no-any-return]
        logger.warning("Scorecard API returned %d for %s", resp.status_code, url)
    except Exception:
        logger.debug("Scorecard API request failed", exc_info=True)
    return None


class ScorecardDevAnalyzer(BaseAnalyzer):
    """Fetch OpenSSF Scorecard security assessment for the image source repository."""

    name = "scorecarddev"
    schema_file = "analyzer/scorecarddev.schema.json"

    @classmethod
    def default_rules(cls) -> list[dict[str, Any]]:
        return [
            {
                "slug": "scorecard.min-score",
                "description": "OpenSSF Scorecard score is above the threshold.",
                "level": "warning",
                "tags": ["security"],
                "params": {"min_score": 5.0},
                "condition": {
                    ">=": [
                        {"var": "results.scorecarddev.score"},
                        {"var": "rule.params.min_score"},
                    ]
                },
                "messages": {
                    "pass": "Scorecard score is ${results.scorecarddev.score} (min required: ${rule.params.min_score}).",  # nosec B105
                    "fail": "Scorecard score is too low: ${results.scorecarddev.score} (min required: ${rule.params.min_score}).",
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
        """Resolve the source repo and fetch its OpenSSF Scorecard."""
        source_url = _resolve_source_repo(client, repository, tag)

        if not source_url:
            return {
                "analyzer": self.name,
                "repository": repository,
                "source_repo": None,
                "scorecard_available": False,
                "score": None,
                "checks": [],
            }

        parsed = _parse_git_url(source_url)
        if not parsed:
            return {
                "analyzer": self.name,
                "repository": repository,
                "source_repo": source_url,
                "scorecard_available": False,
                "score": None,
                "checks": [],
            }

        platform, owner, repo = parsed
        raw = _fetch_scorecard(platform, owner, repo)

        if not raw:
            return {
                "analyzer": self.name,
                "repository": repository,
                "source_repo": source_url,
                "scorecard_available": False,
                "score": None,
                "checks": [],
            }

        # Transform checks into a simpler structure.
        checks = []
        for check in raw.get("checks", []):
            score = check.get("score", -1)
            checks.append(
                {
                    "name": check["name"],
                    "score": score,
                    "reason": check.get("reason", ""),
                }
            )

        return {
            "analyzer": self.name,
            "repository": repository,
            "source_repo": source_url,
            "scorecard_available": True,
            "score": raw.get("score"),
            "checks": checks,
        }
