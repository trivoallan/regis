"""Stable, tamper-evident fingerprint of the resolved, enforced ruleset."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def ruleset_fingerprint(enabled_rules: list[dict[str, Any]]) -> str:
    """Return a stable hash of what the ruleset actually enforces.

    Keys on ``slug``, ``level``, and the resolved JSON Logic ``condition``
    (thresholds baked in), so loosening a threshold changes the hash. Cosmetic
    fields (description, message, tags) are excluded. Rules are sorted by slug so
    declaration order does not affect the result.
    """
    canonical = [
        {
            "slug": r.get("slug", ""),
            "level": r.get("level", "info"),
            "condition": r.get("condition", {}),
        }
        for r in sorted(enabled_rules, key=lambda r: r.get("slug", ""))
    ]
    blob = json.dumps(
        canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()
