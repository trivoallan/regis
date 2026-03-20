"""Freshness analyzer — checks how up-to-date the image tag is."""

from __future__ import annotations

import json
import logging
import subprocess
from datetime import datetime, timezone
from typing import Any

from regis_cli.analyzers.base import BaseAnalyzer
from regis_cli.registry.client import RegistryClient

logger = logging.getLogger(__name__)


def _get_created_date(client: RegistryClient, repository: str, tag: str) -> str | None:
    """Extract the creation date from an image config using skopeo."""
    registry = client.registry
    target = f"docker://{registry}/{repository}:{tag}"

    cmd = [
        "skopeo",
        "inspect",
        "--config",
        "--override-os",
        "linux",
        "--override-arch",
        "amd64",
        target,
    ]

    if client.username and client.password:
        cmd.extend(["--creds", f"{client.username}:{client.password}"])

    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(res.stdout)
        return data.get("created")  # type: ignore[no-any-return]
    except Exception:
        logger.debug("Skopeo inspect --config failed for %s", target, exc_info=True)
        return None


class FreshnessAnalyzer(BaseAnalyzer):
    """Compare the analyzed tag's creation date against the latest tag."""

    name = "freshness"
    schema_file = "analyzer/freshness.schema.json"

    @classmethod
    def default_rules(cls) -> list[dict[str, Any]]:
        return [
            {
                "slug": "freshness.age",
                "description": "Image should be less than expected days old.",
                "level": "warning",
                "tags": ["freshness"],
                "params": {"max_days": 30},
                "condition": {
                    "<": [
                        {"var": "results.freshness.age_days"},
                        {"var": "rule.params.max_days"},
                    ]
                },
                "messages": {
                    "pass": "Image is less than ${rule.params.max_days} days old (${results.freshness.age_days} days).",  # nosec B105
                    "fail": "Image is older than ${rule.params.max_days} days (${results.freshness.age_days} days).",
                },
            }
        ]

    def analyze(
        self,
        client: RegistryClient,
        repository: str,
        tag: str,
        platform: str | None = None,
    ) -> dict[str, Any]:
        # Get creation date for the analyzed tag.
        tag_created = _get_created_date(client, repository, tag)

        # Get creation date for "latest".
        latest_created = None
        if tag != "latest":
            latest_created = _get_created_date(client, repository, "latest")

        # Compute age and delta.
        age_days: int | None = None
        behind_days: int | None = None
        now = datetime.now(timezone.utc)

        if tag_created:
            try:
                tag_dt = datetime.fromisoformat(tag_created.replace("Z", "+00:00"))
                age_days = (now - tag_dt).days
            except (ValueError, TypeError):
                pass

        if tag_created and latest_created:
            try:
                tag_dt = datetime.fromisoformat(tag_created.replace("Z", "+00:00"))
                latest_dt = datetime.fromisoformat(
                    latest_created.replace("Z", "+00:00")
                )
                behind_days = (latest_dt - tag_dt).days
                if behind_days < 0:
                    behind_days = 0
            except (ValueError, TypeError):
                pass

        return {
            "analyzer": self.name,
            "repository": repository,
            "tag": tag,
            "tag_created": tag_created,
            "latest_created": latest_created,
            "age_days": age_days,
            "behind_latest_days": behind_days,
            "is_latest": tag == "latest" or behind_days == 0,
        }
