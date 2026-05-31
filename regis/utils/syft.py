"""Subprocess wrapper for the syft SBOM generator.

Centralizes syft invocation, registry-credential injection, and CycloneDX-JSON
parsing. Mirrors regis/utils/grype.py.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess  # nosec B404
from typing import Any

import click

from regis.analyzers.base import AnalyzerError
from regis.utils.process import ensure_tool

logger = logging.getLogger(__name__)

#: Default timeout for syft calls (seconds).
DEFAULT_TIMEOUT = 300


def run_syft(
    image: str,
    username: str | None = None,
    password: str | None = None,
    platform: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Run ``syft <image> -o cyclonedx-json`` and return parsed JSON.

    Args:
        image: Full image reference (e.g. ``registry/repo:tag``).
        username: Optional registry username.
        password: Optional registry password.
        platform: Optional platform string (e.g. ``linux/arm64``).
        timeout: Subprocess timeout in seconds.

    Returns:
        The parsed syft CycloneDX-JSON document.

    Raises:
        AnalyzerError: if syft is missing, fails, or emits invalid JSON.
    """
    try:
        syft_path = ensure_tool("syft")
    except click.ClickException as exc:
        raise AnalyzerError(str(exc)) from exc

    env = os.environ.copy()
    user = username or env.get("REGIS_USERNAME")
    pwd = password or env.get("REGIS_PASSWORD")
    if user and pwd:
        env["SYFT_REGISTRY_AUTH_USERNAME"] = user
        env["SYFT_REGISTRY_AUTH_PASSWORD"] = pwd

    cmd = [syft_path, image, "-o", "cyclonedx-json"]
    if platform:
        cmd.extend(["--platform", platform])

    logger.debug("Running syft on %s", image)
    try:
        result = subprocess.run(  # nosec B603
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
            env=env,
        )
        return json.loads(result.stdout)  # type: ignore[no-any-return]
    except subprocess.CalledProcessError as exc:
        raise AnalyzerError(f"syft failed: {exc.stderr}") from exc
    except subprocess.TimeoutExpired as exc:
        raise AnalyzerError(f"syft timed out after {timeout}s") from exc
    except json.JSONDecodeError as exc:
        raise AnalyzerError(f"syft produced invalid JSON: {exc}") from exc
