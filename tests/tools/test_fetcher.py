from __future__ import annotations

import hashlib
import http.server
import os
import threading
from contextlib import contextmanager
from pathlib import Path

import pytest

from regis.tools.fetcher import ToolFetcher, ToolFetchError


def _write_binary(path: Path, content: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    os.chmod(path, 0o755)
    return hashlib.sha256(content).hexdigest()


def _patch_manifest(monkeypatch, tools: dict) -> None:
    """Replace the loader with a controlled in-memory manifest."""
    from regis.tools import manifest as m

    monkeypatch.setattr(m, "load_manifest", lambda path=None: tools)


@pytest.fixture
def fake_tool(monkeypatch, tmp_path):
    """A manifest with a single 'grype' entry whose sha matches a tiny payload."""
    payload = b"hello-grype"
    sha = hashlib.sha256(payload).hexdigest()
    from regis.tools.manifest import Tool

    tools = {
        "grype": Tool(
            name="grype",
            version="0.0.1",
            url_template="https://example.invalid/grype",
            archive="none",
            sha256={"amd64": sha, "arm64": sha},
        )
    }
    _patch_manifest(monkeypatch, tools)
    return payload, sha, tmp_path


def test_ensure_returns_cached_path_when_present(fake_tool) -> None:
    payload, sha, cache = fake_tool
    binpath = cache / "grype" / "0.0.1" / "linux-amd64" / "grype"
    _write_binary(binpath, payload)

    fetcher = ToolFetcher(cache_dir=cache, arch="amd64", offline=True)
    assert fetcher.ensure("grype") == binpath


def test_ensure_raises_when_offline_and_missing(fake_tool) -> None:
    _, _, cache = fake_tool
    fetcher = ToolFetcher(cache_dir=cache, arch="amd64", offline=True)
    with pytest.raises(ToolFetchError, match="offline"):
        fetcher.ensure("grype")


def test_status_lists_each_tool(fake_tool) -> None:
    payload, _, cache = fake_tool
    binpath = cache / "grype" / "0.0.1" / "linux-amd64" / "grype"
    _write_binary(binpath, payload)

    fetcher = ToolFetcher(cache_dir=cache, arch="amd64", offline=True)
    statuses = fetcher.status()
    assert len(statuses) == 1
    assert statuses[0].name == "grype"
    assert statuses[0].cached is True
    assert statuses[0].path == binpath
    assert statuses[0].sha256_ok is True


def test_unknown_tool_raises_value_error(fake_tool) -> None:
    _, _, cache = fake_tool
    fetcher = ToolFetcher(cache_dir=cache, arch="amd64", offline=True)
    with pytest.raises(KeyError):
        fetcher.ensure("nope")


@contextmanager
def _serve(directory: Path, port: int = 0):
    def handler(*a, **kw):
        return http.server.SimpleHTTPRequestHandler(*a, directory=str(directory), **kw)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_ensure_downloads_when_missing(monkeypatch, tmp_path):
    payload = b"binary-bytes"
    sha = hashlib.sha256(payload).hexdigest()
    pub = tmp_path / "pub"
    pub.mkdir()
    (pub / "tool.bin").write_bytes(payload)

    with _serve(pub) as base_url:
        from regis.tools.manifest import Tool

        tools = {
            "grype": Tool(
                name="grype",
                version="0.0.1",
                url_template=f"{base_url}/tool.bin",
                archive="none",
                sha256={"amd64": sha, "arm64": sha},
            )
        }
        _patch_manifest(monkeypatch, tools)
        cache = tmp_path / "cache"
        fetcher = ToolFetcher(cache_dir=cache, arch="amd64")

        path = fetcher.ensure("grype")
        assert path.read_bytes() == payload
        assert os.access(path, os.X_OK)


def test_sha256_mismatch_raises_and_cleans_partial(monkeypatch, tmp_path):
    payload = b"binary-bytes"
    wrong_sha = "0" * 64
    pub = tmp_path / "pub"
    pub.mkdir()
    (pub / "tool.bin").write_bytes(payload)

    with _serve(pub) as base_url:
        from regis.tools.manifest import Tool

        tools = {
            "grype": Tool(
                name="grype",
                version="0.0.1",
                url_template=f"{base_url}/tool.bin",
                archive="none",
                sha256={"amd64": wrong_sha, "arm64": wrong_sha},
            )
        }
        _patch_manifest(monkeypatch, tools)
        cache = tmp_path / "cache"
        fetcher = ToolFetcher(cache_dir=cache, arch="amd64")

        with pytest.raises(ToolFetchError, match="sha256"):
            fetcher.ensure("grype")
        partial_dir = cache / "grype" / "0.0.1" / "linux-amd64"
        # No final file, no leftover partials
        if partial_dir.exists():
            for f in partial_dir.iterdir():
                assert not f.name.startswith("grype.partial")
            assert not (partial_dir / "grype").exists()


def test_archive_targz_extracts_member(monkeypatch, tmp_path):
    import tarfile

    payload = b"#!/bin/sh\necho hi\n"
    sha = hashlib.sha256(payload).hexdigest()
    pub = tmp_path / "pub"
    pub.mkdir()
    bin_path = tmp_path / "grype"
    bin_path.write_bytes(payload)
    with tarfile.open(pub / "grype.tar.gz", "w:gz") as tar:
        tar.add(bin_path, arcname="grype")

    with _serve(pub) as base_url:
        from regis.tools.manifest import Tool

        tools = {
            "grype": Tool(
                name="grype",
                version="0.0.1",
                url_template=f"{base_url}/grype.tar.gz",
                archive="tar.gz",
                member="grype",
                sha256={"amd64": sha, "arm64": sha},
            )
        }
        _patch_manifest(monkeypatch, tools)
        cache = tmp_path / "cache"
        fetcher = ToolFetcher(cache_dir=cache, arch="amd64")

        path = fetcher.ensure("grype")
        assert path.read_bytes() == payload
