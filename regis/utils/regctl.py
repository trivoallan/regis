"""Subprocess wrapper for the regctl OCI registry client.

Centralizes regctl invocation, credential injection, and reference building for
every analyzer that inspects remote images. Replaces the per-analyzer
registry-CLI wrappers.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import shutil
import subprocess  # nosec B404
import tempfile
from dataclasses import dataclass
from typing import Protocol

from regis.core.domain.errors import RegistryError, ToolError
from regis.utils.process import ensure_tool

logger = logging.getLogger(__name__)

#: Default timeout for regctl calls (seconds).
DEFAULT_TIMEOUT = 60


class _RegistryCredentials(Protocol):
    """Duck-typed credential carrier consumed by ``run_regctl``."""

    @property
    def registry(self) -> str: ...

    @property
    def username(self) -> str | None: ...

    @property
    def password(self) -> str | None: ...


def image_ref(registry: str, repository: str, ref: str) -> str:
    """Build a regctl image reference (no ``docker://`` scheme).

    Uses ``@`` for digests (``sha256:…``) and ``:`` for tags. Normalizes the
    Docker Hub API host to ``docker.io``.
    """
    if registry == "registry-1.docker.io":
        registry = "docker.io"
    separator = "@" if ref.startswith("sha256:") else ":"
    return f"{registry}/{repository}{separator}{ref}"


def _temp_docker_config(client: _RegistryCredentials) -> str:
    """Write a temp Docker config.json with the client's credentials.

    Used when credentials contain a comma, which would break regctl's
    ``--host`` comma-separated ``key=val`` parsing. Returns the config dir to
    pass via ``DOCKER_CONFIG``.

    Cleans up the temp directory if the file write fails.
    """
    auth = base64.b64encode(f"{client.username}:{client.password}".encode()).decode()
    config = {"auths": {client.registry: {"auth": auth}}}
    tmpdir = tempfile.mkdtemp(prefix="regis-regctl-")
    try:
        with open(os.path.join(tmpdir, "config.json"), "w", encoding="utf-8") as handle:
            json.dump(config, handle)
    except Exception:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise
    return tmpdir


def run_regctl(
    client: _RegistryCredentials,
    args: list[str],
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """Run regctl with *args*, injecting credentials if present.

    Credentials are passed inline via the global ``--host`` flag. If a
    credential contains a comma, they are written to a per-call temporary Docker
    config and passed via ``DOCKER_CONFIG`` instead (thread-safe: a fresh
    tempdir per call). The temp directory is always removed after the subprocess
    finishes.

    Args:
        client: Registry client carrying the host and optional credentials.
        args: regctl subcommand and arguments, e.g. ``["image", "inspect", ref]``.
        timeout: Subprocess timeout in seconds.

    Returns:
        The command's stdout.

    Raises:
        RegistryError: if regctl is not installed, the call times out, or exits
            non-zero.
    """
    try:
        regctl_bin = ensure_tool("regctl")
    except ToolError as exc:
        raise RegistryError(str(exc)) from exc
    cmd = [regctl_bin]
    env = dict(os.environ)
    docker_config_dir: str | None = None

    if client.username and client.password:
        if "," in client.username or "," in client.password:
            docker_config_dir = _temp_docker_config(client)
            env["DOCKER_CONFIG"] = docker_config_dir
        else:
            cmd += [
                "--host",
                f"reg={client.registry},user={client.username},pass={client.password}",
            ]

    cmd += args
    # Log only the subcommand, never the --host credential string, so the
    # password never reaches the logs.
    logger.debug("Running regctl %s", " ".join(args))
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
        raise RegistryError(
            "regctl not found. Ensure it is installed and in PATH."
        ) from None
    except subprocess.TimeoutExpired:
        raise RegistryError(f"regctl timed out after {timeout}s.") from None
    except subprocess.CalledProcessError as exc:
        raise RegistryError(f"regctl failed: {exc.stderr}") from exc
    finally:
        if docker_config_dir is not None:
            shutil.rmtree(docker_config_dir, ignore_errors=True)


@dataclass(frozen=True)
class _RegctlCreds:
    """Minimal credential carrier accepted by ``run_regctl`` (duck-typed)."""

    registry: str
    username: str | None
    password: str | None


def run_regctl_copy(
    src_ref: str,
    dest_dir: str,
    registry: str,
    username: str | None = None,
    password: str | None = None,
    platform: str | None = None,
    timeout: int = 300,
) -> None:
    """Copy *src_ref* into a local OCI layout directory *dest_dir* via regctl.

    Writes an OCI layout (``index.json``, ``oci-layout``, ``blobs/``) under
    *dest_dir*, tagged ``regis``. Reuses ``run_regctl``'s credential injection.

    Args:
        src_ref: Full remote image reference (e.g. ``docker.io/library/nginx:1.27``).
        dest_dir: Filesystem directory to receive the OCI layout.
        registry: Registry host for credential matching.
        username: Optional registry username.
        password: Optional registry password.
        platform: Optional single platform to copy (e.g. ``linux/amd64``).
        timeout: Subprocess timeout in seconds (image copy can be slow).

    Raises:
        RegistryError: if regctl is missing, times out, or exits non-zero.
    """
    creds = _RegctlCreds(registry, username, password)
    args = ["image", "copy"]
    if platform:
        args += ["--platform", platform]
    args += [src_ref, f"ocidir://{dest_dir}:regis"]
    run_regctl(creds, args, timeout=timeout)
