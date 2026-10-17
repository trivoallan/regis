"""SubprocessToolRunner — ToolRunner backed by external scanner subprocesses."""

from __future__ import annotations

import json
import os
import shutil
import subprocess  # nosec B404
from collections.abc import Sequence
from typing import Any

from regis.core.domain.errors import RegistryError, ToolError
from regis.core.model.image_reference import ImageReference
from regis.core.ports.tool_runner import ToolResult, ToolRunner
from regis.utils.grype import run_grype
from regis.utils.process import ensure_tool
from regis.utils.regctl import _temp_docker_config, run_regctl_copy
from regis.utils.syft import run_syft
from regis.utils.trufflehog import run_trufflehog

#: cosign errors that mean "no acceptable signature", not "could not verify".
_COSIGN_NO_MATCH = ("no matching", "no signatures found")


class SubprocessToolRunner(ToolRunner):
    """Runs external scanners as subprocesses.

    Registry credentials live here (injected by the composition root in P3), so
    the core never sees a password. The ``ImageReference`` carries no creds; this
    adapter builds the full ``registry/repo:tag`` string and injects auth per tool.
    """

    def __init__(
        self, username: str | None = None, password: str | None = None
    ) -> None:
        self._username = username
        self._password = password

    @staticmethod
    def _full_ref(image: ImageReference) -> str:
        # Digests join with ``@``, tags with ``:`` (mirrors regctl.image_ref).
        separator = "@" if image.tag.startswith("sha256:") else ":"
        return f"{image.registry}/{image.repository}{separator}{image.tag}"

    def scan_vulnerabilities(self, image: ImageReference) -> dict[str, Any]:
        return run_grype(
            self._full_ref(image), self._username, self._password, image.platform
        )

    def generate_sbom(self, image: ImageReference) -> dict[str, Any]:
        return run_syft(
            self._full_ref(image), self._username, self._password, image.platform
        )

    def export_layout(self, image: ImageReference, dest_dir: str) -> bool:
        """Copy *image* into a local OCI layout at *dest_dir*; return success.

        A failed export (network/auth) returns ``False`` so the caller falls
        back to a direct remote scan instead of aborting the run.

        Multi-arch images are always narrowed to a single platform: the
        explicitly requested one, or ``"local"`` (regctl resolves it to the
        host OS/arch). This is required because syft and grype cannot consume
        an OCI image *index* from an oci-dir; they need a single manifest.
        """
        try:
            run_regctl_copy(
                self._full_ref(image),
                dest_dir,
                image.registry,
                self._username,
                self._password,
                image.platform or "local",
            )
            return True
        except (RegistryError, ToolError):
            return False

    def generate_sbom_from_layout(self, dest_dir: str) -> dict[str, Any]:
        """Run syft against a local OCI layout (no pull, no creds, no platform)."""
        return run_syft(f"oci-dir:{dest_dir}")

    def scan_vulnerabilities_from_layout(self, dest_dir: str) -> dict[str, Any]:
        """Run grype against a local OCI layout (no pull, no creds, no platform)."""
        return run_grype(f"oci-dir:{dest_dir}")

    def scan_secrets(self, image: ImageReference) -> list[dict[str, Any]]:
        return run_trufflehog(self._full_ref(image), self._username, self._password)

    def lint_dockerfile(self, dockerfile: str) -> list[dict[str, Any]]:
        binary = ensure_tool("hadolint")
        proc = subprocess.run(  # nosec B603
            [binary, "-f", "json", "-"],
            input=dockerfile,
            capture_output=True,
            text=True,
            check=False,
        )
        stdout = proc.stdout.strip()
        if not stdout:
            return []
        try:
            issues: list[dict[str, Any]] = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise ToolError(f"hadolint produced invalid JSON: {exc}") from exc
        return issues

    def audit_image(self, image: ImageReference) -> dict[str, Any]:
        binary = ensure_tool("dockle")
        env = os.environ.copy()
        if self._username and self._password:
            env["DOCKER_USER"] = self._username
            env["DOCKER_PASSWORD"] = self._password
        proc = subprocess.run(  # nosec B603
            [binary, "-f", "json", self._full_ref(image)],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        if not proc.stdout.strip():
            raise ToolError(f"dockle produced no output. stderr: {proc.stderr}")
        try:
            report: dict[str, Any] = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise ToolError(f"dockle produced invalid JSON: {exc}") from exc
        return report

    def verify_signature(
        self, image: ImageReference, *, identity: str, issuer: str
    ) -> bool:
        binary = ensure_tool("cosign")
        args = [
            binary,
            "verify",
            self._full_ref(image),
            "--certificate-identity",
            identity,
            "--certificate-oidc-issuer",
            issuer,
        ]
        trusted_root = os.environ.get("REGIS_COSIGN_TRUSTED_ROOT")
        if trusted_root:
            args += ["--trusted-root", trusted_root]
        env = os.environ.copy()
        config_dir = None
        if self._username and self._password:
            config_dir = _temp_docker_config(
                _Credentials(image.registry, self._username, self._password)
            )
            env["DOCKER_CONFIG"] = config_dir
        try:
            proc = subprocess.run(  # nosec B603
                args, capture_output=True, text=True, check=False, env=env
            )
        finally:
            if config_dir:
                shutil.rmtree(config_dir, ignore_errors=True)
        if proc.returncode == 0:
            return True
        if any(marker in proc.stderr for marker in _COSIGN_NO_MATCH):
            return False
        raise ToolError(f"cosign verify failed: {proc.stderr.strip()[-500:]}")

    def run(
        self, tool: str, args: Sequence[str], *, timeout: int | None = None
    ) -> ToolResult:
        binary = ensure_tool(tool)
        try:
            proc = subprocess.run(  # nosec B603
                [binary, *args],
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise ToolError(f"{tool} timed out after {timeout}s") from exc
        return ToolResult(
            stdout=proc.stdout, stderr=proc.stderr, exit_code=proc.returncode
        )


class _Credentials:
    """Registry credentials in the shape ``_temp_docker_config`` reads."""

    def __init__(self, registry: str, username: str, password: str) -> None:
        self.registry = registry
        self.username: str | None = username
        self.password: str | None = password
