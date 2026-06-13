"""ImageReference value object."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImageReference:
    """An immutable reference to an OCI image to analyze. Carries no credentials."""

    registry: str
    repository: str
    tag: str
    platform: str | None = None
