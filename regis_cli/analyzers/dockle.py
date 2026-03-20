"""Dockle analyzer — container image linter for security and best practices."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from typing import Any

from regis_cli.analyzers.base import AnalyzerError, BaseAnalyzer
from regis_cli.registry.client import RegistryClient

logger = logging.getLogger(__name__)


class DockleAnalyzer(BaseAnalyzer):
    """Lints a remote image using Dockle."""

    name = "dockle"
    schema_file = "analyzer/dockle.schema.json"

    @classmethod
    def default_rules(cls) -> list[dict[str, Any]]:
        return [
            {
                "slug": "dockle.no-fatal",
                "description": "No FATAL issues found by Dockle.",
                "level": "critical",
                "tags": ["security"],
                "params": {"max_count": 0},
                "condition": {
                    "<=": [
                        {"var": "results.dockle.issues_by_level.FATAL"},
                        {"var": "rule.params.max_count"},
                    ]
                },
                "messages": {
                    "pass": "Image has no critical CVEs.",  # nosec B105
                    "fail": "Dockle found ${results.dockle.issues_by_level.FATAL} fatal issues (max allowed: ${rule.params.max_count}).",
                },
            },
            {
                "slug": "dockle.max-warnings",
                "description": "Too many Dockle warnings found.",
                "level": "warning",
                "tags": ["security"],
                "params": {"max_count": 5},
                "condition": {
                    "<=": [
                        {"var": "results.dockle.issues_by_level.WARN"},
                        {"var": "rule.params.max_count"},
                    ]
                },
                "messages": {
                    "pass": "Dockle warnings are within acceptable limits (${results.dockle.issues_by_level.WARN}).",  # nosec B105
                    "fail": "Dockle found ${results.dockle.issues_by_level.WARN} warnings (max allowed: ${rule.params.max_count}).",
                },
            },
        ]

    def analyze(
        self,
        client: RegistryClient,
        repository: str,
        tag: str,
        platform: str | None = None,
    ) -> dict[str, Any]:
        """Return a report with dockle violations."""
        registry = client.registry
        if registry == "registry-1.docker.io":
            registry = "docker.io"

        target = f"{registry}/{repository}:{tag}"

        cmd_dockle = ["dockle", "-f", "json", target]

        # Setup environment variables for dockle authentication
        env = os.environ.copy()
        if client.username and client.password:
            env["DOCKER_USER"] = client.username
            env["DOCKER_PASSWORD"] = client.password

        # Not all analyzers support platform properly with dockle, but we can pass it if we want
        # Dockle does not have a native --platform flag out of the box like trivy or skopeo in the
        # same easy way in old versions, but it usually inspects what docker/containerd pulls.
        # Generally, it pulls the manifest. It doesn't strictly have a --platform.
        # We'll omit platform for Dockle to avoid breaking if the CLI flags don't match.

        try:
            res_dockle = subprocess.run(
                cmd_dockle,
                capture_output=True,
                text=True,
                check=False,  # Dockle returns non-zero when fatals are found
                env=env,
            )
        except Exception as e:
            msg = "Dockle execution failed. Ensure dockle is installed and in PATH."
            logger.error(msg)
            raise AnalyzerError(msg) from e

        if not res_dockle.stdout.strip():
            # If stdout is empty, there might be an error in stderr
            msg = f"Dockle produced no output. stderr: {res_dockle.stderr}"
            logger.error(msg)
            raise AnalyzerError(msg)

        try:
            output = json.loads(res_dockle.stdout)
        except json.JSONDecodeError as e:
            msg = f"Failed to parse dockle output: {res_dockle.stdout}"
            logger.error(msg)
            raise AnalyzerError(msg) from e

        # Parse Dockle JSON output
        # Dockle JSON format typically looks like:
        # {
        #   "summary": { "fatal": 1, "warn": 2, "info": 0, "skip": 0, "pass": 15 },
        #   "details": [
        #     { "code": "CIS-DI-0001", "title": "Create a user...", "level": "FATAL", "alerts": ["..."] }
        #   ]
        # }

        details = output.get("details", [])

        mapped_issues = []
        issues_by_level = {"FATAL": 0, "WARN": 0, "INFO": 0, "SKIP": 0, "PASS": 0}

        for issue in details:
            level = issue.get("level", "INFO").upper()
            if level in issues_by_level:
                issues_by_level[level] += 1
            else:
                issues_by_level[level] = issues_by_level.get(level, 0) + 1

            # Only count relevant issues, PASS/SKIP might not be strictly "violations"
            # but we list them if dockle returns them. Let's record them.
            mapped_issues.append(
                {
                    "code": issue.get("code", "UNKNOWN"),
                    "level": level,
                    "title": issue.get("title", ""),
                    "alerts": issue.get("alerts", []),
                }
            )

        # Is it a pass? Dockle defines "passed" usually when there are no FATAL errors (or WARN depending on run).
        # To align with Hadolint, we could say passed if there are no FATAL and WARN,
        # or we just rely on `issues_count` filtering for actual problems.
        # Typically dockle exits with 0 if no FATAL.
        passed = issues_by_level.get("FATAL", 0) == 0

        # Count total issues ignoring PASS
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
