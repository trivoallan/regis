"""The fakes implement their ports and return canned data with no I/O."""

from pathlib import Path

from regis.core.application.analyzer_provider import AnalyzerProvider
from regis.core.model.image_reference import ImageReference
from regis.core.model.report import Report
from regis.core.ports.image_inspector import ImageInspector
from regis.core.ports.report_sink import ReportSink
from regis.core.ports.tool_runner import ToolRunner
from tests.fakes import (
    FakeImageInspector,
    FakeReportSink,
    FakeToolRunner,
    StubAnalyzerProvider,
)

IMG = ImageReference(registry="docker.io", repository="library/nginx", tag="1.27")


def test_fakes_are_instances_of_their_ports() -> None:
    assert isinstance(FakeImageInspector(), ImageInspector)
    assert isinstance(FakeToolRunner(), ToolRunner)
    assert isinstance(FakeReportSink(), ReportSink)
    assert isinstance(StubAnalyzerProvider({}), AnalyzerProvider)


def test_fake_tool_runner_returns_canned() -> None:
    runner = FakeToolRunner(scan_vulnerabilities={"matches": [1, 2]})
    assert runner.scan_vulnerabilities(IMG) == {"matches": [1, 2]}
    assert runner.generate_sbom(IMG) == {}  # default empty


def test_fake_report_sink_records_emissions() -> None:
    sink = FakeReportSink()
    paths = sink.emit(
        Report(payload={}), formats=["json", "html"], output_dir=Path("/out")
    )
    assert paths == [Path("/out/report.json"), Path("/out/report.html")]
    assert len(sink.emitted) == 1


def test_stub_analyzer_provider_returns_mapping() -> None:
    provider = StubAnalyzerProvider({"cve": object})
    assert provider.available() == {"cve": object}


def test_fake_image_inspector_copies_and_honors_sentinel() -> None:
    inspector = FakeImageInspector(tags=["1.27"], blob={"config": "x"}, digest=None)
    # Returned containers are independent (shallow) copies — top-level mutation must not leak.
    inspector.list_tags().append("evil")
    assert inspector.list_tags() == ["1.27"]
    inspector.get_blob("sha256:x")["leak"] = True
    assert inspector.get_blob("sha256:x") == {"config": "x"}
    # digest sentinel honored (None is valid for str | None); default is "sha256:fake".
    assert inspector.get_digest("1.27") is None
    assert FakeImageInspector().get_digest("1.27") == "sha256:fake"
