"""Composition root: assemble an AnalyzeImage from creds + driven adapters.

This is the one place that knows the concrete adapter types. It hands the
use-case **callables** (not adapter types) so ``core/application`` stays free of
adapter imports.
"""

from __future__ import annotations

from regis.adapters.driven.registry.regctl_image_inspector import RegctlImageInspector
from regis.adapters.driven.report.file_report_sink import FileReportSink
from regis.adapters.driven.tools.subprocess_tool_runner import SubprocessToolRunner
from regis.core.application.analyze_image import AnalyzeImage
from regis.core.model.image_reference import ImageReference
from regis.core.ports.image_inspector import ImageInspector
from regis.registry.client import RegistryClient


def build_analyze_image(
    username: str | None,
    password: str | None,
    *,
    output_dir_template: str = "reports/{registry}/{repository}/{digest}",
    output_template: str | None = None,
    theme: str = "default",
    pretty: bool = True,
    sections: str = "all",
) -> AnalyzeImage:
    """Wire an AnalyzeImage for the given registry credentials.

    - ``tools``: a shared, stateless SubprocessToolRunner (creds live here).
    - ``inspector_factory``: a fresh regctl ImageInspector per image (creds captured).
    - ``sink``: a FileReportSink configured with the given output template and options.
    """

    def _client(image: ImageReference) -> RegistryClient:
        return RegistryClient(
            registry=image.registry,
            repository=image.repository,
            username=username,
            password=password,
        )

    def _inspector(image: ImageReference) -> ImageInspector:
        return RegctlImageInspector(_client(image))

    sink = FileReportSink(
        output_dir_template=output_dir_template,
        output_template=output_template,
        theme=theme,
        pretty=pretty,
        sections=sections,
    )

    return AnalyzeImage(
        tools=SubprocessToolRunner(username, password),
        inspector_factory=_inspector,
        sink=sink,
    )
