"""Dockle analyzer — container image linter for security and best practices."""

from __future__ import annotations

from typing import Any

from regis.analyzers.base import BaseAnalyzer
from regis.core.domain.context import AnalysisContext


class DockleAnalyzer(BaseAnalyzer):
    """Lints a remote image using Dockle."""

    name = "dockle"
    schema_file = "analyzer/dockle.schema.json"
    uses_context = True

    @classmethod
    def default_criteria(cls) -> list[dict[str, Any]]:
        return [
            {
                "slug": "severity-count",
                "description": "Max allowed issues for a given severity level.",
                "level": "warning",
                "tags": ["security"],
                "params": {"level": "FATAL", "max_count": 0},
                "condition": {
                    "<=": [
                        {
                            "get": [
                                {"var": "results.dockle.issues_by_level"},
                                {"var": "criterion.params.level"},
                            ]
                        },
                        {"var": "criterion.params.max_count"},
                    ]
                },
                "messages": {
                    "pass": "Dockle ${criterion.params.level} issues are within limits.",  # nosec B105
                    "fail": "Dockle found ${results.dockle.issues_by_level.${criterion.params.level}} ${criterion.params.level} issues (max allowed: ${criterion.params.max_count}).",
                },
            },
        ]

    def analyze(self, ctx: AnalysisContext) -> dict[str, Any]:  # type: ignore[override]
        """Return a report with dockle violations."""
        output = ctx.tools.audit_image(ctx.image)
        repository = ctx.image.repository
        tag = ctx.image.tag

        details = output.get("details", [])

        mapped_issues = []
        issues_by_level = {"FATAL": 0, "WARN": 0, "INFO": 0, "SKIP": 0, "PASS": 0}

        for issue in details:
            level = issue.get("level", "INFO").upper()
            if level in issues_by_level:
                issues_by_level[level] += 1
            else:
                issues_by_level[level] = issues_by_level.get(level, 0) + 1
            mapped_issues.append(
                {
                    "code": issue.get("code", "UNKNOWN"),
                    "level": level,
                    "title": issue.get("title", ""),
                    "alerts": issue.get("alerts", []),
                }
            )

        passed = issues_by_level.get("FATAL", 0) == 0
        issues_count = (
            issues_by_level.get("FATAL", 0)
            + issues_by_level.get("WARN", 0)
            + issues_by_level.get("INFO", 0)
        )

        return {
            "analyzer": self.name,
            "repository": repository,
            "tag": tag,
            "passed": passed,
            "issues_count": issues_count,
            "issues_by_level": issues_by_level,
            "issues": mapped_issues,
        }
