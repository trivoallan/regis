"""Core exception hierarchy for regis.

All errors raised inside the hexagonal core (domain, application) and by the
driven adapters derive from :class:`RegisError`. Only the driving CLI adapter
translates these into ``click.ClickException`` at the process boundary — the
core never imports ``click``.
"""


class RegisError(Exception):
    """Base class for all regis errors."""


class AnalyzerError(RegisError):
    """Raised when an analyzer encounters an error."""


class RegistryError(RegisError):
    """Raised when the registry adapter fails (HTTP, auth, manifest)."""


class ToolError(RegisError):
    """Raised when an external tool is missing, fails, times out, or emits bad output."""


class ReportError(RegisError):
    """Raised when report emission fails."""


class PlaybookError(RegisError):
    """Raised when a playbook cannot be loaded, validated, or evaluated."""
