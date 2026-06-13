"""The core exception hierarchy and the AnalyzerError re-home."""

from regis.analyzers.base import AnalyzerError as ReexportedAnalyzerError
from regis.core.domain.errors import (
    AnalyzerError,
    PlaybookError,
    RegisError,
    RegistryError,
    ReportError,
    ToolError,
)

CORE_SUBCLASSES = [AnalyzerError, RegistryError, ToolError, ReportError, PlaybookError]


def test_regis_error_is_exception() -> None:
    assert issubclass(RegisError, Exception)


def test_all_core_errors_derive_from_regis_error() -> None:
    for cls in CORE_SUBCLASSES:
        assert issubclass(cls, RegisError)


def test_base_module_reexports_core_analyzer_error() -> None:
    # Re-home must preserve identity so existing `except AnalyzerError` keeps working.
    assert ReexportedAnalyzerError is AnalyzerError
