"""Best-effort cosign verification for downloaded tool binaries."""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
from pathlib import Path

from regis.adapters.driven.tools.manifest import CosignPolicy


class CosignUnavailable(RuntimeError):
    """Raised when the cosign binary is not on PATH."""


class CosignVerificationFailed(RuntimeError):
    """Raised when cosign rejects the signature."""


def verify_blob(blob: Path, source_url: str, policy: CosignPolicy) -> None:
    """Verify *blob* against the keyless-signed signature published next to *source_url*.

    Assumes signature artefacts live at ``{source_url}.sig`` and ``{source_url}.pem`` --
    the layout used by GoReleaser-built projects (grype, syft, trufflehog).
    """
    cosign = shutil.which("cosign")
    if not cosign:
        raise CosignUnavailable("cosign binary not found on PATH")
    cmd = [
        cosign,
        "verify-blob",
        "--certificate-oidc-issuer",
        policy.issuer,
        "--certificate-identity-regexp",
        policy.identity_regex,
        "--signature",
        f"{source_url}.sig",
        "--certificate",
        f"{source_url}.pem",
        str(blob),
    ]
    result = subprocess.run(  # nosec B603
        cmd, capture_output=True, text=True, check=False, timeout=30
    )
    if result.returncode != 0:
        raise CosignVerificationFailed(
            f"cosign verify-blob failed: {result.stderr.strip() or result.stdout.strip()}"
        )
