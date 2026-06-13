"""AnalysisContext — the capabilities bundle passed to an analyzer."""

from __future__ import annotations

from dataclasses import dataclass

from regis.core.model.image_reference import ImageReference
from regis.core.ports.image_inspector import ImageInspector
from regis.core.ports.tool_runner import ToolRunner


@dataclass
class AnalysisContext:
    """What an analyzer receives: the image under analysis and the ports it may use."""

    image: ImageReference
    inspector: ImageInspector
    tools: ToolRunner
