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


def test_concurrent_ensure_downloads_only_once(monkeypatch, tmp_path):
    import concurrent.futures
    import threading

    payload = b"x" * 1024
    sha = hashlib.sha256(payload).hexdigest()
    pub = tmp_path / "pub"
    pub.mkdir()
    (pub / "tool.bin").write_bytes(payload)

    serve_count = {"n": 0}
    lock = threading.Lock()

    class CountingHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            with lock:
                serve_count["n"] += 1
            super().do_GET()

    def handler(*a, **kw):
        return CountingHandler(*a, directory=str(pub), **kw)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"

    try:
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

        def worker(_):
            f = ToolFetcher(cache_dir=cache, arch="amd64")
            return f.ensure("grype")

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            paths = list(pool.map(worker, range(4)))

        assert all(p == paths[0] for p in paths)
        assert paths[0].read_bytes() == payload
        # Concurrent first-run: only one fetch should hit the network.
        assert serve_count["n"] == 1
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_mirror_overrides_manifest_url(monkeypatch, tmp_path):
    payload = b"mirror-payload"
    sha = hashlib.sha256(payload).hexdigest()
    pub = tmp_path / "mirror"
    pub.mkdir()
    # Mirror layout: {mirror}/{tool}/{version}/{tool}_{version}_linux_{arch}{ext}
    target_dir = pub / "grype" / "0.0.1"
    target_dir.mkdir(parents=True)
    (target_dir / "grype_0.0.1_linux_amd64").write_bytes(payload)

    with _serve(pub) as base_url:
        from regis.tools.manifest import Tool

        tools = {
            "grype": Tool(
                name="grype",
                version="0.0.1",
                url_template="https://example.invalid/will-not-be-hit",
                archive="none",
                sha256={"amd64": sha, "arm64": sha},
            )
        }
        _patch_manifest(monkeypatch, tools)
        cache = tmp_path / "cache"
        fetcher = ToolFetcher(cache_dir=cache, mirror=base_url, arch="amd64")
        path = fetcher.ensure("grype")
        assert path.read_bytes() == payload


def test_mirror_env_var_is_picked_up(monkeypatch, tmp_path):
    monkeypatch.setenv("REGIS_TOOLS_MIRROR", "https://nope.invalid")
    from regis.tools.manifest import Tool

    tools = {
        "grype": Tool(
            name="grype",
            version="0.0.1",
            url_template="https://orig.invalid",
            archive="none",
            sha256={"amd64": "a" * 64, "arm64": "b" * 64},
        )
    }
    _patch_manifest(monkeypatch, tools)
    fetcher = ToolFetcher(cache_dir=tmp_path / "cache", arch="amd64")
    assert fetcher.mirror == "https://nope.invalid"


def test_cosign_required_but_missing_raises(monkeypatch, tmp_path):
    payload = b"x"
    sha = hashlib.sha256(payload).hexdigest()
    pub = tmp_path / "pub"
    pub.mkdir()
    (pub / "tool.bin").write_bytes(payload)
    with _serve(pub) as base_url:
        from regis.tools.manifest import CosignPolicy, Tool

        tools = {
            "grype": Tool(
                name="grype",
                version="0.0.1",
                url_template=f"{base_url}/tool.bin",
                archive="none",
                sha256={"amd64": sha, "arm64": sha},
                cosign=CosignPolicy(issuer="https://x", identity_regex=".*"),
            )
        }
        _patch_manifest(monkeypatch, tools)
        monkeypatch.setenv("REGIS_REQUIRE_COSIGN", "1")
        monkeypatch.setattr("regis.tools.cosign.shutil.which", lambda _: None)
        fetcher = ToolFetcher(cache_dir=tmp_path / "cache", arch="amd64")
        with pytest.raises(ToolFetchError, match="cosign required but unavailable"):
            fetcher.ensure("grype")


def test_cosign_missing_is_silently_skipped_by_default(monkeypatch, tmp_path, caplog):
    payload = b"x"
    sha = hashlib.sha256(payload).hexdigest()
    pub = tmp_path / "pub"
    pub.mkdir()
    (pub / "tool.bin").write_bytes(payload)
    with _serve(pub) as base_url:
        from regis.tools.manifest import CosignPolicy, Tool

        tools = {
            "grype": Tool(
                name="grype",
                version="0.0.1",
                url_template=f"{base_url}/tool.bin",
                archive="none",
                sha256={"amd64": sha, "arm64": sha},
                cosign=CosignPolicy(issuer="https://x", identity_regex=".*"),
            )
        }
        _patch_manifest(monkeypatch, tools)
        monkeypatch.delenv("REGIS_REQUIRE_COSIGN", raising=False)
        monkeypatch.setattr("regis.tools.cosign.shutil.which", lambda _: None)
        fetcher = ToolFetcher(cache_dir=tmp_path / "cache", arch="amd64")
        with caplog.at_level("INFO"):
            fetcher.ensure("grype")
        assert any("cosign verification skipped" in r.message for r in caplog.records)


def test_fetch_all_downloads_each_tool(monkeypatch, tmp_path):
    payloads = {n: f"bin-{n}".encode() for n in ("grype", "syft")}
    shas = {n: hashlib.sha256(p).hexdigest() for n, p in payloads.items()}
    pub = tmp_path / "pub"
    pub.mkdir()
    for n, p in payloads.items():
        (pub / f"{n}.bin").write_bytes(p)
    with _serve(pub) as base_url:
        from regis.tools.manifest import Tool

        tools = {
            n: Tool(
                name=n,
                version="0.0.1",
                url_template=f"{base_url}/{n}.bin",
                archive="none",
                sha256={"amd64": shas[n], "arm64": shas[n]},
            )
            for n in ("grype", "syft")
        }
        _patch_manifest(monkeypatch, tools)
        fetcher = ToolFetcher(cache_dir=tmp_path / "cache", arch="amd64")
        result = fetcher.fetch_all()
        assert set(result) == {"grype", "syft"}
        assert all(result[n].read_bytes() == payloads[n] for n in payloads)


def test_fetch_all_subset(monkeypatch, tmp_path):
    payload = b"only-grype"
    sha = hashlib.sha256(payload).hexdigest()
    pub = tmp_path / "pub"
    pub.mkdir()
    (pub / "grype.bin").write_bytes(payload)
    with _serve(pub) as base_url:
        from regis.tools.manifest import Tool

        tools = {
            "grype": Tool(
                name="grype",
                version="0.0.1",
                url_template=f"{base_url}/grype.bin",
                archive="none",
                sha256={"amd64": sha, "arm64": sha},
            ),
            "syft": Tool(
                name="syft",
                version="0.0.1",
                url_template="https://offline.invalid",
                archive="none",
                sha256={"amd64": "0" * 64, "arm64": "0" * 64},
            ),
        }
        _patch_manifest(monkeypatch, tools)
        fetcher = ToolFetcher(cache_dir=tmp_path / "cache", arch="amd64")
        result = fetcher.fetch_all(names=["grype"])
        assert list(result) == ["grype"]
