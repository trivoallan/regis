from typing import Any

import pytest

from regis.core.domain.analyzers.dockle import DockleAnalyzer
from regis.core.domain.context import AnalysisContext
from regis.core.domain.errors import ToolError
from regis.core.model.image_reference import ImageReference
from tests.fakes import FakeImageInspector, FakeToolRunner

_DOCKLE = {
    "summary": {"fatal": 1, "warn": 1, "info": 0, "skip": 0, "pass": 3},
    "details": [
        {
            "code": "CIS-DI-0001",
            "title": "root user",
            "level": "FATAL",
            "alerts": ["a"],
        },
        {
            "code": "CIS-DI-0005",
            "title": "content trust",
            "level": "WARN",
            "alerts": [],
        },
    ],
}


def _dockle_ctx(tools, *, repository="library/nginx", tag="1.27"):
    return AnalysisContext(
        image=ImageReference(registry="docker.io", repository=repository, tag=tag),
        inspector=FakeImageInspector(),
        tools=tools,
    )


class TestDockleAnalyzer:
    def test_analyze_maps_levels_and_passed(self):
        report = DockleAnalyzer().analyze(
            _dockle_ctx(FakeToolRunner(audit_image=_DOCKLE))
        )
        assert report["analyzer"] == "dockle"
        assert report["issues_by_level"]["FATAL"] == 1
        assert report["issues_by_level"]["WARN"] == 1
        assert report["passed"] is False  # FATAL present
        assert report["issues_count"] == 2  # FATAL + WARN + INFO
        assert report["repository"] == "library/nginx"
        assert report["tag"] == "1.27"
        DockleAnalyzer().validate(report)

    def test_passed_true_without_fatal(self):
        clean = {
            "details": [{"code": "X", "title": "t", "level": "INFO", "alerts": []}]
        }
        report = DockleAnalyzer().analyze(
            _dockle_ctx(FakeToolRunner(audit_image=clean))
        )
        assert report["passed"] is True

    def test_propagates_tool_error(self):
        class _Boom(FakeToolRunner):
            def audit_image(self, image: ImageReference) -> dict[str, Any]:
                raise ToolError("dockle missing")

        with pytest.raises(ToolError, match="dockle missing"):
            DockleAnalyzer().analyze(_dockle_ctx(_Boom()))

    def test_default_criteria(self):
        criteria = DockleAnalyzer.default_criteria()
        assert len(criteria) >= 1
        assert criteria[0]["slug"] == "severity-count"
        assert criteria[0]["params"]["level"] == "FATAL"

    def test_pass_and_unknown_levels_counted_but_excluded_from_issues_count(self):
        data = {
            "details": [
                {"code": "P", "title": "ok", "level": "PASS", "alerts": []},
                {"code": "D", "title": "dbg", "level": "DEBUG", "alerts": []},
                {"code": "F", "title": "bad", "level": "FATAL", "alerts": ["x"]},
            ]
        }
        report = DockleAnalyzer().analyze(_dockle_ctx(FakeToolRunner(audit_image=data)))
        # PASS is counted in its bucket; DEBUG is an unknown level (else branch).
        assert report["issues_by_level"]["PASS"] == 1
        assert report["issues_by_level"]["DEBUG"] == 1
        # issues_count sums only FATAL+WARN+INFO → PASS and DEBUG are excluded.
        assert report["issues_count"] == 1
        assert report["passed"] is False
