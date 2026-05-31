from __future__ import annotations

import shutil

import pytest

from regis.tools.cosign import CosignUnavailable, verify_blob
from regis.tools.manifest import CosignPolicy


def test_verify_blob_returns_unavailable_when_cosign_not_in_path(monkeypatch, tmp_path):
    monkeypatch.setattr(shutil, "which", lambda _name: None)
    policy = CosignPolicy(issuer="https://example", identity_regex=".*")
    blob = tmp_path / "x.bin"
    blob.write_bytes(b"hi")
    with pytest.raises(CosignUnavailable):
        verify_blob(blob, "https://example.com/x.bin", policy)
