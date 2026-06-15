"""Tests for the CLI composition root."""

from __future__ import annotations

from regis.adapters.driven.registry.regctl_image_inspector import RegctlImageInspector
from regis.adapters.driven.report.file_report_sink import FileReportSink
from regis.adapters.driven.tools.subprocess_tool_runner import SubprocessToolRunner
from regis.adapters.driving.cli.composition import build_analyze_image
from regis.core.application.analyze_image import AnalyzeImage
from regis.core.model.image_reference import ImageReference

IMAGE = ImageReference(registry="reg.example", repository="ns/app", tag="1.0")


def test_build_returns_wired_analyze_image():
    uc = build_analyze_image("user", "pass")
    assert isinstance(uc, AnalyzeImage)
    assert isinstance(uc._tools, SubprocessToolRunner)


def test_inspector_factory_builds_regctl_inspector_for_image():
    uc = build_analyze_image("user", "pass")
    inspector = uc._inspector_factory(IMAGE)
    assert isinstance(inspector, RegctlImageInspector)


def test_build_wires_file_report_sink_with_default_template():
    """Default call wires a FileReportSink with the default output_dir_template."""
    uc = build_analyze_image("user", "pass")
    assert isinstance(uc._sink, FileReportSink)


def test_build_captures_custom_output_dir_template():
    """Custom output_dir_template is forwarded to the FileReportSink."""
    uc = build_analyze_image("user", "pass", output_dir_template="reports/custom")
    assert isinstance(uc._sink, FileReportSink)
    assert uc._sink._output_dir_template == "reports/custom"
