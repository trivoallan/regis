"""AnalyzerProvider is an abstract driven port (core.ports)."""

import pytest

from regis.core.ports.analyzer_provider import AnalyzerProvider


def test_analyzer_provider_is_abstract() -> None:
    with pytest.raises(TypeError):
        AnalyzerProvider()
