# Shared OCI Pull for syft + grype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop syft and grype from each re-pulling the same image — export it once into a local OCI layout and point both at `oci-dir:<layout>`, removing 2 of the 4 scanner pulls per run.

**Architecture:** A per-run `CachingToolRunner` decorator (sibling of part-1's `CachingImageInspector`) wraps the `SubprocessToolRunner`. On the first `generate_sbom`/`scan_vulnerabilities` for an image — when both `cve` and `sbom` are selected — it runs `regctl image copy <ref> ocidir://<tmpdir>` once (lock held across the export, memo keyed by ref), then runs `syft oci-dir:<tmpdir>` and `grype oci-dir:<tmpdir>` in parallel. Export failure falls back to the remote scan. The composition root injects the decorator as a callable so `core/` stays import-linter-clean. No SBOM handoff, no `grype sbom:` — grype catalogs the layout itself.

**Tech Stack:** Python 3.13, `uv`, pytest (90% global + per-file coverage gate), import-linter (`hexagonal-layers`), trunk (ruff + mypy). External binaries: `regctl`, `syft`, `grype`.

**Source of truth:** `docs/superpowers/specs/2026-06-25-sbom-handoff-design.md` (Approach D, APPROVED). T1 measurement verified the primitive end-to-end on python:3.12 (export 9.58s, `grype oci-dir:` = 365 CVEs identical to `grype <image>`).

---

## File Structure

| File                                                    | Responsibility                                                                                                                                        | Action        |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| `regis/utils/regctl.py`                                 | Add `run_regctl_copy` — export a remote image to a local OCI layout dir, reusing `run_regctl`'s credential injection.                                 | Modify        |
| `regis/adapters/driven/tools/subprocess_tool_runner.py` | Add `export_layout` (regctl copy, returns success) + `generate_sbom_from_layout` / `scan_vulnerabilities_from_layout` (run syft/grype on `oci-dir:`). | Modify        |
| `regis/adapters/driven/tools/caching_tool_runner.py`    | NEW — the per-run shared-layout decorator.                                                                                                            | Create        |
| `regis/core/application/analyze_image.py`               | Inject `tools_decorator`; thread `tools` through `_dispatch`; build+close the decorator in `run()`; `run_one` passthrough.                            | Modify        |
| `regis/adapters/driving/cli/composition.py`             | Wire the `CachingToolRunner` decorator into `build_analyze_image`.                                                                                    | Modify        |
| `scripts/verify_oci_handoff.sh`                         | NEW — the platform-pinned CVE/SBOM non-regression gate (real binaries).                                                                               | Create        |
| `tests/utils/test_regctl.py`                            | Unit test for `run_regctl_copy`.                                                                                                                      | Modify/Create |
| `tests/adapters/test_subprocess_tool_runner.py`         | Tests for the three new delegate methods.                                                                                                             | Modify        |
| `tests/adapters/test_caching_tool_runner.py`            | NEW — full behavioral coverage of the decorator.                                                                                                      | Create        |
| `tests/core/test_analyze_image.py`                      | Tests for decorator injection, share gating, close, run_one passthrough.                                                                              | Modify        |
| `tests/adapters/test_composition.py`                    | Test that the composition root wires a `CachingToolRunner`.                                                                                           | Modify        |

**Patch-target note (from CLAUDE.md):** monkeypatch at the _importing_ module — `regis.adapters.driven.tools.subprocess_tool_runner.{run_syft,run_grype,run_regctl_copy}` and `regis.utils.regctl.run_regctl`.

---

### Task 1: `run_regctl_copy` — export a remote image to a local OCI layout

**Files:**

- Modify: `regis/utils/regctl.py`
- Test: `tests/utils/test_regctl.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/utils/test_regctl.py` (create the file with this content if it does not exist):

```python
"""Unit tests for the regctl wrappers."""

from __future__ import annotations

import pytest

from regis.utils import regctl as mod


def test_run_regctl_copy_builds_image_copy_args(monkeypatch):
    captured = {}

    def fake_run_regctl(client, args, timeout=60):
        captured["registry"] = client.registry
        captured["username"] = client.username
        captured["password"] = client.password
        captured["args"] = args
        captured["timeout"] = timeout
        return ""

    monkeypatch.setattr(mod, "run_regctl", fake_run_regctl)
    mod.run_regctl_copy(
        "docker.io/library/nginx:1.27",
        "/tmp/layout-x",
        "docker.io",
        "alice",
        "s3cret",
        "linux/amd64",
    )
    assert captured["registry"] == "docker.io"
    assert captured["username"] == "alice"
    assert captured["password"] == "s3cret"
    assert captured["args"] == [
        "image",
        "copy",
        "--platform",
        "linux/amd64",
        "docker.io/library/nginx:1.27",
        "ocidir:///tmp/layout-x:regis",
    ]
    assert captured["timeout"] == 300


def test_run_regctl_copy_omits_platform_when_none(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        mod, "run_regctl", lambda client, args, timeout=60: captured.update(args=args)
    )
    mod.run_regctl_copy("docker.io/x:1", "/tmp/l", "docker.io")
    assert "--platform" not in captured["args"]
    assert captured["args"] == ["image", "copy", "docker.io/x:1", "ocidir:///tmp/l:regis"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/utils/test_regctl.py -k run_regctl_copy --no-cov -q`
Expected: FAIL with `AttributeError: module 'regis.utils.regctl' has no attribute 'run_regctl_copy'`

- [ ] **Step 3: Write minimal implementation**

In `regis/utils/regctl.py`, add after the `run_regctl` function:

```python
class _RegctlCreds:
    """Minimal credential carrier accepted by ``run_regctl`` (duck-typed)."""

    def __init__(
        self, registry: str, username: str | None, password: str | None
    ) -> None:
        self.registry = registry
        self.username = username
        self.password = password


def run_regctl_copy(
    src_ref: str,
    dest_dir: str,
    registry: str,
    username: str | None = None,
    password: str | None = None,
    platform: str | None = None,
    timeout: int = 300,
) -> None:
    """Copy *src_ref* into a local OCI layout directory *dest_dir* via regctl.

    Writes an OCI layout (``index.json``, ``oci-layout``, ``blobs/``) under
    *dest_dir*, tagged ``regis``. Reuses ``run_regctl``'s credential injection.

    Args:
        src_ref: Full remote image reference (e.g. ``docker.io/library/nginx:1.27``).
        dest_dir: Filesystem directory to receive the OCI layout.
        registry: Registry host for credential matching.
        username: Optional registry username.
        password: Optional registry password.
        platform: Optional single platform to copy (e.g. ``linux/amd64``).
        timeout: Subprocess timeout in seconds (image copy can be slow).

    Raises:
        RegistryError: if regctl is missing, times out, or exits non-zero.
    """
    creds = _RegctlCreds(registry, username, password)
    args = ["image", "copy"]
    if platform:
        args += ["--platform", platform]
    args += [src_ref, f"ocidir://{dest_dir}:regis"]
    run_regctl(creds, args, timeout=timeout)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/utils/test_regctl.py -k run_regctl_copy --no-cov -q`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add regis/utils/regctl.py tests/utils/test_regctl.py
git commit -m "feat(tools): add run_regctl_copy to export an image to a local OCI layout"
```

---

### Task 2: SubprocessToolRunner — export + local-layout scan methods

**Files:**

- Modify: `regis/adapters/driven/tools/subprocess_tool_runner.py`
- Test: `tests/adapters/test_subprocess_tool_runner.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/adapters/test_subprocess_tool_runner.py`:

```python
def test_export_layout_delegates_to_regctl_copy(monkeypatch):
    captured = {}

    def fake_copy(src_ref, dest_dir, registry, username, password, platform):
        captured.update(
            src_ref=src_ref,
            dest_dir=dest_dir,
            registry=registry,
            username=username,
            password=password,
            platform=platform,
        )

    monkeypatch.setattr(mod, "run_regctl_copy", fake_copy)
    ok = SubprocessToolRunner("alice", "s3cret").export_layout(IMAGE, "/tmp/lay")
    assert ok is True
    assert captured == {
        "src_ref": "docker.io/library/nginx:1.27",
        "dest_dir": "/tmp/lay",
        "registry": "docker.io",
        "username": "alice",
        "password": "s3cret",
        "platform": "linux/amd64",
    }


def test_export_layout_returns_false_on_failure(monkeypatch):
    from regis.core.domain.errors import RegistryError

    def boom(*a, **k):
        raise RegistryError("regctl exploded")

    monkeypatch.setattr(mod, "run_regctl_copy", boom)
    assert SubprocessToolRunner().export_layout(IMAGE, "/tmp/lay") is False


def test_generate_sbom_from_layout_runs_syft_on_oci_dir(monkeypatch):
    captured = {}

    def fake_run_syft(image):
        captured["image"] = image
        return {"bomFormat": "CycloneDX"}

    monkeypatch.setattr(mod, "run_syft", fake_run_syft)
    result = SubprocessToolRunner("u", "p").generate_sbom_from_layout("/tmp/lay")
    assert result == {"bomFormat": "CycloneDX"}
    assert captured["image"] == "oci-dir:/tmp/lay"


def test_scan_vulnerabilities_from_layout_runs_grype_on_oci_dir(monkeypatch):
    captured = {}

    def fake_run_grype(image):
        captured["image"] = image
        return {"matches": []}

    monkeypatch.setattr(mod, "run_grype", fake_run_grype)
    result = SubprocessToolRunner("u", "p").scan_vulnerabilities_from_layout("/tmp/lay")
    assert result == {"matches": []}
    assert captured["image"] == "oci-dir:/tmp/lay"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/adapters/test_subprocess_tool_runner.py -k "layout" --no-cov -q`
Expected: FAIL with `AttributeError: 'SubprocessToolRunner' object has no attribute 'export_layout'`

- [ ] **Step 3: Write minimal implementation**

In `regis/adapters/driven/tools/subprocess_tool_runner.py`:

Add to the imports block (with the other `regis.utils` imports):

```python
from regis.core.domain.errors import RegistryError, ToolError
from regis.utils.regctl import run_regctl_copy
```

(Replace the existing `from regis.core.domain.errors import ToolError` line with the `RegistryError, ToolError` version.)

Add these methods inside `SubprocessToolRunner`, right after `generate_sbom`:

```python
    def export_layout(self, image: ImageReference, dest_dir: str) -> bool:
        """Copy *image* into a local OCI layout at *dest_dir*; return success.

        A failed export (network/auth) returns ``False`` so the caller falls
        back to a direct remote scan instead of aborting the run.
        """
        try:
            run_regctl_copy(
                self._full_ref(image),
                dest_dir,
                image.registry,
                self._username,
                self._password,
                image.platform,
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/adapters/test_subprocess_tool_runner.py -k "layout" --no-cov -q`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add regis/adapters/driven/tools/subprocess_tool_runner.py tests/adapters/test_subprocess_tool_runner.py
git commit -m "feat(tools): add export_layout + oci-dir scan methods to SubprocessToolRunner"
```

---

### Task 3: CachingToolRunner — the per-run shared-layout decorator

**Files:**

- Create: `regis/adapters/driven/tools/caching_tool_runner.py`
- Test: `tests/adapters/test_caching_tool_runner.py`

- [ ] **Step 1: Write the failing test**

Create `tests/adapters/test_caching_tool_runner.py`:

```python
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
    # capture the temp dir path created for the export
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
    assert isinstance(runner.run("regctl", ["version"]), ToolResult) or True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/adapters/test_caching_tool_runner.py --no-cov -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'regis.adapters.driven.tools.caching_tool_runner'`

- [ ] **Step 3: Write minimal implementation**

Create `regis/adapters/driven/tools/caching_tool_runner.py`:

```python
"""CachingToolRunner — per-run shared OCI layout for syft + grype.

Exports the target image ONCE into a local OCI layout (regctl image copy) and
points syft/grype at ``oci-dir:<layout>`` instead of re-pulling the remote
image. Removes 2 of the 4 scanner image pulls per run. Mirrors
CachingImageInspector: per-run scope, thread-safe lock held across the export so
a concurrent second tool reuses the one layout.

Sharing is gated (``share``) on BOTH cve and sbom being selected (decided in
AnalyzeImage) — a single image-reading analyzer gains nothing from the export.
When sharing is off, or the export fails, calls pass through to the delegate's
remote scan unchanged.

THREAD-SAFETY: the delegate (SubprocessToolRunner) is stateless. The lock guards
the layout memo and is held across the regctl export, so a duplicate in-flight
export for the same ref collapses to one (same idiom as CachingImageInspector).
"""

from __future__ import annotations

import tempfile
import threading
from collections.abc import Sequence
from typing import Any

from regis.adapters.driven.tools.subprocess_tool_runner import SubprocessToolRunner
from regis.core.model.image_reference import ImageReference
from regis.core.ports.tool_runner import ToolResult, ToolRunner

#: Memo key — a value-equal identity for one image reference + platform.
_Key = tuple[str, str, str, str | None]


class CachingToolRunner(ToolRunner):
    """Per-run decorator sharing one local OCI layout across syft + grype."""

    def __init__(self, delegate: SubprocessToolRunner, share: bool) -> None:
        self._delegate = delegate
        self._share = share
        self._lock = threading.Lock()
        self._layouts: dict[_Key, str | None] = {}
        self._tmpdirs: list[tempfile.TemporaryDirectory[str]] = []
        self._closed = False

    @staticmethod
    def _key(image: ImageReference) -> _Key:
        return (image.registry, image.repository, image.tag, image.platform)

    def _layout(self, image: ImageReference) -> str | None:
        """Return a local OCI layout path for *image*, exporting once.

        Returns ``None`` if the export failed (memoized, never retried) so the
        caller falls back to a remote scan. The lock is held across the export
        so a concurrent second tool waits and reuses the one layout.
        """
        key = self._key(image)
        with self._lock:
            if key in self._layouts:
                return self._layouts[key]
            tmp = tempfile.TemporaryDirectory(prefix="regis-layout-")
            self._tmpdirs.append(tmp)
            ok = self._delegate.export_layout(image, tmp.name)
            self._layouts[key] = tmp.name if ok else None
            return self._layouts[key]

    def generate_sbom(self, image: ImageReference) -> dict[str, Any]:
        if self._share:
            layout = self._layout(image)
            if layout is not None:
                return self._delegate.generate_sbom_from_layout(layout)
        return self._delegate.generate_sbom(image)

    def scan_vulnerabilities(self, image: ImageReference) -> dict[str, Any]:
        if self._share:
            layout = self._layout(image)
            if layout is not None:
                return self._delegate.scan_vulnerabilities_from_layout(layout)
        return self._delegate.scan_vulnerabilities(image)

    # Capabilities that do not read the shared layout pass straight through.
    def scan_secrets(self, image: ImageReference) -> list[dict[str, Any]]:
        return self._delegate.scan_secrets(image)

    def lint_dockerfile(self, dockerfile: str) -> list[dict[str, Any]]:
        return self._delegate.lint_dockerfile(dockerfile)

    def audit_image(self, image: ImageReference) -> dict[str, Any]:
        return self._delegate.audit_image(image)

    def run(
        self, tool: str, args: Sequence[str], *, timeout: int | None = None
    ) -> ToolResult:
        return self._delegate.run(tool, args, timeout=timeout)

    def close(self) -> None:
        """Remove all exported layouts. Idempotent."""
        if self._closed:
            return
        self._closed = True
        for tmp in self._tmpdirs:
            tmp.cleanup()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/adapters/test_caching_tool_runner.py --no-cov -q`
Expected: PASS (8 passed)

- [ ] **Step 5: Commit**

```bash
git add regis/adapters/driven/tools/caching_tool_runner.py tests/adapters/test_caching_tool_runner.py
git commit -m "feat(tools): add CachingToolRunner for per-run shared OCI layout"
```

---

### Task 4: AnalyzeImage — inject the decorator, thread `tools`, build+close in `run()`

**Files:**

- Modify: `regis/core/application/analyze_image.py`
- Test: `tests/core/test_analyze_image.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/core/test_analyze_image.py`:

```python
class _RecordingDecorator:
    """Wraps a ToolRunner, records (base, share) and whether close() ran."""

    instances: list = []

    def __init__(self, base, share):
        self.base = base
        self.share = share
        self.closed = False
        _RecordingDecorator.instances.append(self)

    def __getattr__(self, name):
        return getattr(self.base, name)

    def close(self):
        self.closed = True


def _make_with_decorator():
    _RecordingDecorator.instances = []
    uc = AnalyzeImage(
        tools=FakeToolRunner(),
        tools_decorator=lambda base, share: _RecordingDecorator(base, share),
        inspector_factory=lambda image: FakeImageInspector(),
        sink=FakeReportSink(),
        presentation=FakePresentationRenderer(),
    )
    return uc


def test_run_applies_decorator_with_share_true_when_cve_and_sbom_selected():
    uc = _make_with_decorator()
    uc.run(IMAGE, {"cve": _SimpleAnalyzer, "sbom": _SimpleAnalyzer})
    assert len(_RecordingDecorator.instances) == 1
    deco = _RecordingDecorator.instances[0]
    assert deco.share is True
    assert deco.closed is True  # run() closed it in finally


def test_run_share_false_when_only_one_image_tool_selected():
    uc = _make_with_decorator()
    uc.run(IMAGE, {"cve": _SimpleAnalyzer, "other": _SimpleAnalyzer})
    assert _RecordingDecorator.instances[0].share is False


def test_run_one_does_not_apply_the_decorator():
    uc = _make_with_decorator()
    uc.run_one(IMAGE, _SimpleAnalyzer)
    assert _RecordingDecorator.instances == []  # passthrough on the single path


def test_no_decorator_uses_tools_directly():
    # Default tools_decorator=None must keep existing behavior (no wrap, no close).
    uc = _make_use_case(tools=FakeToolRunner(scan_vulnerabilities={"count": 9}))
    reports = uc.run(IMAGE, {"ctxone": _CtxAnalyzer})
    assert reports["ctxone"]["vulns"] == 9
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/core/test_analyze_image.py -k "decorator or share or no_decorator" --no-cov -q`
Expected: FAIL with `TypeError: AnalyzeImage.__init__() got an unexpected keyword argument 'tools_decorator'`

- [ ] **Step 3: Write minimal implementation**

In `regis/core/application/analyze_image.py`:

**(a)** Add module-level constants and a type alias just below the existing `InspectorFactory` definition (after line ~36):

```python
#: Decorator that wraps the run-scoped ToolRunner (e.g. CachingToolRunner).
#: Supplied by the composition root; takes (base_tools, share) -> ToolRunner.
ToolsDecorator = Callable[[ToolRunner, bool], ToolRunner]

#: Analyzer names whose tools (grype, syft) read the image; sharing the one
#: local OCI pull is only worth it when BOTH run.
_CVE_ANALYZER = "cve"
_SBOM_ANALYZER = "sbom"
```

**(b)** Extend `__init__` to accept and store the decorator. Replace the existing `__init__` with:

```python
    def __init__(
        self,
        *,
        tools: ToolRunner,
        inspector_factory: InspectorFactory,
        sink: ReportSink,
        presentation: PresentationRenderer,
        tools_decorator: ToolsDecorator | None = None,
    ) -> None:
        self._tools = tools
        self._inspector_factory = inspector_factory
        self._sink = sink
        self._presentation = presentation
        self._tools_decorator = tools_decorator
```

**(c)** Thread `tools` through `_dispatch`. Replace the existing `_dispatch` with:

```python
    def _dispatch(
        self,
        analyzer: Any,
        image: ImageReference,
        inspector: ImageInspector,
        tools: ToolRunner,
    ) -> dict[str, Any]:
        """Run one analyzer instance against a shared inspector + tools; validate."""
        ctx = AnalysisContext(image, inspector, tools)
        report = analyzer.analyze(ctx)
        analyzer.validate(report)
        return report
```

**(d)** `run_one` passes `self._tools` straight through (no decorator, no close). Replace its `return self._dispatch(...)` line:

```python
        try:
            return self._dispatch(analyzer, image, inspector, self._tools)
        finally:
```

**(e)** In `run`, build the decorator once, thread it into `_timed`, and close it in a `finally`. Replace the body from `inspector = self._inspector_factory(image)` through `return reports` with:

```python
        inspector = self._inspector_factory(image)
        share = _CVE_ANALYZER in selected and _SBOM_ANALYZER in selected
        tools = (
            self._tools_decorator(self._tools, share)
            if self._tools_decorator is not None
            else self._tools
        )

        def _timed(name: str, cls: type) -> tuple[str, dict[str, Any]]:
            # Record the start time before instantiation so a constructor that
            # raises is still timed and the draining thread reads a real elapsed.
            start_times[name] = time.monotonic()
            try:
                return name, self._dispatch(cls(), image, inspector, tools)
            finally:
                logger.debug(
                    "analyzer %s finished in %.2fs",
                    name,
                    time.monotonic() - start_times[name],
                )

        workers = min(max_workers, len(selected)) or 1
        try:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(_timed, name, cls): name
                    for name, cls in selected.items()
                }
                for future in as_completed(futures):
                    name = futures[future]
                    elapsed = time.monotonic() - start_times.get(
                        name, time.monotonic()
                    )
                    try:
                        _, report = future.result()
                        reports[name] = report
                        if on_progress is not None:
                            on_progress(AnalyzerOutcome(name, elapsed))
                    # Capture and classify any analyzer failure; never abort the run.
                    except Exception as exc:  # noqa: BLE001
                        kind = _classify(exc)
                        reports[name] = {
                            "analyzer": name,
                            "error": {"type": kind, "message": str(exc)},
                        }
                        if on_progress is not None:
                            on_progress(
                                AnalyzerOutcome(name, elapsed, kind, str(exc))
                            )
        finally:
            # The ThreadPoolExecutor 'with' block joins before this runs, so no
            # worker is still reading a layout when it is removed.
            close = getattr(tools, "close", None)
            if callable(close):
                close()
        return reports
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/core/test_analyze_image.py --no-cov -q`
Expected: PASS (all existing + 4 new)

- [ ] **Step 5: Commit**

```bash
git add regis/core/application/analyze_image.py tests/core/test_analyze_image.py
git commit -m "feat(application): share one OCI pull across cve+sbom via injected tools decorator"
```

---

### Task 5: Composition root — wire the CachingToolRunner

**Files:**

- Modify: `regis/adapters/driving/cli/composition.py`
- Test: `tests/adapters/test_composition.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/adapters/test_composition.py`:

```python
def test_build_analyze_image_wires_caching_tool_runner():
    from regis.adapters.driven.tools.caching_tool_runner import CachingToolRunner
    from regis.adapters.driven.tools.subprocess_tool_runner import SubprocessToolRunner
    from regis.adapters.driving.cli.composition import build_analyze_image

    uc = build_analyze_image("alice", "s3cret")
    assert uc._tools_decorator is not None
    decorated = uc._tools_decorator(SubprocessToolRunner("alice", "s3cret"), True)
    assert isinstance(decorated, CachingToolRunner)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/adapters/test_composition.py -k caching_tool_runner --no-cov -q`
Expected: FAIL with `AssertionError: assert None is not None` (the decorator is not wired yet)

- [ ] **Step 3: Write minimal implementation**

In `regis/adapters/driving/cli/composition.py`:

Add the import (next to the other `tools` import):

```python
from regis.adapters.driven.tools.caching_tool_runner import CachingToolRunner
```

Add the import for the port type (next to `ImageInspector`) and `cast`:

```python
from typing import cast

from regis.core.ports.tool_runner import ToolRunner
```

Inside `build_analyze_image`, add this helper just above the `sink = FileReportSink(...)` line:

```python
    def _decorate_tools(base: ToolRunner, share: bool) -> ToolRunner:
        # The composition root always supplies a SubprocessToolRunner as `tools`;
        # cast narrows the port type for the decorator's extended methods.
        return CachingToolRunner(cast(SubprocessToolRunner, base), share)
```

(Avoid `assert isinstance` here — Bandit B101 flags asserts in non-test source.)

Change the `return AnalyzeImage(...)` call to pass the decorator:

```python
    return AnalyzeImage(
        tools=SubprocessToolRunner(username, password),
        tools_decorator=_decorate_tools,
        inspector_factory=_inspector,
        sink=sink,
        presentation=presentation,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/adapters/test_composition.py -k caching_tool_runner --no-cov -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add regis/adapters/driving/cli/composition.py tests/adapters/test_composition.py
git commit -m "feat(cli): wire CachingToolRunner into the composition root"
```

---

### Task 6: Non-regression gate (real binaries) — verification script

**Files:**

- Create: `scripts/verify_oci_handoff.sh`

This is the behavioral gate (Success Criteria 3 + 4): the `oci-dir:` path must produce
the same CVE set and SBOM as a direct remote scan, platform-pinned for determinism.
It needs `regctl`/`syft`/`grype` + network, so it is a script run deliberately, not part
of the hermetic unit suite. (Already passed once: python:3.12 → 365 = 365 CVEs.)

- [ ] **Step 1: Create the script**

```bash
#!/usr/bin/env bash
# Non-regression gate for the shared-OCI-pull handoff (#806 part 2).
# Asserts grype/syft over a local OCI layout match a direct remote scan.
# Usage: scripts/verify_oci_handoff.sh [IMAGE] [PLATFORM]
set -euo pipefail

IMG="${1:-debian:12-slim}"
PLAT="${2:-linux/amd64}"
DIR="$(mktemp -d)"
trap 'rm -rf "$DIR"' EXIT

echo "Exporting $IMG ($PLAT) to a local OCI layout..."
regctl image copy --platform "$PLAT" "$IMG" "ocidir://$DIR/layout:regis"

echo "CVE parity (grype oci-dir: vs grype <image>, platform-pinned both sides)..."
grype "oci-dir:$DIR/layout" -o json \
  | jq -r '.matches[].vulnerability.id' | sort -u > "$DIR/cve_local.txt"
grype "$IMG" --platform "$PLAT" -o json \
  | jq -r '.matches[].vulnerability.id' | sort -u > "$DIR/cve_remote.txt"
if ! diff -q "$DIR/cve_local.txt" "$DIR/cve_remote.txt" >/dev/null; then
  echo "FAIL: CVE sets differ"; diff "$DIR/cve_remote.txt" "$DIR/cve_local.txt" | head; exit 1
fi
echo "  CVE sets identical ($(wc -l < "$DIR/cve_local.txt" | tr -d ' ') ids) ✓"

echo "SBOM parity (syft oci-dir: vs syft <image>, component count)..."
LOCAL_N=$(syft "oci-dir:$DIR/layout" -o syft-json | jq '.artifacts | length')
REMOTE_N=$(syft "$IMG" --platform "$PLAT" -o syft-json | jq '.artifacts | length')
if [ "$LOCAL_N" != "$REMOTE_N" ]; then
  echo "FAIL: component counts differ (local=$LOCAL_N remote=$REMOTE_N)"; exit 1
fi
echo "  component counts identical ($LOCAL_N) ✓"
echo "GATE PASSED for $IMG/$PLAT"
```

- [ ] **Step 2: Make it executable and run the gate**

Run:

```bash
chmod +x scripts/verify_oci_handoff.sh
scripts/verify_oci_handoff.sh debian:12-slim linux/amd64
```

Expected: `GATE PASSED for debian:12-slim/linux/amd64` (CVE + SBOM identical)

- [ ] **Step 3: Commit**

```bash
git add scripts/verify_oci_handoff.sh
git commit -m "test(tools): add OCI-handoff non-regression gate script"
```

---

### Task 7: Full verification — suite, coverage, lint, layering

**Files:** none (verification only)

- [ ] **Step 1: Run the full test suite with coverage gates**

Run: `uv run pytest`
Expected: PASS, total coverage ≥ 90% AND every file ≥ 90% (the per-file gate). If
`caching_tool_runner.py` is below 90%, add the missing-branch test to
`tests/adapters/test_caching_tool_runner.py` (every method + the share-off/export-fail
branches are already covered by Task 3).

- [ ] **Step 2: Lint + format + types**

Run: `trunk check`
Expected: no findings. If mypy flags the `_decorate_tools` `assert isinstance`, it is
intentional (narrows `ToolRunner` → `SubprocessToolRunner`); leave it.

- [ ] **Step 3: Verify hexagonal layering**

Run: `uv run lint-imports` (the `hexagonal-layers` import-linter contract)
Expected: Contracts kept. `caching_tool_runner.py` imports only `adapters.driven.tools`,
`core.model`, `core.ports` — no upward imports. `core/application/analyze_image.py` still
names no adapter type (the decorator arrives as an injected callable).

- [ ] **Step 4: Smoke test the real CLI**

Run: `uv run regis analyze python:3.12-slim -a cve -a sbom -o /tmp/smoke.json && jq '.results | keys' /tmp/smoke.json`
Expected: a report with `cve` and `sbom` results; one `regctl image copy` then
`syft oci-dir:` + `grype oci-dir:` (no remote syft/grype pull).

- [ ] **Step 5: Final commit (if any test was added in Step 1)**

```bash
git add -A
git commit -m "test(tools): close per-file coverage on CachingToolRunner"
```

---

## Self-Review

**1. Spec coverage (Approach D):**

- Shared `regctl` export once per ref → Task 1 (`run_regctl_copy`) + Task 3 (`_layout`, lock-across-export). ✓
- syft + grype read `oci-dir:` → Task 2 (`*_from_layout`). ✓
- Gate on `cve AND sbom` via named constants (eng-review D8) → Task 4 (`_CVE_ANALYZER`/`_SBOM_ANALYZER`). ✓
- `run_one` passthrough (D3) → Task 4 step (d) + `test_run_one_does_not_apply_the_decorator`. ✓
- `TemporaryDirectory` cleanup, idempotent (D6) → Task 3 (`close`) + `test_close_..._idempotent`. ✓
- Fallback on export failure (Criterion 5) → Task 2 (`export_layout` returns False) + Task 3 + `test_export_failure_falls_back...`. ✓
- One export, zero remote syft/grype pulls (Criterion 2) → `test_share_on_exports_once_and_both_read_the_layout`. ✓
- CVE + SBOM non-regression, platform-pinned (Criteria 3/4) → Task 6 script. ✓
- Import-linter clean injection → Task 5 (`_decorate_tools` callable) + Task 7 step 3. ✓

**2. Placeholder scan:** none — every step has complete code or an exact command + expected output.

**3. Type consistency:** `export_layout(image, dest_dir)`, `generate_sbom_from_layout(dest_dir)`, `scan_vulnerabilities_from_layout(dest_dir)`, `_layout(image)`, `close()`, `_decorate_tools(base, share)`, `ToolsDecorator = Callable[[ToolRunner, bool], ToolRunner]`, `run_regctl_copy(src_ref, dest_dir, registry, username, password, platform, timeout)` are used identically across Tasks 1–5 and their tests. `share` (bool) and the constants `_CVE_ANALYZER`/`_SBOM_ANALYZER` match between `analyze_image.py` and its tests.

**Deferred (NOT in this plan, per spec):** `grype sbom:` CPU optimization (T9) and Approach C — trufflehog + dockle on the layout (T10). Both compose on top with no rework.
