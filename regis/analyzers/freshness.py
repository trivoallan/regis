"""Freshness analyzer — checks how up-to-date the image tag is."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from regis.analyzers.base import BaseAnalyzer
from regis.core.domain.context import AnalysisContext
from regis.core.domain.manifest import get_image_config
from regis.core.ports.image_inspector import ImageInspector

logger = logging.getLogger(__name__)


def _get_created_date(inspector: ImageInspector, reference: str) -> str | None:
    """Extract the creation date from an image config using the domain helper."""
    try:
        config = get_image_config(inspector, reference, "linux", "amd64")
        return config.get("created")  # type: ignore[no-any-return]
    except Exception:
        logger.debug("get_image_config failed for %s", reference, exc_info=True)
        return None


class FreshnessAnalyzer(BaseAnalyzer):
    """Compare the analyzed tag's creation date against the latest tag."""

    name = "freshness"
    schema_file = "analyzer/freshness.schema.json"
    uses_context = True

    @classmethod
    def default_criteria(cls) -> list[dict[str, Any]]:
        return [
            {
                "slug": "age",
                "description": "Image should be less than expected days old.",
                "level": "warning",
                "tags": ["freshness"],
                "params": {"max_days": 30},
                "condition": {
                    "<": [
                        {"var": "results.freshness.age_days"},
                        {"var": "criterion.params.max_days"},
                    ]
                },
                "messages": {
                    "pass": "Image is less than ${criterion.params.max_days} days old (${results.freshness.age_days} days).",  # nosec B105
                    "fail": "Image is older than ${criterion.params.max_days} days (${results.freshness.age_days} days).",
                },
            }
        ]

    def analyze(self, ctx: AnalysisContext) -> dict[str, Any]:  # type: ignore[override]
        repository = ctx.image.repository
        tag = ctx.image.tag

        # Get creation date for the analyzed tag.
        tag_created = _get_created_date(ctx.inspector, tag)

        # Get creation date for "latest".
        latest_created = None
        if tag != "latest":
            latest_created = _get_created_date(ctx.inspector, "latest")

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
