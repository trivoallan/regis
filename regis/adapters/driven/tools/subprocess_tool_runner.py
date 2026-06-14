"""SubprocessToolRunner — ToolRunner backed by external scanner subprocesses."""

from __future__ import annotations

import json
import subprocess  # nosec B404
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any

import click

from regis.core.domain.errors import AnalyzerError, ToolError
from regis.core.model.image_reference import ImageReference
from regis.core.ports.tool_runner import ToolResult, ToolRunner
from regis.utils.grype import run_grype
from regis.utils.process import ensure_tool
from regis.utils.syft import run_syft
from regis.utils.trufflehog import run_trufflehog


@contextmanager
def _as_tool_error() -> Iterator[None]:
    """Translate a legacy AnalyzerError raised by a wrapper into the core ToolError."""
    try:
        yield
    except AnalyzerError as exc:
        raise ToolError(str(exc)) from exc


class SubprocessToolRunner(ToolRunner):
    """Runs external scanners as subprocesses.

    Registry credentials live here (injected by the composition root in P3), so
    the core never sees a password. The ``ImageReference`` carries no creds; this
    adapter builds the full ``registry/repo:tag`` string and injects auth per tool.
    """

    def __init__(
        self, username: str | None = None, password: str | None = None
    ) -> None:
        self._username = username
        self._password = password

    @staticmethod
    def _full_ref(image: ImageReference) -> str:
        return f"{image.registry}/{image.repository}:{image.tag}"

    def scan_vulnerabilities(self, image: ImageReference) -> dict[str, Any]:
        with _as_tool_error():
            return run_grype(
                self._full_ref(image), self._username, self._password, image.platform
            )

    def generate_sbom(self, image: ImageReference) -> dict[str, Any]:
        with _as_tool_error():
            return run_syft(
                self._full_ref(image), self._username, self._password, image.platform
            )

    def scan_secrets(self, image: ImageReference) -> list[dict[str, Any]]:
        with _as_tool_error():
            return run_trufflehog(self._full_ref(image), self._username, self._password)

    def lint_dockerfile(self, dockerfile: str) -> list[dict[str, Any]]:
        try:
            binary = ensure_tool("hadolint")
        except click.ClickException as exc:
            raise ToolError(str(exc)) from exc
        proc = subprocess.run(  # nosec B603
            [binary, "-f", "json", "-"],
            input=dockerfile,
            capture_output=True,
            text=True,
            check=False,
        )
        stdout = proc.stdout.strip()
        if not stdout:
            return []
        try:
            issues: list[dict[str, Any]] = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise ToolError(f"hadolint produced invalid JSON: {exc}") from exc
        return issues

    def audit_image(self, image: ImageReference) -> dict[str, Any]:
        raise NotImplementedError  # Task 4

    def run(
        self, tool: str, args: Sequence[str], *, timeout: int | None = None
    ) -> ToolResult:
        raise NotImplementedError  # Task 5
