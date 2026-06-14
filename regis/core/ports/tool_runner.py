"""ToolRunner port — execution of external scanners (capability-oriented)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from regis.core.model.image_reference import ImageReference


@dataclass(frozen=True)
class ToolResult:
    """Generic result of running a tool via the escape hatch."""

    stdout: str
    stderr: str
    exit_code: int


class ToolRunner(ABC):
    """Port for running external scanners.

    Capability methods return parsed output; ``run`` is a generic escape hatch
    for plugin-supplied tools. Registry inspection (regctl) is NOT here — it is a
    second ImageInspector (see RegctlImageInspector, P2b-2).
    """

    @abstractmethod
    def scan_vulnerabilities(self, image: ImageReference) -> dict[str, Any]:
        """Scan *image* for vulnerabilities (e.g. grype)."""

    @abstractmethod
    def generate_sbom(self, image: ImageReference) -> dict[str, Any]:
        """Generate an SBOM for *image* (e.g. syft)."""

    @abstractmethod
    def scan_secrets(self, image: ImageReference) -> list[dict[str, Any]]:
        """Scan *image* for embedded secrets (e.g. trufflehog); one dict per finding."""

    @abstractmethod
    def lint_dockerfile(self, dockerfile: str) -> list[dict[str, Any]]:
        """Lint a Dockerfile *contents* string (e.g. hadolint); one dict per issue."""

    @abstractmethod
    def audit_image(self, image: ImageReference) -> dict[str, Any]:
        """Audit *image* for best practices (e.g. dockle)."""

    @abstractmethod
    def run(
        self, tool: str, args: Sequence[str], *, timeout: int | None = None
    ) -> ToolResult:
        """Escape hatch: run an arbitrary resolved tool with *args*."""
