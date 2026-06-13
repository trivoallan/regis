"""In-memory fakes implementing the hexagonal ports, for hermetic tests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from regis.core.application.analyzer_provider import AnalyzerProvider
from regis.core.model.image_reference import ImageReference
from regis.core.model.report import Report
from regis.core.ports.image_inspector import ImageInspector
from regis.core.ports.report_sink import ReportSink
from regis.core.ports.tool_runner import ToolResult, ToolRunner


class FakeImageInspector(ImageInspector):
    """Returns canned registry data; no network.

    Limitation: ``get_manifest``/``get_blob`` ignore their reference/digest
    argument and return the single canned value. Extend with a per-reference
    map if a test must distinguish multiple references (e.g. a multi-arch path).
    """

    def __init__(
        self,
        *,
        tags: list[str] | None = None,
        manifest: dict[str, Any] | None = None,
        blob: dict[str, Any] | None = None,
        digest: str | None = "sha256:fake",
    ) -> None:
        self._tags = tags or []
        self._manifest = manifest or {}
        self._blob = blob or {}
        self._digest = digest

    def list_tags(self) -> list[str]:
        return list(self._tags)

    def get_manifest(self, reference: str) -> dict[str, Any]:
        return dict(self._manifest)

    def get_blob(self, digest: str) -> dict[str, Any]:
        return dict(self._blob)

    def get_digest(self, reference: str) -> str | None:
        return self._digest


class FakeToolRunner(ToolRunner):
    """Returns canned tool output per capability; no subprocess."""

    def __init__(self, **canned: dict[str, Any]) -> None:
        self._canned = canned

    def scan_vulnerabilities(self, image: ImageReference) -> dict[str, Any]:
        return self._canned.get("scan_vulnerabilities", {})

    def generate_sbom(self, image: ImageReference) -> dict[str, Any]:
        return self._canned.get("generate_sbom", {})

    def scan_secrets(self, image: ImageReference) -> dict[str, Any]:
        return self._canned.get("scan_secrets", {})

    def lint_dockerfile(self, dockerfile_contents: str) -> dict[str, Any]:
        return self._canned.get("lint_dockerfile", {})

    def audit_image(self, image: ImageReference) -> dict[str, Any]:
        return self._canned.get("audit_image", {})

    def inspect_platforms(self, image: ImageReference) -> dict[str, Any]:
        return self._canned.get("inspect_platforms", {})

    def run(
        self, tool: str, args: Sequence[str], *, timeout: int | None = None
    ) -> ToolResult:
        # Always a zero-exit empty result; subclass if a test needs a failure path.
        return ToolResult(stdout="", stderr="", exit_code=0)


class FakeReportSink(ReportSink):
    """Records emissions in memory; writes nothing to disk."""

    def __init__(self) -> None:
        self.emitted: list[tuple[Report, tuple[str, ...], Path]] = []

    def emit(
        self, report: Report, *, formats: Sequence[str], output_dir: Path
    ) -> list[Path]:
        self.emitted.append((report, tuple(formats), output_dir))
        return [output_dir / f"report.{fmt}" for fmt in formats]


class StubAnalyzerProvider(AnalyzerProvider):
    """Returns a fixed analyzer mapping; no entry-point discovery."""

    def __init__(self, analyzers: Mapping[str, type]) -> None:
        self._analyzers = dict(analyzers)

    def available(self) -> Mapping[str, type]:
        return dict(self._analyzers)
