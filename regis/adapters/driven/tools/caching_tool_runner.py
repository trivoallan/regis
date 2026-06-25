"""CachingToolRunner — per-run shared OCI layout for syft + grype.

Exports the target image ONCE into a local OCI layout (regctl image copy) and
points syft/grype at ``oci-dir:<layout>`` instead of re-pulling the remote
image. Removes 2 of the 4 scanner image pulls per run. Mirrors
CachingImageInspector: per-run scope, thread-safe lock held across the export so
a concurrent second tool reuses the one layout.

Sharing is gated (``share``) on BOTH cve and sbom being selected (decided in
AnalyzeImage) — a single image-reading analyzer gains nothing from the export.
When sharing is off, or the export fails, calls pass through to the delegate's
remote scan unchanged.

THREAD-SAFETY: the delegate (SubprocessToolRunner) is stateless. The lock guards
the layout memo and is held across the regctl export, so a duplicate in-flight
export for the same ref collapses to one (same idiom as CachingImageInspector).
"""

from __future__ import annotations

import tempfile
import threading
from collections.abc import Sequence
from typing import Any

from regis.adapters.driven.tools.subprocess_tool_runner import SubprocessToolRunner
from regis.core.model.image_reference import ImageReference
from regis.core.ports.tool_runner import ToolResult, ToolRunner

#: Memo key — a value-equal identity for one image reference + platform.
_Key = tuple[str, str, str, str | None]


class CachingToolRunner(ToolRunner):
    """Per-run decorator sharing one local OCI layout across syft + grype."""

    def __init__(self, delegate: SubprocessToolRunner, share: bool) -> None:
        self._delegate = delegate
        self._share = share
        self._lock = threading.Lock()
        self._layouts: dict[_Key, str | None] = {}
        self._tmpdirs: list[tempfile.TemporaryDirectory[str]] = []
        self._closed = False

    @staticmethod
    def _key(image: ImageReference) -> _Key:
        return (image.registry, image.repository, image.tag, image.platform)

    def _layout(self, image: ImageReference) -> str | None:
        """Return a local OCI layout path for *image*, exporting once.

        Returns ``None`` if the export failed (memoized, never retried) so the
        caller falls back to a remote scan. The lock is held across the export
        so a concurrent second tool waits and reuses the one layout.
        """
        key = self._key(image)
        with self._lock:
            if key in self._layouts:
                return self._layouts[key]
            # Track the tempdir before the export so close() cleans it up even
            # if the export fails and leaves it empty (bounded: one per ref).
            tmp = tempfile.TemporaryDirectory(prefix="regis-layout-")
            self._tmpdirs.append(tmp)
            ok = self._delegate.export_layout(image, tmp.name)
            self._layouts[key] = tmp.name if ok else None
            return self._layouts[key]

    def generate_sbom(self, image: ImageReference) -> dict[str, Any]:
        if self._share:
            layout = self._layout(image)
            if layout is not None:
                return self._delegate.generate_sbom_from_layout(layout)
        return self._delegate.generate_sbom(image)

    def scan_vulnerabilities(self, image: ImageReference) -> dict[str, Any]:
        if self._share:
            layout = self._layout(image)
            if layout is not None:
                return self._delegate.scan_vulnerabilities_from_layout(layout)
        return self._delegate.scan_vulnerabilities(image)

    # Capabilities that do not read the shared layout pass straight through.
    def scan_secrets(self, image: ImageReference) -> list[dict[str, Any]]:
        return self._delegate.scan_secrets(image)

    def lint_dockerfile(self, dockerfile: str) -> list[dict[str, Any]]:
        return self._delegate.lint_dockerfile(dockerfile)

    def audit_image(self, image: ImageReference) -> dict[str, Any]:
        return self._delegate.audit_image(image)

    def run(
        self, tool: str, args: Sequence[str], *, timeout: int | None = None
    ) -> ToolResult:
        return self._delegate.run(tool, args, timeout=timeout)

    def close(self) -> None:
        """Remove all exported layouts. Idempotent.

        Single-caller contract: called once from ``run()`` after the analyzer
        ThreadPoolExecutor has joined, so ``_closed`` needs no lock — no worker
        is reading a layout when it is removed.
        """
        if self._closed:
            return
        self._closed = True
        for tmp in self._tmpdirs:
            tmp.cleanup()
