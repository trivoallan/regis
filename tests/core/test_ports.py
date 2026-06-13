"""The infra ports are abstract and reference only the model layer."""

import pytest

from regis.core.ports.image_inspector import ImageInspector
from regis.core.ports.report_sink import ReportSink
from regis.core.ports.tool_runner import ToolResult, ToolRunner


@pytest.mark.parametrize("port", [ImageInspector, ToolRunner, ReportSink])
def test_ports_cannot_be_instantiated(port: type) -> None:
    with pytest.raises(TypeError):
        port()  # abstract — has unimplemented abstractmethods


def test_tool_result_is_a_value() -> None:
    r = ToolResult(stdout="out", stderr="", exit_code=0)
    assert (r.stdout, r.exit_code) == ("out", 0)
