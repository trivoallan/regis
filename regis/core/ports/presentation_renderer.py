"""PresentationRenderer port — renders playbook-directed presentation output."""

from __future__ import annotations

from abc import ABC, abstractmethod

from regis.core.model.report import Report


class PresentationRenderer(ABC):
    """Driven port: render the presentation templates a report's playbooks request.

    Implementations execute the Cookiecutter templates surfaced by playbook
    ``presentation`` directives, writing to a configured destination. It is a
    no-op when the report declares no templates.
    """

    @abstractmethod
    def render(self, report: Report) -> None:
        """Render any presentation templates declared in ``report``'s playbooks."""
