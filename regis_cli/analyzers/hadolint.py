"""Hadolint analyzer — pseudo-Dockerfile linting."""

from __future__ import annotations

import json
import logging
import subprocess
from typing import Any

from regis_cli.analyzers.base import AnalyzerError, BaseAnalyzer
from regis_cli.registry.client import RegistryClient

logger = logging.getLogger(__name__)


class HadolintAnalyzer(BaseAnalyzer):
    """Lints a reverse-engineered Dockerfile using Hadolint."""

    name = "hadolint"
    schema_file = "analyzer/hadolint.schema.json"

    @classmethod
    def default_rules(cls) -> list[dict[str, Any]]:
        return [
            {
                "slug": "hadolint.no-error",
                "description": "No 'error' level violations found by Hadolint.",
                "level": "critical",
                "tags": ["best-practices"],
                "params": {"max_count": 0},
                "condition": {
                    "<=": [
                        {"var": "results.hadolint.issues_by_level.error"},
                        {"var": "rule.params.max_count"},
                    ]
                },
                "messages": {
                    "pass": "No hadolint errors detected.",  # nosec B105
                    "fail": "Hadolint found ${results.hadolint.issues_by_level.error} errors.",
                },
            },
            {
                "slug": "hadolint.max-warnings",
                "description": "Limit the number of warnings from Hadolint.",
                "level": "warning",
                "tags": ["best-practices"],
                "params": {"max_count": 5},
                "condition": {
                    "<=": [
                        {"var": "results.hadolint.issues_by_level.warning"},
                        {"var": "rule.params.max_count"},
                    ]
                },
                "messages": {
                    "pass": "Hadolint warnings are within limits.",  # nosec B105
                    "fail": "Too many hadolint warnings: ${results.hadolint.issues_by_level.warning} (max ${rule.params.max_count}).",
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
        """Return a report with hadolint violations."""
        registry = client.registry
        if registry == "registry-1.docker.io":
            registry = "docker.io"

        target = f"docker://{registry}/{repository}:{tag}"

        # 1. Fetch image configuration using Skopeo
        if platform:
            if "/" in platform:
                os_name, arch = platform.split("/", 1)
            else:
                os_name, arch = "linux", platform
        else:
            # Fallback for Hadolint to ensure we get something coherent if not specified
            os_name, arch = "linux", "amd64"

        cmd_skopeo = [
            "skopeo",
            "inspect",
            "--config",
            "--override-os",
            os_name,
            "--override-arch",
            arch,
            target,
        ]
        if client.username and client.password:
            cmd_skopeo.extend(["--creds", f"{client.username}:{client.password}"])

        try:
            res_skopeo = subprocess.run(
                cmd_skopeo, capture_output=True, text=True, check=True
            )
            config = json.loads(res_skopeo.stdout)
        except subprocess.CalledProcessError as e:
            msg = f"Failed to fetch config for {target}: {e.stderr}"
            logger.error(msg)
            raise AnalyzerError(msg) from e
        except Exception as e:
            msg = f"Failed to parse skopeo output for {target}: {e}"
            logger.error(msg)
            raise AnalyzerError(msg) from e

        history = config.get("history", [])

        # 2. Build pseudo-Dockerfile
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
        logger.debug("Pseudo-Dockerfile for %s:\n%s", target, pseudo_dockerfile)

        # 3. Pipe to Hadolint
        cmd_hadolint = ["hadolint", "-f", "json", "-"]
        try:
            res_hadolint = subprocess.run(
                cmd_hadolint,
                input=pseudo_dockerfile,
                capture_output=True,
                text=True,
                check=False,  # hadolint returns non-zero on violations, we handle that
            )
        except FileNotFoundError as e:
            msg = "hadolint not found. Ensure it is installed and in PATH."
            logger.error(msg)
            raise AnalyzerError(msg) from e

        # 4. Parse Hadolint JSON output
        try:
            issues = (
                json.loads(res_hadolint.stdout) if res_hadolint.stdout.strip() else []
            )
        except json.JSONDecodeError as e:
            msg = f"Failed to parse hadolint output: {res_hadolint.stdout}"
            logger.error(msg)
            raise AnalyzerError(msg) from e

        # Basic filtering and mapping
        mapped_issues = []
        issues_by_level = {"error": 0, "warning": 0, "info": 0, "style": 0}

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
            "repository": repository,
            "tag": tag,
            "passed": len(mapped_issues) == 0,
            "issues_count": len(mapped_issues),
            "issues_by_level": issues_by_level,
            "issues": mapped_issues,
            "dockerfile": pseudo_dockerfile,
        }
