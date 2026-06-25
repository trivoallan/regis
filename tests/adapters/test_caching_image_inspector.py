"""Unit tests for CachingImageInspector (per-run registry memo)."""

from __future__ import annotations

import threading
import time
from typing import Any

import pytest

from regis.adapters.driven.registry.caching_image_inspector import (
    CachingImageInspector,
)
from regis.core.ports.image_inspector import ImageInspector


class _CountingInspector(ImageInspector):
    """Counts delegate calls; optional per-call delay to exercise overlap."""

    def __init__(self, *, delay: float = 0.0) -> None:
        self.calls: dict[str, int] = {
            "list_tags": 0,
            "get_manifest": 0,
            "get_blob": 0,
            "get_digest": 0,
        }
        self._delay = delay

    def list_tags(self) -> list[str]:
        self.calls["list_tags"] += 1
        return ["1.0", "latest"]

    def get_manifest(self, reference: str) -> dict[str, Any]:
        self.calls["get_manifest"] += 1
        if self._delay:
            time.sleep(self._delay)
        return {"ref": reference}

    def get_blob(self, digest: str) -> dict[str, Any]:
        self.calls["get_blob"] += 1
        return {"digest": digest}

    def get_digest(self, reference: str) -> str | None:
        self.calls["get_digest"] += 1
        return "sha256:abc"


def test_same_reference_fetched_once():
    delegate = _CountingInspector()
    cache = CachingImageInspector(delegate)
    first = cache.get_manifest("a")
    second = cache.get_manifest("a")
    assert delegate.calls["get_manifest"] == 1
    assert first == {"ref": "a"}
    assert second is first  # same object returned (shared, read-only invariant)


def test_distinct_references_each_hit_the_delegate():
    delegate = _CountingInspector()
    cache = CachingImageInspector(delegate)
    cache.get_manifest("a")
    cache.get_manifest("b")
    assert delegate.calls["get_manifest"] == 2


def test_all_four_methods_are_memoized():
    delegate = _CountingInspector()
    cache = CachingImageInspector(delegate)
    for _ in range(2):
        cache.list_tags()
        cache.get_manifest("ref")
        cache.get_blob("sha256:d")
        cache.get_digest("ref")
    assert delegate.calls == {
        "list_tags": 1,
        "get_manifest": 1,
        "get_blob": 1,
        "get_digest": 1,
    }


def test_exceptions_are_not_cached():
    class _RaiseThenOk(ImageInspector):
        def __init__(self) -> None:
            self.attempts = 0

        def list_tags(self) -> list[str]:
            return []

        def get_manifest(self, reference: str) -> dict[str, Any]:
            self.attempts += 1
            if self.attempts == 1:
                raise RuntimeError("transient")
            return {"ref": reference}

        def get_blob(self, digest: str) -> dict[str, Any]:
            return {}

        def get_digest(self, reference: str) -> str | None:
            return None

    delegate = _RaiseThenOk()
    cache = CachingImageInspector(delegate)
    with pytest.raises(RuntimeError):
        cache.get_manifest("a")
    # The failure was not cached: the retry reaches the delegate and succeeds.
    assert cache.get_manifest("a") == {"ref": "a"}
    assert delegate.attempts == 2


def test_concurrent_same_reference_fetches_once():
    delegate = _CountingInspector(delay=0.01)
    cache = CachingImageInspector(delegate)
    results: list[dict] = []

    def worker() -> None:
        results.append(cache.get_manifest("a"))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert delegate.calls["get_manifest"] == 1
    assert all(r == {"ref": "a"} for r in results)
