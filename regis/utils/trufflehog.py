"""Subprocess wrapper for the trufflehog secret scanner.

Runs ``trufflehog docker --image <ref> --json`` and parses the NDJSON output.
The exit code is not used to detect failure (trufflehog exits 0 even with
findings unless ``--fail`` is passed); an unparseable line is the failure
signal instead. Credentials, when present, are forwarded via a temporary
``DOCKER_CONFIG`` (trufflehog has no basic-auth env pair) -- same pattern as
regis/utils/regctl.py.

Known limitation: a failed remote-registry pull also yields exit 0 + empty
stdout, which is indistinguishable from "no secrets found".
"""

from __future__ import annotations

import base64
import json
import logging
import os
import shutil
import subprocess  # nosec B404
import tempfile
from typing import Any

from regis.core.domain.errors import ToolError
from regis.utils.process import ensure_tool

logger = logging.getLogger(__name__)

#: Default timeout for trufflehog calls (seconds).
DEFAULT_TIMEOUT = 300


def _registry_host(image: str) -> str:
    """Derive the docker-config auths key (registry host) from an image ref."""
    first = image.split("/", 1)[0]
    if "." in first or ":" in first or first == "localhost":
        return first
    return "https://index.docker.io/v1/"  # Docker Hub default auths key


def _write_docker_config(host: str, user: str, pwd: str) -> str:
    """Write a temp Docker config.json with credentials; return its dir.

    Cleans up the temp directory if the write fails. The caller is responsible
    for removing the directory after the subprocess finishes.
    """
    auth = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    config = {"auths": {host: {"auth": auth}}}
    tmpdir = tempfile.mkdtemp(prefix="regis-trufflehog-")
    try:
        with open(os.path.join(tmpdir, "config.json"), "w", encoding="utf-8") as handle:
            json.dump(config, handle)
    except Exception:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise
    return tmpdir


def run_trufflehog(
    image: str,
    username: str | None = None,
    password: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> list[dict[str, Any]]:
    """Run trufflehog against a container image and return parsed findings.

    Args:
        image: Full image reference.
        username: Optional registry username (forwarded via temp DOCKER_CONFIG).
        password: Optional registry password (forwarded via temp DOCKER_CONFIG).
        timeout: Subprocess timeout in seconds.

    Returns:
        A list of finding dicts (one per NDJSON line).

    Raises:
        ToolError: if trufflehog is missing, times out, or emits a line
            that is not valid JSON.
    """
    th_path = ensure_tool("trufflehog")

    env = os.environ.copy()
    user = username or env.get("REGIS_USERNAME")
    pwd = password or env.get("REGIS_PASSWORD")
    docker_config_dir: str | None = None
    if user and pwd:
        docker_config_dir = _write_docker_config(_registry_host(image), user, pwd)
        env["DOCKER_CONFIG"] = docker_config_dir

    cmd = [th_path, "docker", "--image", image, "--json", "--no-update"]

    logger.debug("Running trufflehog on %s", image)
    try:
        result = subprocess.run(  # nosec B603
            cmd,
            capture_output=True,
            text=True,
            check=False,  # trufflehog exits 0 even with findings (no --fail)
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise ToolError(f"trufflehog timed out after {timeout}s") from exc
    finally:
        if docker_config_dir:
            shutil.rmtree(docker_config_dir, ignore_errors=True)

    findings: list[dict[str, Any]] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            findings.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ToolError(f"trufflehog produced invalid JSON: {exc}") from exc
    return findings
