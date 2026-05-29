"""Subprocess wrapper for the regctl OCI registry client.

Centralizes regctl invocation, credential injection, and reference building for
every analyzer that inspects remote images. Replaces the per-analyzer skopeo
wrappers.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import subprocess  # nosec B404
import tempfile
from typing import TYPE_CHECKING

from regis.analyzers.base import AnalyzerError

if TYPE_CHECKING:
    from regis.registry.client import RegistryClient

logger = logging.getLogger(__name__)

#: Default timeout for regctl calls (seconds).
DEFAULT_TIMEOUT = 60


def image_ref(registry: str, repository: str, ref: str) -> str:
    """Build a regctl image reference (no ``docker://`` scheme).

    Uses ``@`` for digests (``sha256:…``) and ``:`` for tags. Normalizes the
    Docker Hub API host to ``docker.io``.
    """
    if registry == "registry-1.docker.io":
        registry = "docker.io"
    separator = "@" if ref.startswith("sha256:") else ":"
    return f"{registry}/{repository}{separator}{ref}"


def _temp_docker_config(client: RegistryClient) -> str:
    """Write a temp Docker config.json with the client's credentials.

    Used when credentials contain a comma, which would break regctl's
    ``--host`` comma-separated ``key=val`` parsing. Returns the config dir to
    pass via ``DOCKER_CONFIG``.
    """
    auth = base64.b64encode(f"{client.username}:{client.password}".encode()).decode()
    config = {"auths": {client.registry: {"auth": auth}}}
    tmpdir = tempfile.mkdtemp(prefix="regis-regctl-")
    with open(os.path.join(tmpdir, "config.json"), "w", encoding="utf-8") as handle:
        json.dump(config, handle)
    return tmpdir


def run_regctl(
    client: RegistryClient,
    args: list[str],
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """Run regctl with *args*, injecting credentials if present.

    Credentials are passed inline via the global ``--host`` flag. If a
    credential contains a comma, they are written to a per-call temporary Docker
    config and passed via ``DOCKER_CONFIG`` instead (thread-safe: a fresh
    tempdir per call).

    Args:
        client: Registry client carrying the host and optional credentials.
        args: regctl subcommand and arguments, e.g. ``["image", "inspect", ref]``.
        timeout: Subprocess timeout in seconds.

    Returns:
        The command's stdout.

    Raises:
        AnalyzerError: if regctl is not installed.
        subprocess.CalledProcessError: if regctl exits non-zero.
    """
    cmd = ["regctl"]
    env = dict(os.environ)

    if client.username and client.password:
        if "," in client.username or "," in client.password:
            env["DOCKER_CONFIG"] = _temp_docker_config(client)
        else:
            cmd += [
                "--host",
                f"reg={client.registry},user={client.username},pass={client.password}",
            ]

    cmd += args
    logger.debug("Running regctl: %s", " ".join(c for c in cmd if "pass=" not in c))
    try:
        result = subprocess.run(  # nosec B603
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
            env=env,
        )
        return result.stdout
    except FileNotFoundError:
        raise AnalyzerError(
            "regctl not found. Ensure it is installed and in PATH."
        ) from None
