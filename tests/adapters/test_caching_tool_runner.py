"""Unit tests for CachingToolRunner (per-run shared OCI layout for syft+grype)."""

from __future__ import annotations

import threading
import time

from regis.adapters.driven.tools.caching_tool_runner import CachingToolRunner
from regis.adapters.driven.tools.subprocess_tool_runner import SubprocessToolRunner
from regis.core.model.image_reference import ImageReference
from regis.core.ports.tool_runner import ToolResult, ToolRunner

IMAGE = ImageReference(
    registry="docker.io", repository="library/nginx", tag="1.27", platform="linux/amd64"
)
OTHER = ImageReference(
    registry="docker.io", repository="library/redis", tag="7", platform="linux/amd64"
)


class _FakeDelegate(SubprocessToolRunner):
    """Counts calls and routes by path; never touches a real subprocess."""

    def __init__(self, *, export_ok: bool = True, delay: float = 0.0) -> None:
        super().__init__()
        self._export_ok = export_ok
        self._delay = delay
        self.calls = {
            "export": 0,
            "sbom_remote": 0,
            "sbom_layout": 0,
            "cve_remote": 0,
            "cve_layout": 0,
            "secrets": 0,
        }

    def export_layout(self, image, dest_dir):
        self.calls["export"] += 1
        if self._delay:
            time.sleep(self._delay)
        return self._export_ok

    def generate_sbom(self, image):
        self.calls["sbom_remote"] += 1
        return {"src": "remote-sbom"}

    def generate_sbom_from_layout(self, dest_dir):
        self.calls["sbom_layout"] += 1
        return {"src": "layout-sbom"}

    def scan_vulnerabilities(self, image):
        self.calls["cve_remote"] += 1
        return {"src": "remote-cve"}

    def scan_vulnerabilities_from_layout(self, dest_dir):
        self.calls["cve_layout"] += 1
        return {"src": "layout-cve"}

    def scan_secrets(self, image):
        self.calls["secrets"] += 1
        return [{"x": 1}]


def test_is_a_tool_runner():
    assert isinstance(CachingToolRunner(_FakeDelegate(), share=True), ToolRunner)


def test_share_on_exports_once_and_both_read_the_layout():
    delegate = _FakeDelegate()
    runner = CachingToolRunner(delegate, share=True)
    assert runner.generate_sbom(IMAGE) == {"src": "layout-sbom"}
    assert runner.scan_vulnerabilities(IMAGE) == {"src": "layout-cve"}
    assert delegate.calls["export"] == 1  # one export for the pair
    assert delegate.calls["sbom_layout"] == 1
    assert delegate.calls["cve_layout"] == 1
    assert delegate.calls["sbom_remote"] == 0
    assert delegate.calls["cve_remote"] == 0


def test_share_off_passes_through_to_remote():
    delegate = _FakeDelegate()
    runner = CachingToolRunner(delegate, share=False)
    runner.generate_sbom(IMAGE)
    runner.scan_vulnerabilities(IMAGE)
    assert delegate.calls["export"] == 0
    assert delegate.calls["sbom_remote"] == 1
    assert delegate.calls["cve_remote"] == 1


def test_export_failure_falls_back_to_remote_and_is_not_retried():
    delegate = _FakeDelegate(export_ok=False)
    runner = CachingToolRunner(delegate, share=True)
    assert runner.generate_sbom(IMAGE) == {"src": "remote-sbom"}
    assert runner.scan_vulnerabilities(IMAGE) == {"src": "remote-cve"}
    assert delegate.calls["export"] == 1  # failure memoized, not retried
    assert delegate.calls["sbom_remote"] == 1
    assert delegate.calls["cve_remote"] == 1


def test_distinct_refs_export_each():
    delegate = _FakeDelegate()
    runner = CachingToolRunner(delegate, share=True)
    runner.generate_sbom(IMAGE)
    runner.generate_sbom(OTHER)
    assert delegate.calls["export"] == 2


def test_concurrent_same_ref_exports_once():
    delegate = _FakeDelegate(delay=0.02)
    runner = CachingToolRunner(delegate, share=True)

    def gen():
        runner.generate_sbom(IMAGE)

    def scan():
        runner.scan_vulnerabilities(IMAGE)

    threads = [threading.Thread(target=gen) for _ in range(4)] + [
        threading.Thread(target=scan) for _ in range(4)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert delegate.calls["export"] == 1


def test_close_removes_layouts_and_is_idempotent():
    import os

    delegate = _FakeDelegate()
    runner = CachingToolRunner(delegate, share=True)
    runner.generate_sbom(IMAGE)
    (path,) = [p for p in runner._layouts.values() if p is not None]
    assert os.path.isdir(path)
    runner.close()
    assert not os.path.isdir(path)
    runner.close()  # second call must not raise


def test_non_shared_methods_pass_through():
    delegate = _FakeDelegate()
    runner = CachingToolRunner(delegate, share=True)
    assert runner.scan_secrets(IMAGE) == [{"x": 1}]
    assert delegate.calls["secrets"] == 1
