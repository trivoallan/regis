from __future__ import annotations

import shutil

import click
import pytest


def test_ensure_tool_returns_path_when_on_path(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _n: "/usr/local/bin/grype")
    from regis.utils.process import ensure_tool
    assert ensure_tool("grype") == "/usr/local/bin/grype"


def test_ensure_tool_delegates_to_fetcher_when_in_manifest(monkeypatch, tmp_path):
    monkeypatch.setattr(shutil, "which", lambda _n: None)
    calls = {}

    class FakeFetcher:
        def __init__(self): pass
        def ensure(self, name): calls["name"] = name; return tmp_path / name

    from regis.utils import process as proc
    monkeypatch.setattr(proc, "_default_fetcher", lambda: FakeFetcher())
    monkeypatch.setattr(proc, "_in_manifest", lambda n: True)

    assert proc.ensure_tool("grype") == str(tmp_path / "grype")
    assert calls["name"] == "grype"


def test_ensure_tool_unknown_tool_raises_click_exception(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _n: None)
    from regis.utils import process as proc
    monkeypatch.setattr(proc, "_in_manifest", lambda n: False)
    with pytest.raises(click.ClickException, match="not found"):
        proc.ensure_tool("zorglub")
