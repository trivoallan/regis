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

    Capability methods return parsed output (a dict); ``run`` is a generic
    escape hatch for plugin-supplied tools.
    """

    @abstractmethod
    def scan_vulnerabilities(self, image: ImageReference) -> dict[str, Any]:
        """Scan *image* for vulnerabilities (e.g. grype)."""

    @abstractmethod
    def generate_sbom(self, image: ImageReference) -> dict[str, Any]:
        """Generate an SBOM for *image* (e.g. syft)."""

    @abstractmethod
    def scan_secrets(self, image: ImageReference) -> dict[str, Any]:
        """Scan *image* for embedded secrets (e.g. trufflehog)."""

    @abstractmethod
    def lint_dockerfile(self, dockerfile_contents: str) -> dict[str, Any]:
        """Lint the given Dockerfile *contents* string (e.g. hadolint)."""

    @abstractmethod
    def audit_image(self, image: ImageReference) -> dict[str, Any]:
        """Audit *image* for best practices (e.g. dockle)."""

    @abstractmethod
    def inspect_platforms(self, image: ImageReference) -> dict[str, Any]:
        """Inspect *image* manifest/platform data (e.g. regctl)."""

    @abstractmethod
    def run(
        self, tool: str, args: Sequence[str], *, timeout: int | None = None
    ) -> ToolResult:
        """Escape hatch: run an arbitrary resolved tool with *args*."""
