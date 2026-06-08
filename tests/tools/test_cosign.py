from __future__ import annotations

import shutil
from unittest.mock import MagicMock, patch

import pytest

from regis.tools.cosign import CosignUnavailable, CosignVerificationFailed, verify_blob
from regis.tools.manifest import CosignPolicy


def test_verify_blob_returns_unavailable_when_cosign_not_in_path(monkeypatch, tmp_path):
    monkeypatch.setattr(shutil, "which", lambda _name: None)
    policy = CosignPolicy(issuer="https://example", identity_regex=".*")
    blob = tmp_path / "x.bin"
    blob.write_bytes(b"hi")
    with pytest.raises(CosignUnavailable):
        verify_blob(blob, "https://example.com/x.bin", policy)


def test_verify_blob_success(monkeypatch, tmp_path):
    monkeypatch.setattr("regis.tools.cosign.shutil.which", lambda _n: "/usr/bin/cosign")
    blob = tmp_path / "artifact.bin"
    blob.write_bytes(b"data")
    policy = CosignPolicy(
        issuer="https://token.actions.githubusercontent.com",
        identity_regex="^https://github\\.com/org/.*",
    )
    with patch("regis.tools.cosign.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stderr="", stdout="")
        verify_blob(blob, "https://r.example.com/bin.tar.gz", policy)
    cmd = run.call_args[0][0]
    assert cmd[1] == "verify-blob"
    assert "--signature" in cmd
    assert "https://r.example.com/bin.tar.gz.sig" in cmd
    assert "--certificate" in cmd
    assert "https://r.example.com/bin.tar.gz.pem" in cmd
    assert "--certificate-oidc-issuer" in cmd
    assert "https://token.actions.githubusercontent.com" in cmd
    assert "--certificate-identity-regexp" in cmd
    assert "^https://github\\.com/org/.*" in cmd
    assert str(blob) in cmd


def test_verify_blob_failure_uses_stderr(monkeypatch, tmp_path):
    monkeypatch.setattr("regis.tools.cosign.shutil.which", lambda _n: "/usr/bin/cosign")
    blob = tmp_path / "a.bin"
    blob.write_bytes(b"x")
    policy = CosignPolicy(issuer="i", identity_regex="r")
    with patch("regis.tools.cosign.subprocess.run") as run:
        run.return_value = MagicMock(returncode=1, stderr="bad signature", stdout="")
        with pytest.raises(CosignVerificationFailed) as exc:
            verify_blob(blob, "https://r.example.com/bin.tar.gz", policy)
    assert "bad signature" in str(exc.value)


def test_verify_blob_failure_falls_back_to_stdout(monkeypatch, tmp_path):
    monkeypatch.setattr("regis.tools.cosign.shutil.which", lambda _n: "/usr/bin/cosign")
    blob = tmp_path / "a.bin"
    blob.write_bytes(b"x")
    policy = CosignPolicy(issuer="i", identity_regex="r")
    with patch("regis.tools.cosign.subprocess.run") as run:
        run.return_value = MagicMock(returncode=1, stderr="", stdout="stdout error")
        with pytest.raises(CosignVerificationFailed) as exc:
            verify_blob(blob, "https://r.example.com/bin.tar.gz", policy)
    assert "stdout error" in str(exc.value)
