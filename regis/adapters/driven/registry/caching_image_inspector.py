"""CachingImageInspector — memoize read-only ImageInspector calls for one run.

Wraps a delegate ImageInspector and caches the four read methods by their
arguments, so the ~15 get_manifest call sites across analyzers (and oci.py's
double get_manifest per platform) hit the registry once per distinct reference.

Built once per analysis run and shared across analyzer threads.

THREAD-SAFETY: safe only over a *stateless* delegate. RegctlImageInspector (the
wired delegate) is stateless. The HTTP RegistryImageInspector shares a mutable
requests.Session/token and must NOT be placed behind this cache without first
making it thread-safe. The lock guards the memo dict; because it is held across
the delegate call, a duplicate in-flight fetch for the same key collapses to one.

Caching policy: successes only (exceptions propagate, never cached); no eviction
(one image touches a bounded set of refs); per-run scope (one instance per run).
Returned values are SHARED across callers, who MUST treat them as read-only.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

from regis.core.ports.image_inspector import ImageInspector

_Key = tuple[str, tuple[Any, ...]]


class CachingImageInspector(ImageInspector):
    """Per-run memoizing decorator over an ImageInspector."""

    def __init__(self, delegate: ImageInspector) -> None:
        self._delegate = delegate
        self._lock = threading.Lock()
        self._cache: dict[_Key, Any] = {}

    def _cached(
        self, method: str, args: tuple[Any, ...], compute: Callable[[], Any]
    ) -> Any:
        key = (method, args)
        with self._lock:
            if key in self._cache:
                return self._cache[key]
            value = compute()  # exception propagates here -> key never stored
            self._cache[key] = value
            return value

    def list_tags(self) -> list[str]:
        return self._cached("list_tags", (), self._delegate.list_tags)

    def get_manifest(self, reference: str) -> dict[str, Any]:
        return self._cached(
            "get_manifest",
            (reference,),
            lambda: self._delegate.get_manifest(reference),
        )

    def get_blob(self, digest: str) -> dict[str, Any]:
        return self._cached(
            "get_blob", (digest,), lambda: self._delegate.get_blob(digest)
        )

    def get_digest(self, reference: str) -> str | None:
        return self._cached(
            "get_digest", (reference,), lambda: self._delegate.get_digest(reference)
        )
