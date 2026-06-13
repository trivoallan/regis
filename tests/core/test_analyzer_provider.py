"""AnalyzerProvider is an abstract, application-facing port."""

import pytest

from regis.core.application.analyzer_provider import AnalyzerProvider


def test_analyzer_provider_is_abstract() -> None:
    with pytest.raises(TypeError):
        AnalyzerProvider()
