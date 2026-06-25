"""Composition root: assemble an AnalyzeImage from creds + driven adapters.

This is the one place that knows the concrete adapter types. It hands the
use-case **callables** (not adapter types) so ``core/application`` stays free of
adapter imports.
"""

from __future__ import annotations

from regis.adapters.driven.registry.caching_image_inspector import (
    CachingImageInspector,
)
from regis.adapters.driven.registry.client import RegistryClient
from regis.adapters.driven.registry.regctl_image_inspector import RegctlImageInspector
from regis.adapters.driven.report.file_report_sink import FileReportSink
from regis.adapters.driven.report.presentation_renderer import (
    CookiecutterPresentationRenderer,
)
from regis.adapters.driven.tools.subprocess_tool_runner import SubprocessToolRunner
from regis.core.application.analyze_image import AnalyzeImage
from regis.core.application.evaluate import Evaluate
from regis.core.model.image_reference import ImageReference
from regis.core.ports.image_inspector import ImageInspector


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
        return CachingImageInspector(RegctlImageInspector(_client(image)))

    sink = FileReportSink(
        output_dir_template=output_dir_template,
        output_template=output_template,
        theme=theme,
        pretty=pretty,
        sections=sections,
    )
    presentation = CookiecutterPresentationRenderer(
        output_dir_template=output_dir_template
    )

    return AnalyzeImage(
        tools=SubprocessToolRunner(username, password),
        inspector_factory=_inspector,
        sink=sink,
        presentation=presentation,
    )


def build_evaluate(
    *,
    output_dir_template: str = "reports/dry-run/{timestamp}",
    output_template: str | None = None,
    theme: str = "default",
    pretty: bool = True,
    sections: str = "all",
) -> Evaluate:
    """Wire an Evaluate use-case with a FileReportSink for the dry-run path.

    No registry credentials are needed: ``evaluate`` re-reads a local report
    file rather than hitting a registry.
    """
    sink = FileReportSink(
        output_dir_template=output_dir_template,
        output_template=output_template,
        theme=theme,
        pretty=pretty,
        sections=sections,
    )
    presentation = CookiecutterPresentationRenderer(
        output_dir_template=output_dir_template
    )
    return Evaluate(sink=sink, presentation=presentation)
