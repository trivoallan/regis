"""Tests for the CookiecutterPresentationRenderer adapter."""

from __future__ import annotations

from unittest.mock import patch

from regis.adapters.driven.report.presentation_renderer import (
    CookiecutterPresentationRenderer,
)
from regis.core.model.report import Report


def test_render_delegates_to_util_with_payload_and_template():
    renderer = CookiecutterPresentationRenderer(output_dir_template="reports/x")
    payload = {"playbooks": [], "results": {}}

    with patch(
        "regis.adapters.driven.report.presentation_renderer.render_presentation_templates"
    ) as mock_util:
        renderer.render(Report(payload))

    mock_util.assert_called_once_with(payload, "reports/x")


def test_fake_presentation_renderer_records_calls():
    from tests.fakes import FakePresentationRenderer

    fake = FakePresentationRenderer()
    report = Report({"playbooks": []})
    fake.render(report)
    assert fake.rendered == [report]
