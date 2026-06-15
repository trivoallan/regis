"""Hadolint analyzer — pseudo-Dockerfile linting."""

from __future__ import annotations

import logging
from typing import Any

from regis.analyzers.base import BaseAnalyzer
from regis.core.domain.context import AnalysisContext
from regis.core.domain.manifest import get_image_config

logger = logging.getLogger(__name__)


class HadolintAnalyzer(BaseAnalyzer):
    """Lints a reverse-engineered Dockerfile using Hadolint."""

    name = "hadolint"
    schema_file = "analyzer/hadolint.schema.json"

    @classmethod
    def default_criteria(cls) -> list[dict[str, Any]]:
        return [
            {
                "slug": "severity-count",
                "description": "Max allowed violations for a given severity level.",
                "level": "warning",
                "tags": ["best-practices"],
                "params": {"level": "error", "max_count": 0},
                "condition": {
                    "<=": [
                        {
                            "get": [
                                {"var": "results.hadolint.issues_by_level"},
                                {"var": "criterion.params.level"},
                            ]
                        },
                        {"var": "criterion.params.max_count"},
                    ]
                },
                "messages": {
                    "pass": "Hadolint ${criterion.params.level} issues are within limits.",  # nosec B105
                    "fail": "Hadolint found ${results.hadolint.issues_by_level.${criterion.params.level}} ${criterion.params.level} issues (max allowed: ${criterion.params.max_count}).",
                },
            },
        ]

    def analyze(self, ctx: AnalysisContext) -> dict[str, Any]:
        """Return a report with hadolint violations."""
        # 1. Resolve platform
        platform = ctx.image.platform or "linux/amd64"
        if "/" in platform:
            os_name, arch = platform.split("/", 1)
        else:
            os_name, arch = "linux", platform

        # 2. Fetch image configuration via the inspector port
        config = get_image_config(ctx.inspector, ctx.image.tag, os_name, arch)
        history = config.get("history", [])

        # 3. Build pseudo-Dockerfile
        dockerfile_lines = ["FROM scratch"]
        for entry in history:
            created_by = entry.get("created_by", "").strip()
            if not created_by:
                continue

            # Standard Dockerfile instruction markers in history
            if "#(nop)" in created_by:
                # E.g., "/bin/sh -c #(nop)  CMD [\"python3\"]" -> "CMD [\"python3\"]"
                parts = created_by.split("#(nop)", 1)
                if len(parts) > 1:
                    instruction = parts[1].strip()
                    if instruction:
                        dockerfile_lines.append(instruction)
            else:
                # It's a standard shell command execution
                # We prepend RUN if it's not empty
                # We strip any `/bin/sh -c` prefixes for cleaner output
                cmd = created_by
                if cmd.startswith("/bin/sh -c "):
                    cmd = cmd[11:].strip()
                if cmd:
                    dockerfile_lines.append(f"RUN {cmd}")

        pseudo_dockerfile = "\n".join(dockerfile_lines)
        logger.debug(
            "Pseudo-Dockerfile for %s:%s:\n%s",
            ctx.image.repository,
            ctx.image.tag,
            pseudo_dockerfile,
        )

        # 4. Lint via the tool runner port (raises ToolError on missing binary / bad output)
        issues = ctx.tools.lint_dockerfile(pseudo_dockerfile)

        # 5. Map issues into by-level counts
        mapped_issues = []
        issues_by_level: dict[str, int] = {
            "error": 0,
            "warning": 0,
            "info": 0,
            "style": 0,
        }

        for issue in issues:
            level = issue.get("level", "info")
            if level in issues_by_level:
                issues_by_level[level] += 1
            else:
                # Fallback for unrecognized levels in the future
                issues_by_level[level] = issues_by_level.get(level, 0) + 1

            mapped_issues.append(
                {
                    "code": issue.get("code", "UNKNOWN"),
                    "level": level,
                    "message": issue.get("message", ""),
                    "line": issue.get("line"),
                }
            )

        return {
            "analyzer": self.name,
            "repository": ctx.image.repository,
            "tag": ctx.image.tag,
            "passed": len(mapped_issues) == 0,
            "issues_count": len(mapped_issues),
            "issues_by_level": issues_by_level,
            "issues": mapped_issues,
            "dockerfile": pseudo_dockerfile,
        }
