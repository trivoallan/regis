"""Composition root: assemble an AnalyzeImage from creds + driven adapters.

This is the one place that knows the concrete adapter types. It hands the
use-case **callables** (not adapter types) so ``core/application`` stays free of
adapter imports.
"""

from __future__ import annotations

from regis.adapters.driven.registry.regctl_image_inspector import RegctlImageInspector
from regis.adapters.driven.tools.subprocess_tool_runner import SubprocessToolRunner
from regis.core.application.analyze_image import AnalyzeImage
from regis.core.model.image_reference import ImageReference
from regis.core.ports.image_inspector import ImageInspector
from regis.registry.client import RegistryClient


def build_analyze_image(username: str | None, password: str | None) -> AnalyzeImage:
    """Wire an AnalyzeImage for the given registry credentials.

    - ``tools``: a shared, stateless SubprocessToolRunner (creds live here).
    - ``inspector_factory``: a fresh regctl ImageInspector per image (creds captured).
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

    return AnalyzeImage(
        tools=SubprocessToolRunner(username, password),
        inspector_factory=_inspector,
    )
