"""AnalysisContext bundles the image and the domain-facing ports."""

from unittest.mock import create_autospec

from regis.core.domain.context import AnalysisContext
from regis.core.model.image_reference import ImageReference
from regis.core.ports.image_inspector import ImageInspector
from regis.core.ports.tool_runner import ToolRunner


def test_analysis_context_holds_image_and_ports() -> None:
    # Field set catches an added/removed/renamed field.
    assert set(AnalysisContext.__dataclass_fields__) == {"image", "inspector", "tools"}

    # Construction + attribute round-trip exercises the dataclass itself.
    image = ImageReference(registry="docker.io", repository="library/nginx", tag="1.27")
    inspector = create_autospec(ImageInspector, instance=True)
    tools = create_autospec(ToolRunner, instance=True)
    ctx = AnalysisContext(image=image, inspector=inspector, tools=tools)
    assert ctx.image is image
    assert ctx.inspector is inspector
    assert ctx.tools is tools
