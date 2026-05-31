# Image-size reduction round 3 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a slim default Docker image (<150 MB amd64) by lazy-loading scanner binaries (grype, syft, trufflehog, hadolint, dockle) on first use, and a `-full` variant that bakes everything for air-gapped use; switch runtime base to `gcr.io/distroless/python3-debian12:nonroot`.

**Architecture:** New `regis.tools` package with a manifest (`regis/tools/manifest.yaml`) listing version + URL + sha256 + optional cosign per tool, plus a `ToolFetcher` that resolves a tool's local cache path (download + verify if absent). A thin `ensure_tool()` wrapper in `regis/utils/process.py` plugs into existing analyzer code: when the binary is already on PATH (dev host, `-full` image), it short-circuits; otherwise it delegates to the fetcher. The Dockerfile becomes two-variant via `--build-arg VARIANT=slim|full` selecting between `final-slim` (only regctl baked) and `final-full` (all binaries baked). CI matrix-builds both, enforces per-variant size ceilings, and a new manifest-validation workflow re-verifies sha256s weekly.

**Tech Stack:** Python 3.10+ (urllib + hashlib + fcntl, no new deps for fetcher), PyYAML (already used), jsonschema (already used), Click (CLI), Docker Buildx multi-arch, GitHub Actions matrix, distroless Python 3.11, optional cosign binary.

**Spec:** [docs/superpowers/specs/2026-05-31-image-size-round-3-design.md](../../superpowers/specs/2026-05-31-image-size-round-3-design.md)

---

## File Structure

**New files:**

- `regis/tools/__init__.py` — package init, re-exports `ToolFetcher`, `ToolFetchError`, `load_manifest`
- `regis/tools/manifest.py` — manifest loader, typed view
- `regis/tools/manifest.yaml` — versions, URLs, sha256, cosign per tool
- `regis/tools/fetcher.py` — `ToolFetcher` class + helpers
- `regis/tools/cosign.py` — cosign verification helper (best-effort)
- `regis/schemas/tools-manifest.schema.json` — JSON Schema for the manifest
- `tests/tools/__init__.py`
- `tests/tools/test_manifest.py`
- `tests/tools/test_fetcher.py`
- `tests/tools/test_cosign.py`
- `tests/tools/test_ensure_tool.py`
- `.github/workflows/ci-tools-manifest.yml`
- `.github/workflows/ci-tools-fetch-smoke.yml`
- `docs/website/docs/usage/tools-management.md`

**Modified files:**

- `regis/utils/process.py` — add `ensure_tool()` helper
- `regis/utils/grype.py` — use `ensure_tool("grype")` instead of `shutil.which`
- `regis/utils/syft.py` — same
- `regis/utils/trufflehog.py` — same
- `regis/utils/regctl.py` — resolve path via `ensure_tool("regctl")` before invoking
- `regis/analyzers/hadolint.py` — same
- `regis/analyzers/dockle.py` — same
- `regis/commands/bootstrap.py` — new `tools` subgroup
- `regis/commands/doctor.py` — add Tools section reading from `ToolFetcher.status()`
- `pyproject.toml` — `[tool.setuptools.package-data]` include `regis/tools/manifest.yaml` and the new schema
- `Dockerfile` — two-variant build (slim/full), distroless runtime
- `.dockerignore` — verify nothing under `regis/tools/` is excluded
- `.github/workflows/cd-docker.yml` — matrix on variant, dual tags
- `.github/workflows/ci-image-size.yml` — matrix on variant, per-variant ceiling
- `renovate.json` (if present) or new `.github/renovate.json5` — custom regex manager for `manifest.yaml`
- `docs/website/docs/reference/cli.md` — document `bootstrap tools` + doctor Tools section
- `docs/website/docs/usage/configuration.md` — add 4 new env vars
- `README.md` — add "lazy by default" note + image variants table

---

## Task 0: POC — distroless venv compatibility smoke

**Why first:** the entire plan hinges on a venv compiled on `python:3.11-slim` Debian 12 being executable inside `gcr.io/distroless/python3-debian12`. Validate in <10 minutes before any other work.

**Files:**

- Create (throwaway): `Dockerfile.poc`
- No commit; delete after validation.

- [ ] **Step 1: Write throwaway Dockerfile**

```dockerfile
# Dockerfile.poc — throwaway, do not commit
FROM python:3.11-slim AS builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir click pyyaml jsonschema

FROM gcr.io/distroless/python3-debian12:nonroot
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENTRYPOINT ["python", "-c", "import click, yaml, jsonschema; print('OK', click.__version__)"]
```

- [ ] **Step 2: Build and run**

```bash
docker build -f Dockerfile.poc -t regis-poc .
docker run --rm regis-poc
```

Expected: prints `OK <click version>`. If it errors with `ImportError` for a `.so` (e.g. cffi, lxml), the cross-base venv assumption is wrong — STOP and revisit base choice (fallback option: build runtime stage on `python:3.11-slim` too, keep distroless out of scope for this round).

- [ ] **Step 3: Cleanup**

```bash
rm Dockerfile.poc
docker image rm regis-poc
```

- [ ] **Step 4: Record outcome in PR description**

No commit; the POC result gates the rest of the plan.

---

## Task 1: Tools manifest JSON Schema

**Files:**

- Create: `regis/schemas/tools-manifest.schema.json`
- Test: `tests/tools/test_manifest.py` (schema validation only, manifest loading in Task 3)

- [ ] **Step 1: Create the schema**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://regis.dev/schemas/tools-manifest.schema.json",
  "title": "Regis Tools Manifest",
  "type": "object",
  "required": ["schema_version", "tools"],
  "additionalProperties": false,
  "properties": {
    "schema_version": { "type": "integer", "const": 1 },
    "tools": {
      "type": "object",
      "minProperties": 1,
      "patternProperties": {
        "^[a-z][a-z0-9_-]*$": { "$ref": "#/$defs/tool" }
      },
      "additionalProperties": false
    }
  },
  "$defs": {
    "tool": {
      "type": "object",
      "required": ["version", "url_template", "archive", "sha256"],
      "additionalProperties": false,
      "properties": {
        "version": {
          "type": "string",
          "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"
        },
        "url_template": { "type": "string", "format": "uri-reference" },
        "archive": { "enum": ["none", "tar.gz", "zip"] },
        "member": { "type": "string" },
        "arch_alt": {
          "type": "object",
          "additionalProperties": { "type": "string" }
        },
        "cosign": {
          "oneOf": [
            { "type": "null" },
            {
              "type": "object",
              "required": ["issuer", "identity_regex"],
              "additionalProperties": false,
              "properties": {
                "issuer": { "type": "string", "format": "uri" },
                "identity_regex": { "type": "string" }
              }
            }
          ]
        },
        "sha256": {
          "type": "object",
          "required": ["amd64", "arm64"],
          "additionalProperties": false,
          "properties": {
            "amd64": { "type": "string", "pattern": "^[0-9a-f]{64}$" },
            "arm64": { "type": "string", "pattern": "^[0-9a-f]{64}$" }
          }
        }
      }
    }
  }
}
```

- [ ] **Step 2: Write the failing schema test**

```python
# tests/tools/test_manifest.py
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA_PATH = Path("regis/schemas/tools-manifest.schema.json")


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_schema_loads_and_is_draft_2020_12(schema: dict) -> None:
    assert schema["$schema"].endswith("/2020-12/schema")
    jsonschema.Draft202012Validator.check_schema(schema)


def test_minimal_valid_manifest(schema: dict) -> None:
    doc = {
        "schema_version": 1,
        "tools": {
            "grype": {
                "version": "0.112.0",
                "url_template": "https://example.com/{version}/{arch}",
                "archive": "tar.gz",
                "member": "grype",
                "sha256": {"amd64": "a" * 64, "arm64": "b" * 64},
            }
        },
    }
    jsonschema.validate(doc, schema)


def test_rejects_short_sha256(schema: dict) -> None:
    doc = {
        "schema_version": 1,
        "tools": {
            "grype": {
                "version": "0.1.0",
                "url_template": "https://x/{version}",
                "archive": "none",
                "sha256": {"amd64": "abc", "arm64": "b" * 64},
            }
        },
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(doc, schema)


def test_rejects_unknown_archive_type(schema: dict) -> None:
    doc = {
        "schema_version": 1,
        "tools": {
            "x": {
                "version": "0.1.0",
                "url_template": "u",
                "archive": "rar",
                "sha256": {"amd64": "a" * 64, "arm64": "b" * 64},
            }
        },
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(doc, schema)
```

- [ ] **Step 3: Run the tests**

```bash
pipenv run pytest tests/tools/test_manifest.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add regis/schemas/tools-manifest.schema.json tests/tools/__init__.py tests/tools/test_manifest.py
git commit -m "feat(tools): add JSON Schema for tool fetch manifest"
```

(Create the empty `tests/tools/__init__.py` if missing: `touch tests/tools/__init__.py`.)

---

## Task 2: Pin tool versions and compute sha256

**Files:**

- Create: `scripts/compute_tool_hashes.sh` (throwaway helper, kept in tree)
- Create: `regis/tools/manifest.yaml`

This task is **mechanical**: download each tool at the pinned version for amd64 and arm64, compute sha256, write the manifest.

- [ ] **Step 1: Write the helper script**

```bash
# scripts/compute_tool_hashes.sh
#!/usr/bin/env bash
set -euo pipefail

TOOLS=(
  "grype|0.112.0|https://github.com/anchore/grype/releases/download/v{version}/grype_{version}_linux_{arch}.tar.gz"
  "syft|1.44.0|https://github.com/anchore/syft/releases/download/v{version}/syft_{version}_linux_{arch}.tar.gz"
  "trufflehog|3.95.3|https://github.com/trufflesecurity/trufflehog/releases/download/v{version}/trufflehog_{version}_linux_{arch}.tar.gz"
  "regctl|0.11.5|https://github.com/regclient/regclient/releases/download/v{version}/regctl-linux-{arch}"
  "dockle|0.4.15|https://github.com/goodwithtech/dockle/releases/download/v{version}/dockle_{version}_Linux-{arch_alt}.tar.gz"
  "hadolint|2.12.0|https://github.com/hadolint/hadolint/releases/download/v{version}/hadolint-Linux-{arch_alt}"
)

for entry in "${TOOLS[@]}"; do
  IFS='|' read -r name version tpl <<<"$entry"
  for arch in amd64 arm64; do
    case "$name/$arch" in
      dockle/amd64) arch_alt=64bit ;;
      dockle/arm64) arch_alt=ARM64 ;;
      hadolint/amd64) arch_alt=x86_64 ;;
      hadolint/arm64) arch_alt=arm64 ;;
      *) arch_alt="$arch" ;;
    esac
    url="${tpl//\{version\}/$version}"
    url="${url//\{arch\}/$arch}"
    url="${url//\{arch_alt\}/$arch_alt}"
    sha=$(curl -sSfL "$url" | sha256sum | awk '{print $1}')
    echo "$name  $arch  $sha"
  done
done
```

- [ ] **Step 2: Run it and capture output**

```bash
chmod +x scripts/compute_tool_hashes.sh
./scripts/compute_tool_hashes.sh | tee /tmp/tool-hashes.txt
```

Expected: 12 lines (6 tools × 2 arches) with a hex sha256 per line. If any line errors, the URL is wrong or the release was retracted — fix the version pin before continuing.

- [ ] **Step 3: Write the manifest using captured hashes**

```yaml
# regis/tools/manifest.yaml
schema_version: 1
tools:
  grype:
    version: "0.112.0"
    url_template: "https://github.com/anchore/grype/releases/download/v{version}/grype_{version}_linux_{arch}.tar.gz"
    archive: tar.gz
    member: grype
    cosign:
      issuer: "https://token.actions.githubusercontent.com"
      identity_regex: "^https://github.com/anchore/grype/.+"
    sha256:
      amd64: "<paste from step 2>"
      arm64: "<paste from step 2>"

  syft:
    version: "1.44.0"
    url_template: "https://github.com/anchore/syft/releases/download/v{version}/syft_{version}_linux_{arch}.tar.gz"
    archive: tar.gz
    member: syft
    cosign:
      issuer: "https://token.actions.githubusercontent.com"
      identity_regex: "^https://github.com/anchore/syft/.+"
    sha256:
      amd64: "<paste>"
      arm64: "<paste>"

  trufflehog:
    version: "3.95.3"
    url_template: "https://github.com/trufflesecurity/trufflehog/releases/download/v{version}/trufflehog_{version}_linux_{arch}.tar.gz"
    archive: tar.gz
    member: trufflehog
    cosign:
      issuer: "https://token.actions.githubusercontent.com"
      identity_regex: "^https://github.com/trufflesecurity/trufflehog/.+"
    sha256:
      amd64: "<paste>"
      arm64: "<paste>"

  regctl:
    version: "0.11.5"
    url_template: "https://github.com/regclient/regclient/releases/download/v{version}/regctl-linux-{arch}"
    archive: none
    cosign: null
    sha256:
      amd64: "<paste>"
      arm64: "<paste>"

  dockle:
    version: "0.4.15"
    url_template: "https://github.com/goodwithtech/dockle/releases/download/v{version}/dockle_{version}_Linux-{arch_alt}.tar.gz"
    archive: tar.gz
    member: dockle
    arch_alt:
      amd64: "64bit"
      arm64: "ARM64"
    cosign: null
    sha256:
      amd64: "<paste>"
      arm64: "<paste>"

  hadolint:
    version: "2.12.0"
    url_template: "https://github.com/hadolint/hadolint/releases/download/v{version}/hadolint-Linux-{arch_alt}"
    archive: none
    arch_alt:
      amd64: "x86_64"
      arm64: "arm64"
    cosign: null
    sha256:
      amd64: "<paste>"
      arm64: "<paste>"
```

- [ ] **Step 4: Validate the manifest against the schema**

```bash
pipenv run python -c "
import json, yaml, jsonschema
from pathlib import Path
schema = json.loads(Path('regis/schemas/tools-manifest.schema.json').read_text())
doc = yaml.safe_load(Path('regis/tools/manifest.yaml').read_text())
jsonschema.validate(doc, schema)
print('manifest OK')
"
```

Expected: prints `manifest OK`. Any validation error → fix the manifest (wrong sha length, missing field, etc.).

- [ ] **Step 5: Commit**

```bash
git add regis/tools/manifest.yaml scripts/compute_tool_hashes.sh
git commit -m "feat(tools): pin scanner versions in tools manifest"
```

---

## Task 3: `regis.tools` package skeleton + manifest loader

**Files:**

- Create: `regis/tools/__init__.py`
- Create: `regis/tools/manifest.py`
- Test: extend `tests/tools/test_manifest.py`

- [ ] **Step 1: Write the failing loader test**

Append to `tests/tools/test_manifest.py`:

```python
from regis.tools.manifest import Tool, load_manifest


def test_load_manifest_returns_typed_tools() -> None:
    tools = load_manifest()
    assert "grype" in tools
    grype = tools["grype"]
    assert isinstance(grype, Tool)
    assert grype.version
    assert grype.sha256["amd64"] and grype.sha256["arm64"]


def test_tool_resolves_url_for_arch() -> None:
    tools = load_manifest()
    url = tools["dockle"].url(arch="amd64")
    assert url.endswith("Linux-64bit.tar.gz")
    assert "/v" + tools["dockle"].version + "/" in url


def test_tool_url_hadolint_arch_alt() -> None:
    tools = load_manifest()
    url = tools["hadolint"].url(arch="arm64")
    assert url.endswith("hadolint-Linux-arm64")


def test_load_manifest_raises_on_unknown_path(tmp_path) -> None:
    bad = tmp_path / "missing.yaml"
    with pytest.raises(FileNotFoundError):
        load_manifest(path=bad)
```

- [ ] **Step 2: Run, verify failure**

```bash
pipenv run pytest tests/tools/test_manifest.py -v
```

Expected: 4 new tests FAIL with `ModuleNotFoundError: regis.tools.manifest`.

- [ ] **Step 3: Implement the loader**

```python
# regis/tools/__init__.py
"""Tool fetch infrastructure (manifest + downloader)."""

from regis.tools.manifest import Tool, load_manifest

__all__ = ["Tool", "load_manifest"]
```

```python
# regis/tools/manifest.py
"""Typed view over regis/tools/manifest.yaml."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import Mapping

import jsonschema
import yaml

MANIFEST_RESOURCE = "manifest.yaml"
SCHEMA_RESOURCE = "tools-manifest.schema.json"


@dataclass(frozen=True)
class CosignPolicy:
    issuer: str
    identity_regex: str


@dataclass(frozen=True)
class Tool:
    name: str
    version: str
    url_template: str
    archive: str  # "none" | "tar.gz" | "zip"
    sha256: Mapping[str, str]  # arch -> hex
    member: str | None = None
    arch_alt: Mapping[str, str] = field(default_factory=dict)
    cosign: CosignPolicy | None = None

    def url(self, arch: str) -> str:
        arch_alt = self.arch_alt.get(arch, arch)
        return (
            self.url_template
            .replace("{version}", self.version)
            .replace("{arch_alt}", arch_alt)
            .replace("{arch}", arch)
        )

    def sha_for(self, arch: str) -> str:
        try:
            return self.sha256[arch]
        except KeyError as exc:
            raise KeyError(f"no sha256 pinned for {self.name}/{arch}") from exc


def _load_schema() -> dict:
    schema_path = files("regis.schemas").joinpath(SCHEMA_RESOURCE)
    return json.loads(schema_path.read_text(encoding="utf-8"))


def load_manifest(path: Path | None = None) -> dict[str, Tool]:
    """Load and validate the tools manifest. Returns name -> Tool."""
    if path is None:
        resource = files("regis.tools").joinpath(MANIFEST_RESOURCE)
        raw = resource.read_text(encoding="utf-8")
    else:
        raw = Path(path).read_text(encoding="utf-8")
    doc = yaml.safe_load(raw)
    jsonschema.validate(doc, _load_schema())

    tools: dict[str, Tool] = {}
    for name, body in doc["tools"].items():
        cosign_block = body.get("cosign")
        cosign = (
            CosignPolicy(issuer=cosign_block["issuer"], identity_regex=cosign_block["identity_regex"])
            if cosign_block
            else None
        )
        tools[name] = Tool(
            name=name,
            version=body["version"],
            url_template=body["url_template"],
            archive=body["archive"],
            sha256=dict(body["sha256"]),
            member=body.get("member"),
            arch_alt=dict(body.get("arch_alt") or {}),
            cosign=cosign,
        )
    return tools
```

- [ ] **Step 4: Update `pyproject.toml` to ship the data file**

In `pyproject.toml`, under `[tool.setuptools.package-data]`:

```toml
[tool.setuptools.package-data]
regis = ["py.typed"]
"regis.schemas" = ["*.json", "**/*.json"]
"regis.tools" = ["manifest.yaml"]
```

(Adapt to the existing block — add only the `regis.tools` line if the others exist.)

- [ ] **Step 5: Run tests**

```bash
pipenv run pytest tests/tools/test_manifest.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add regis/tools/__init__.py regis/tools/manifest.py pyproject.toml tests/tools/test_manifest.py
git commit -m "feat(tools): add typed manifest loader"
```

---

## Task 4: `ToolFetcher` — cache-hit path (no network)

**Files:**

- Create: `regis/tools/fetcher.py`
- Test: `tests/tools/test_fetcher.py`

- [ ] **Step 1: Write failing tests for cache hit + status**

```python
# tests/tools/test_fetcher.py
from __future__ import annotations

import hashlib
import os
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
```

- [ ] **Step 2: Run, verify failure**

```bash
pipenv run pytest tests/tools/test_fetcher.py -v
```

Expected: ImportError / ModuleNotFoundError for `regis.tools.fetcher`.

- [ ] **Step 3: Implement the cache-hit slice**

```python
# regis/tools/fetcher.py
"""Lazy downloader for analyzer tool binaries."""

from __future__ import annotations

import hashlib
import logging
import os
import platform
from dataclasses import dataclass
from pathlib import Path

from regis.tools.manifest import Tool, load_manifest

logger = logging.getLogger(__name__)


class ToolFetchError(RuntimeError):
    """Raised when a tool cannot be made available locally."""


@dataclass(frozen=True)
class ToolStatus:
    name: str
    version: str
    cached: bool
    path: Path | None
    sha256_ok: bool | None  # None when not cached


def _detect_arch() -> str:
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        return "amd64"
    if machine in ("aarch64", "arm64"):
        return "arm64"
    raise ToolFetchError(f"unsupported architecture: {machine}")


def _default_cache_dir() -> Path:
    explicit = os.environ.get("REGIS_CACHE_DIR")
    if explicit:
        return Path(explicit)
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    return base / "regis" / "tools"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class ToolFetcher:
    def __init__(
        self,
        cache_dir: Path | None = None,
        mirror: str | None = None,
        arch: str | None = None,
        verify_cosign: bool = False,
        require_cosign: bool = False,
        offline: bool = False,
    ) -> None:
        self.cache_dir = (cache_dir or _default_cache_dir()).resolve()
        self.mirror = mirror or os.environ.get("REGIS_TOOLS_MIRROR")
        self.arch = arch or _detect_arch()
        self.verify_cosign = verify_cosign
        self.require_cosign = require_cosign
        self.offline = offline or os.environ.get("REGIS_OFFLINE") == "1"
        self._tools = load_manifest()

    def _path_for(self, tool: Tool) -> Path:
        return (
            self.cache_dir
            / tool.name
            / tool.version
            / f"linux-{self.arch}"
            / tool.name
        )

    def ensure(self, name: str) -> Path:
        tool = self._tools[name]  # KeyError on unknown name (test expects this)
        target = self._path_for(tool)
        if target.exists() and _sha256_file(target) == tool.sha_for(self.arch):
            return target
        if self.offline:
            raise ToolFetchError(
                f"{name} not in cache and offline mode is enabled "
                f"(REGIS_OFFLINE=1). Expected at {target}."
            )
        # download path implemented in Task 5
        raise NotImplementedError("download path implemented in next task")

    def status(self) -> list[ToolStatus]:
        out: list[ToolStatus] = []
        for name, tool in self._tools.items():
            path = self._path_for(tool)
            cached = path.exists()
            sha_ok: bool | None = None
            if cached:
                sha_ok = _sha256_file(path) == tool.sha_for(self.arch)
            out.append(
                ToolStatus(
                    name=name,
                    version=tool.version,
                    cached=cached,
                    path=path if cached else None,
                    sha256_ok=sha_ok,
                )
            )
        return out
```

- [ ] **Step 4: Run tests**

```bash
pipenv run pytest tests/tools/test_fetcher.py -v
```

Expected: the 4 tests in this task PASS. (Other future tests will fail until later tasks.)

- [ ] **Step 5: Commit**

```bash
git add regis/tools/fetcher.py tests/tools/test_fetcher.py
git commit -m "feat(tools): add ToolFetcher cache-hit + status surfaces"
```

---

## Task 5: `ToolFetcher` — download + sha256 verification

**Files:**

- Modify: `regis/tools/fetcher.py`
- Test: extend `tests/tools/test_fetcher.py`

- [ ] **Step 1: Add a fixture spinning up a local HTTP server**

Append to `tests/tools/test_fetcher.py`:

```python
import http.server
import threading
from contextlib import contextmanager


@contextmanager
def _serve(directory: Path, port: int = 0):
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(
        *a, directory=str(directory), **kw
    )
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        thread.join(timeout=2)
```

- [ ] **Step 2: Write failing download tests**

```python
def test_ensure_downloads_when_missing(monkeypatch, tmp_path):
    payload = b"binary-bytes"
    sha = hashlib.sha256(payload).hexdigest()
    # Publish the file via local HTTP
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
        partial = cache / "grype" / "0.0.1" / "linux-amd64" / "grype.partial"
        final = cache / "grype" / "0.0.1" / "linux-amd64" / "grype"
        assert not partial.exists()
        assert not final.exists()


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
```

- [ ] **Step 3: Run, verify failure**

```bash
pipenv run pytest tests/tools/test_fetcher.py -v -k "downloads or sha256_mismatch or extracts"
```

Expected: all 3 FAIL with `NotImplementedError`.

- [ ] **Step 4: Implement download + verify + extract**

Replace the `ensure()` body and add helpers in `regis/tools/fetcher.py`:

```python
import shutil
import tarfile
import tempfile
import urllib.request
import zipfile

# ... existing imports and code ...

DOWNLOAD_TIMEOUT_S = 120


class ToolFetcher:
    # ... existing __init__, _path_for, status ...

    def ensure(self, name: str) -> Path:
        tool = self._tools[name]
        target = self._path_for(tool)
        expected_sha = tool.sha_for(self.arch)
        if target.exists() and _sha256_file(target) == expected_sha:
            return target
        if self.offline:
            raise ToolFetchError(
                f"{name} not in cache and offline mode is enabled "
                f"(REGIS_OFFLINE=1). Expected at {target}."
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        self._download_and_install(tool, target, expected_sha)
        return target

    def _resolve_url(self, tool: Tool) -> str:
        if self.mirror:
            ext = {"none": "", "tar.gz": ".tar.gz", "zip": ".zip"}[tool.archive]
            return f"{self.mirror.rstrip('/')}/{tool.name}/{tool.version}/{tool.name}_{tool.version}_linux_{self.arch}{ext}"
        return tool.url(arch=self.arch)

    def _download_and_install(self, tool: Tool, target: Path, expected_sha: str) -> None:
        url = self._resolve_url(tool)
        logger.info("Fetching %s %s from %s", tool.name, tool.version, url)
        with tempfile.NamedTemporaryFile(
            dir=target.parent, prefix=f"{tool.name}.", suffix=".partial", delete=False
        ) as tmpf:
            partial = Path(tmpf.name)
        try:
            with urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT_S) as resp:  # nosec B310 — http(s) only, verified by sha256
                with partial.open("wb") as out:
                    shutil.copyfileobj(resp, out)

            extracted = self._maybe_extract(tool, partial)
            actual = _sha256_file(extracted)
            if actual != expected_sha:
                raise ToolFetchError(
                    f"{tool.name} sha256 mismatch: expected {expected_sha}, got {actual}"
                )
            extracted.replace(target)
            os.chmod(target, 0o755)
        finally:
            if partial.exists():
                partial.unlink()
            # extracted may equal partial; cleanup any sibling
            for stray in target.parent.glob(f"{tool.name}.*.partial*"):
                stray.unlink(missing_ok=True)

    def _maybe_extract(self, tool: Tool, archive_path: Path) -> Path:
        if tool.archive == "none":
            return archive_path
        if tool.member is None:
            raise ToolFetchError(f"{tool.name}: archive set but no member to extract")
        out = archive_path.with_suffix(".extracted")
        if tool.archive == "tar.gz":
            with tarfile.open(archive_path, "r:gz") as tar:
                m = tar.getmember(tool.member)
                with tar.extractfile(m) as src, out.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
        elif tool.archive == "zip":
            with zipfile.ZipFile(archive_path) as zf:
                with zf.open(tool.member) as src, out.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
        else:
            raise ToolFetchError(f"unsupported archive type: {tool.archive}")
        archive_path.unlink()
        return out
```

- [ ] **Step 5: Run all fetcher tests**

```bash
pipenv run pytest tests/tools/test_fetcher.py -v
```

Expected: all PASS (the 4 cache-hit tests from Task 4 and the 3 download tests from this task).

- [ ] **Step 6: Commit**

```bash
git add regis/tools/fetcher.py tests/tools/test_fetcher.py
git commit -m "feat(tools): download and verify tool binaries with sha256"
```

---

## Task 6: Atomic write + flock concurrency

**Files:**

- Modify: `regis/tools/fetcher.py`
- Test: extend `tests/tools/test_fetcher.py`

- [ ] **Step 1: Write failing concurrency test**

```python
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

    handler = lambda *a, **kw: CountingHandler(*a, directory=str(pub), **kw)
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

        def worker():
            f = ToolFetcher(cache_dir=cache, arch="amd64")
            return f.ensure("grype")

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            paths = list(pool.map(lambda _: worker(), range(4)))

        assert all(p == paths[0] for p in paths)
        assert paths[0].read_bytes() == payload
        # Concurrent first-run: only one fetch should hit the network.
        assert serve_count["n"] == 1
    finally:
        server.shutdown()
        thread.join(timeout=2)
```

- [ ] **Step 2: Run, verify failure**

```bash
pipenv run pytest tests/tools/test_fetcher.py::test_concurrent_ensure_downloads_only_once -v
```

Expected: FAIL with `serve_count["n"] > 1` (or possibly a race-induced exception).

- [ ] **Step 3: Add cross-process lock around download**

In `regis/tools/fetcher.py`, add at top:

```python
import fcntl
from contextlib import contextmanager


@contextmanager
def _file_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as lockf:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
```

Wrap the download in `ensure()`:

```python
    def ensure(self, name: str) -> Path:
        tool = self._tools[name]
        target = self._path_for(tool)
        expected_sha = tool.sha_for(self.arch)
        if target.exists() and _sha256_file(target) == expected_sha:
            return target
        if self.offline:
            raise ToolFetchError(
                f"{name} not in cache and offline mode is enabled "
                f"(REGIS_OFFLINE=1). Expected at {target}."
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        lock_path = target.with_suffix(target.suffix + ".lock")
        with _file_lock(lock_path):
            # Re-check inside the lock: another thread may have downloaded.
            if target.exists() and _sha256_file(target) == expected_sha:
                return target
            self._download_and_install(tool, target, expected_sha)
        return target
```

- [ ] **Step 4: Run tests**

```bash
pipenv run pytest tests/tools/test_fetcher.py -v
```

Expected: all PASS, `serve_count["n"] == 1`.

- [ ] **Step 5: Commit**

```bash
git add regis/tools/fetcher.py tests/tools/test_fetcher.py
git commit -m "feat(tools): serialize concurrent tool downloads via flock"
```

---

## Task 7: `REGIS_TOOLS_MIRROR` integration tests

**Files:**

- Test: extend `tests/tools/test_fetcher.py`

The mirror code path was already added in Task 5 — this task only adds tests that exercise it.

- [ ] **Step 1: Add the mirror tests**

```python
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
```

- [ ] **Step 2: Run and confirm pass**

```bash
pipenv run pytest tests/tools/test_fetcher.py -v -k "mirror"
```

Expected: 2 PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/tools/test_fetcher.py
git commit -m "test(tools): cover REGIS_TOOLS_MIRROR fetch path"
```

---

## Task 8: Cosign verification (best-effort + require)

**Files:**

- Create: `regis/tools/cosign.py`
- Modify: `regis/tools/fetcher.py`
- Test: `tests/tools/test_cosign.py`, extend `tests/tools/test_fetcher.py`

- [ ] **Step 1: Failing cosign tests**

```python
# tests/tools/test_cosign.py
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
```

- [ ] **Step 2: Implement minimal cosign module**

```python
# regis/tools/cosign.py
"""Best-effort cosign verification for downloaded tool binaries."""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
from pathlib import Path

from regis.tools.manifest import CosignPolicy


class CosignUnavailable(RuntimeError):
    """Raised when the cosign binary is not on PATH."""


class CosignVerificationFailed(RuntimeError):
    """Raised when cosign rejects the signature."""


def verify_blob(blob: Path, source_url: str, policy: CosignPolicy) -> None:
    """Verify *blob* against the keyless-signed signature published next to *source_url*.

    Assumes signature artefacts live at ``{source_url}.sig`` and ``{source_url}.pem`` —
    the layout used by GoReleaser-built projects (grype, syft, trufflehog).
    """
    cosign = shutil.which("cosign")
    if not cosign:
        raise CosignUnavailable("cosign binary not found on PATH")
    cmd = [
        cosign, "verify-blob",
        "--certificate-oidc-issuer", policy.issuer,
        "--certificate-identity-regexp", policy.identity_regex,
        "--signature", f"{source_url}.sig",
        "--certificate", f"{source_url}.pem",
        str(blob),
    ]
    result = subprocess.run(  # nosec B603
        cmd, capture_output=True, text=True, check=False, timeout=30
    )
    if result.returncode != 0:
        raise CosignVerificationFailed(
            f"cosign verify-blob failed: {result.stderr.strip() or result.stdout.strip()}"
        )
```

- [ ] **Step 3: Wire into the fetcher**

Add in `regis/tools/fetcher.py`:

```python
from regis.tools.cosign import (
    CosignUnavailable,
    CosignVerificationFailed,
    verify_blob,
)
```

Inside `_download_and_install`, after the sha matches and before `extracted.replace(target)`:

```python
            if tool.cosign is not None:
                try:
                    verify_blob(extracted, url, tool.cosign)
                    logger.info("cosign: verified %s", tool.name)
                except CosignUnavailable as exc:
                    if self.require_cosign or os.environ.get("REGIS_REQUIRE_COSIGN") == "1":
                        raise ToolFetchError(
                            f"{tool.name}: cosign required but unavailable ({exc})"
                        ) from exc
                    logger.info(
                        "cosign verification skipped for %s (binary not on PATH)",
                        tool.name,
                    )
                except CosignVerificationFailed as exc:
                    raise ToolFetchError(
                        f"{tool.name}: cosign verification failed: {exc}"
                    ) from exc
```

- [ ] **Step 4: Add fetcher-level tests using a stub cosign**

Append to `tests/tools/test_fetcher.py`:

```python
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
                name="grype", version="0.0.1",
                url_template=f"{base_url}/tool.bin",
                archive="none", sha256={"amd64": sha, "arm64": sha},
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
                name="grype", version="0.0.1",
                url_template=f"{base_url}/tool.bin",
                archive="none", sha256={"amd64": sha, "arm64": sha},
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
```

- [ ] **Step 5: Run cosign tests**

```bash
pipenv run pytest tests/tools/test_cosign.py tests/tools/test_fetcher.py -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add regis/tools/cosign.py regis/tools/fetcher.py tests/tools/test_cosign.py tests/tools/test_fetcher.py
git commit -m "feat(tools): best-effort cosign verification with require flag"
```

---

## Task 9: `fetch_all` and arch auto-detection coverage

**Files:**

- Modify: `regis/tools/fetcher.py`
- Test: extend `tests/tools/test_fetcher.py`

- [ ] **Step 1: Failing tests for `fetch_all`**

```python
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
                name=n, version="0.0.1",
                url_template=f"{base_url}/{n}.bin",
                archive="none", sha256={"amd64": shas[n], "arm64": shas[n]},
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
                name="grype", version="0.0.1",
                url_template=f"{base_url}/grype.bin",
                archive="none", sha256={"amd64": sha, "arm64": sha},
            ),
            "syft": Tool(
                name="syft", version="0.0.1",
                url_template="https://offline.invalid",
                archive="none", sha256={"amd64": "0" * 64, "arm64": "0" * 64},
            ),
        }
        _patch_manifest(monkeypatch, tools)
        fetcher = ToolFetcher(cache_dir=tmp_path / "cache", arch="amd64")
        result = fetcher.fetch_all(names=["grype"])
        assert list(result) == ["grype"]
```

- [ ] **Step 2: Implement `fetch_all`**

Add to `ToolFetcher` in `regis/tools/fetcher.py`:

```python
    def fetch_all(self, names: list[str] | None = None) -> dict[str, Path]:
        targets = list(names) if names else list(self._tools)
        out: dict[str, Path] = {}
        for name in targets:
            out[name] = self.ensure(name)
        return out
```

- [ ] **Step 3: Run tests**

```bash
pipenv run pytest tests/tools/test_fetcher.py -v
```

Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add regis/tools/fetcher.py tests/tools/test_fetcher.py
git commit -m "feat(tools): fetch_all helper for bootstrap"
```

---

## Task 10: `ensure_tool()` wrapper in `regis/utils/process.py`

**Files:**

- Modify: `regis/utils/process.py`
- Test: `tests/tools/test_ensure_tool.py`

- [ ] **Step 1: Failing tests**

```python
# tests/tools/test_ensure_tool.py
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
```

- [ ] **Step 2: Run, verify failure**

```bash
pipenv run pytest tests/tools/test_ensure_tool.py -v
```

Expected: 3 FAIL (`ensure_tool` not defined).

- [ ] **Step 3: Implement `ensure_tool`**

Append to `regis/utils/process.py`:

```python
from functools import lru_cache


@lru_cache(maxsize=1)
def _default_fetcher():
    from regis.tools.fetcher import ToolFetcher
    return ToolFetcher()


@lru_cache(maxsize=1)
def _manifest_names() -> frozenset[str]:
    from regis.tools.manifest import load_manifest
    return frozenset(load_manifest().keys())


def _in_manifest(name: str) -> bool:
    return name in _manifest_names()


def ensure_tool(name: str, install_hint: str | None = None) -> str:
    """Return absolute path to *name*, downloading via the manifest if needed.

    Resolution:
      1. ``shutil.which(name)`` (host PATH, full image, dev install)
      2. If *name* is in the tools manifest, delegate to `ToolFetcher.ensure`.
      3. Otherwise raise `ClickException` (same shape as `require_tool`).
    """
    found = shutil.which(name)
    if found:
        return found
    if _in_manifest(name):
        from regis.tools.fetcher import ToolFetchError
        try:
            return str(_default_fetcher().ensure(name))
        except ToolFetchError as exc:
            raise click.ClickException(str(exc)) from exc
    message = f"'{name}' not found in PATH. Please install it."
    if install_hint:
        message = f"{message}\n\n{install_hint}"
    raise click.ClickException(message)
```

- [ ] **Step 4: Run all relevant tests**

```bash
pipenv run pytest tests/tools/ -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add regis/utils/process.py tests/tools/test_ensure_tool.py
git commit -m "feat(tools): add ensure_tool helper bridging PATH and fetcher"
```

---

## Task 11: Switch tool wrappers to `ensure_tool`

**Files:**

- Modify: `regis/utils/grype.py`, `regis/utils/syft.py`, `regis/utils/trufflehog.py`, `regis/utils/regctl.py`
- Modify: `regis/analyzers/hadolint.py`, `regis/analyzers/dockle.py`
- Modify: relevant test files (one assertion shift if mocks of `shutil.which` exist)

- [ ] **Step 1: Patch each wrapper to use `ensure_tool`**

In `regis/utils/grype.py`, replace the `shutil.which` block:

```python
# Before:
grype_path = shutil.which("grype")
if not grype_path:
    raise AnalyzerError("grype executable not found in PATH")

# After:
from regis.utils.process import ensure_tool
try:
    grype_path = ensure_tool("grype")
except click.ClickException as exc:
    raise AnalyzerError(str(exc)) from exc
```

(Drop the `import shutil` if no longer used; add `import click`.)

Apply the same pattern in `regis/utils/syft.py` and `regis/utils/trufflehog.py`.

For `regis/utils/regctl.py`, replace `cmd = ["regctl"]` with:

```python
from regis.utils.process import ensure_tool
cmd = [ensure_tool("regctl")]
```

For `regis/analyzers/hadolint.py`, change `cmd_hadolint = ["hadolint", "-f", "json", "-"]` to:

```python
from regis.utils.process import ensure_tool
cmd_hadolint = [ensure_tool("hadolint"), "-f", "json", "-"]
```

For `regis/analyzers/dockle.py`, change `cmd_dockle = ["dockle", "-f", "json", target]` to:

```python
from regis.utils.process import ensure_tool
cmd_dockle = [ensure_tool("dockle"), "-f", "json", target]
```

- [ ] **Step 2: Update any test that patched `shutil.which` for tool detection**

```bash
pipenv run grep -rln 'shutil\.which.*\(grype\|syft\|trufflehog\|regctl\|hadolint\|dockle\)' tests/
```

For each match, switch the patch target to `regis.utils.process.ensure_tool`. Tests that asserted on the `AnalyzerError("X executable not found in PATH")` exact message stay valid because `ensure_tool` falls through to `ClickException` which is re-wrapped to `AnalyzerError` — assertions on the substring `not found` continue to pass.

- [ ] **Step 3: Run full test suite (no coverage)**

```bash
pipenv run pytest --no-cov
```

Expected: all tests PASS. Investigate and fix any failure before continuing.

- [ ] **Step 4: Run with coverage**

```bash
pipenv run pytest
```

Expected: coverage ≥ 90 %.

- [ ] **Step 5: Commit**

```bash
git add regis/utils/grype.py regis/utils/syft.py regis/utils/trufflehog.py regis/utils/regctl.py regis/analyzers/hadolint.py regis/analyzers/dockle.py tests/
git commit -m "feat(analyzers): route tool lookup through ensure_tool"
```

---

## Task 12: `regis bootstrap tools` CLI command

**Files:**

- Modify: `regis/commands/bootstrap.py`
- Test: `tests/commands/test_bootstrap_tools.py` (new)

- [ ] **Step 1: Failing CLI tests**

```python
# tests/commands/test_bootstrap_tools.py
from __future__ import annotations

from click.testing import CliRunner

from regis.cli import main


def test_bootstrap_tools_check_lists_status(monkeypatch, tmp_path):
    monkeypatch.setenv("REGIS_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("REGIS_OFFLINE", "1")
    runner = CliRunner()
    result = runner.invoke(main, ["bootstrap", "tools", "--check"])
    assert result.exit_code == 0
    assert "grype" in result.output


def test_bootstrap_tools_single_tool(monkeypatch, tmp_path):
    monkeypatch.setenv("REGIS_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("REGIS_OFFLINE", "1")
    runner = CliRunner()
    result = runner.invoke(main, ["bootstrap", "tools", "--tool", "grype"])
    # offline + empty cache → expected failure with a clear message
    assert result.exit_code != 0
    assert "grype" in result.output
    assert "offline" in result.output.lower()
```

- [ ] **Step 2: Implement the command**

`regis/commands/bootstrap.py` already defines `@click.group(name="bootstrap")` (line 80). Append this single command at the bottom of the file:

```python
import click

from regis.tools.fetcher import ToolFetcher, ToolFetchError


@bootstrap.command(name="tools")
@click.option("--tool", "tool_name", default=None, help="Fetch a single tool.")
@click.option("--check", is_flag=True, help="Show status, do not download.")
def bootstrap_tools(tool_name: str | None, check: bool) -> None:
    """Fetch (or check) tool binaries declared in the manifest."""
    fetcher = ToolFetcher()
    if check:
        for status in fetcher.status():
            if status.cached and status.sha256_ok:
                mark = "✓"
            elif status.cached and status.sha256_ok is False:
                mark = "✗"
            else:
                mark = "⏩"
            path = str(status.path) if status.path else "(not cached)"
            click.echo(f"  {mark} {status.name:<12} {status.version:<10} {path}")
        return
    names = [tool_name] if tool_name else None
    try:
        result = fetcher.fetch_all(names=names)
    except ToolFetchError as exc:
        raise click.ClickException(str(exc)) from exc
    for name, path in result.items():
        click.echo(f"  ✓ {name:<12} -> {path}")
```

- [ ] **Step 3: Run tests**

```bash
pipenv run pytest tests/commands/test_bootstrap_tools.py -v
```

Expected: both PASS.

- [ ] **Step 4: Commit**

```bash
git add regis/commands/bootstrap.py tests/commands/test_bootstrap_tools.py
git commit -m "feat(cli): regis bootstrap tools subcommand"
```

---

## Task 13: Extend `regis doctor` with Tools section

**Files:**

- Modify: `regis/commands/doctor.py`
- Test: extend or add `tests/commands/test_doctor.py`

- [ ] **Step 1: Failing test**

```python
# tests/commands/test_doctor.py (add or extend)
from click.testing import CliRunner
from regis.cli import main


def test_doctor_lists_tools_section(monkeypatch, tmp_path):
    monkeypatch.setenv("REGIS_CACHE_DIR", str(tmp_path))
    # Force the manifest-backed lookup path (no host install)
    import shutil
    monkeypatch.setattr(shutil, "which", lambda _n: None)
    runner = CliRunner()
    result = runner.invoke(main, ["doctor"])
    # doctor exits non-zero when tools are missing, but the section must still print
    assert "Tools" in result.output or "grype" in result.output
```

- [ ] **Step 2: Implement the section**

In `regis/commands/doctor.py`, after the existing loop:

```python
from regis.tools.fetcher import ToolFetcher


def _print_tools_section() -> bool:
    fetcher = ToolFetcher()
    click.echo("Tools (manifest):")
    all_ok = True
    for status in fetcher.status():
        if status.cached and status.sha256_ok:
            mark = "✓"
            detail = f"cached @ {status.path}"
        elif status.cached and status.sha256_ok is False:
            mark = "✗"
            detail = f"cache present but sha256 MISMATCH @ {status.path}"
            all_ok = False
        else:
            mark = "⏩"
            detail = "not cached (will fetch on first use)"
        click.echo(f"  {mark} {status.name:<12} {status.version:<10} {detail}")
    return all_ok
```

Call it at the end of `doctor()` before the `SystemExit`:

```python
    tools_ok = _print_tools_section()
    if not all_ok or not tools_ok:
        raise SystemExit(1)
```

(Tighten as needed depending on the existing `all_ok` semantics — "not cached" should not fail doctor, only "MISMATCH" should.)

- [ ] **Step 3: Run tests**

```bash
pipenv run pytest tests/commands/test_doctor.py -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add regis/commands/doctor.py tests/commands/test_doctor.py
git commit -m "feat(cli): regis doctor reports tools manifest cache status"
```

---

## Task 14: Dockerfile — two-variant build, distroless runtime

**Files:**

- Modify: `Dockerfile`
- Verify: `.dockerignore` does not exclude `regis/tools/`

- [ ] **Step 1: Confirm `.dockerignore` keeps `regis/tools/`**

```bash
grep -E "^regis/tools|^regis$" .dockerignore || echo "OK: not excluded"
```

If a rule excludes it, add an explicit `!regis/tools/` before the broad pattern.

- [ ] **Step 2: Replace `Dockerfile`**

```dockerfile
# syntax=docker/dockerfile:1.7
ARG VARIANT=slim

# ── Stage 1: frontend-builder (unchanged) ────────────────────────────────
FROM node:25-slim AS frontend-builder
RUN npm install -g pnpm@10.10.0
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml* ./
COPY apps/ apps/
RUN pnpm install --frozen-lockfile
WORKDIR /app/apps/dashboard
RUN pnpm run build

# ── Stage 2: python-builder (was python:3.14-slim) ───────────────────────
FROM python:3.11-slim AS python-builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1
# hadolint ignore=DL3008
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /src
COPY pyproject.toml Pipfile Pipfile.lock ./
COPY regis/ regis/
COPY --from=frontend-builder /app/apps/dashboard/build regis/dashboard_assets
# `--copies` (not symlinks) so the venv's python3.11 is a real binary copied
# from the slim base — distroless runtime has no /usr/local/bin/python to
# satisfy a symlink. See plan Task 0 POC for the rationale.
RUN rm -rf /opt/venv && python -m venv --copies /opt/venv
RUN VERSION=$(grep -oP '(?<=version = ")[^"]+' pyproject.toml) && \
    SETUPTOOLS_SCM_PRETEND_VERSION="$VERSION" pip install --no-compile . && \
    find /opt/venv -type d -name __pycache__ -prune -exec rm -rf {} + && \
    find /opt/venv -type f -name '*.pyc' -delete

# ── Stage 3: tools-fetcher (unchanged structure) ─────────────────────────
FROM curlimages/curl:8.10.1 AS tools-fetcher
# ... keep current body unchanged ...

# ── Stage 4a: final-slim ──────────────────────────────────────────────────
FROM gcr.io/distroless/python3-debian12:nonroot AS final-slim
LABEL org.opencontainers.image.title="regis" \
      org.opencontainers.image.description="Regis — Registry Scores. Slim variant (lazy-load scanners)." \
      org.opencontainers.image.source="https://github.com/trivoallan/regis" \
      org.opencontainers.image.licenses="MIT"
ENV PATH="/opt/venv/bin:/usr/local/bin:$PATH" \
    PYTHONPATH=/opt/venv/lib/python3.11/site-packages \
    REGIS_VARIANT=slim \
    HOME=/home/nonroot
COPY --from=python-builder /opt/venv /opt/venv
COPY --from=tools-fetcher /tools/regctl /usr/local/bin/regctl
WORKDIR /home/nonroot
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD ["regis", "list"]
ENTRYPOINT ["regis"]
CMD ["--help"]

# ── Stage 4b: final-full ──────────────────────────────────────────────────
FROM gcr.io/distroless/python3-debian12:nonroot AS final-full
LABEL org.opencontainers.image.title="regis" \
      org.opencontainers.image.description="Regis — Registry Scores. Full variant (scanners baked)." \
      org.opencontainers.image.source="https://github.com/trivoallan/regis" \
      org.opencontainers.image.licenses="MIT"
ENV PATH="/opt/venv/bin:/usr/local/bin:$PATH" \
    PYTHONPATH=/opt/venv/lib/python3.11/site-packages \
    REGIS_VARIANT=full \
    HOME=/home/nonroot
COPY --from=python-builder /opt/venv /opt/venv
COPY --from=tools-fetcher /tools/grype      /usr/local/bin/grype
COPY --from=tools-fetcher /tools/syft       /usr/local/bin/syft
COPY --from=tools-fetcher /tools/trufflehog /usr/local/bin/trufflehog
COPY --from=tools-fetcher /tools/hadolint   /usr/local/bin/hadolint
COPY --from=tools-fetcher /tools/dockle     /usr/local/bin/dockle
COPY --from=tools-fetcher /tools/regctl     /usr/local/bin/regctl
WORKDIR /home/nonroot
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD ["regis", "list"]
ENTRYPOINT ["regis"]
CMD ["--help"]

# ── Selector ──────────────────────────────────────────────────────────────
FROM final-${VARIANT} AS final
```

(Keep the existing `tools-fetcher` stage body verbatim; only the two final stages and the selector are new.)

**Why `--copies` + `PYTHONPATH`?** The POC in Task 0 found that distroless cannot follow the venv's default symlinks (which point to `/usr/local/bin/python`, absent in distroless). `--copies` makes `/opt/venv/bin/python3.11` a real binary so the `regis` console-script shebang resolves; `PYTHONPATH` is a belt-and-suspenders safety net in case the shebang dispatch is bypassed. If `docker run regis:slim --help` errors with `ModuleNotFoundError` or `OSError: cannot open`, drop the `PYTHONPATH` and try `python -m regis` form of ENTRYPOINT instead.

- [ ] **Step 3: Build slim locally and smoke**

```bash
docker buildx build --build-arg VARIANT=slim --load -t regis:slim .
docker run --rm regis:slim --help
docker run --rm -e REGIS_OFFLINE=1 regis:slim doctor || true
docker image inspect regis:slim --format='{{.Size}}' | numfmt --to=iec
```

Expected: `--help` prints; `doctor` lists tools with `⏩ not cached`; image size <150 MB (likely ~80-110 MB).

- [ ] **Step 4: Build full and smoke**

```bash
docker buildx build --build-arg VARIANT=full --load -t regis:full .
docker run --rm regis:full doctor
docker image inspect regis:full --format='{{.Size}}' | numfmt --to=iec
```

Expected: `doctor` shows all six tools as ✓ on PATH; image size <400 MB.

- [ ] **Step 5: Commit**

```bash
git add Dockerfile .dockerignore
git commit -m "feat(build)!: two-variant Dockerfile (slim default, full opt-in) on distroless

BREAKING CHANGE: the default :latest image is now slim. Scanner binaries
(grype, syft, trufflehog, hadolint, dockle) are downloaded on first use.
Air-gapped users should pull :latest-full instead, or set REGIS_TOOLS_MIRROR.

Runtime base switched to gcr.io/distroless/python3-debian12:nonroot
(Python 3.11). Runtime user changed from regis:1001 to nonroot:65532."
```

---

## Task 15: CI — `cd-docker.yml` matrix on variant

**Files:**

- Modify: `.github/workflows/cd-docker.yml`

- [ ] **Step 1: Read current workflow**

```bash
cat .github/workflows/cd-docker.yml
```

- [ ] **Step 2: Convert the build job to a matrix**

Add at the job level:

```yaml
strategy:
  fail-fast: false
  matrix:
    variant: [slim, full]
```

In the build step, add the build arg and adjust tags:

```yaml
- name: Set image tags
  id: tags
  run: |
    if [ "${{ matrix.variant }}" = "slim" ]; then
      echo "tags=ghcr.io/${{ github.repository_owner }}/regis:${{ env.VERSION }},ghcr.io/${{ github.repository_owner }}/regis:latest" >> $GITHUB_OUTPUT
    else
      echo "tags=ghcr.io/${{ github.repository_owner }}/regis:${{ env.VERSION }}-full,ghcr.io/${{ github.repository_owner }}/regis:latest-full" >> $GITHUB_OUTPUT
    fi

- name: Build and push
  uses: docker/build-push-action@<pinned-sha>
  with:
    context: .
    platforms: linux/amd64,linux/arm64
    push: true
    build-args: |
      VARIANT=${{ matrix.variant }}
    tags: ${{ steps.tags.outputs.tags }}
```

Keep the SBOM step inside the matrix so each variant gets its own SBOM attached to the release.

- [ ] **Step 3: Lint workflow**

```bash
trunk check .github/workflows/cd-docker.yml
```

Fix any actionlint/yamllint issues reported.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/cd-docker.yml
git commit -m "ci(docker): matrix-publish slim and full image variants"
```

---

## Task 16: CI — `ci-image-size.yml` per-variant ceilings

**Files:**

- Modify: `.github/workflows/ci-image-size.yml`

- [ ] **Step 1: Replace the workflow body**

Inside `jobs.image-size`:

```yaml
strategy:
  fail-fast: false
  matrix:
    include:
      - variant: slim
        ceiling: 150MB
      - variant: full
        ceiling: 400MB
steps:
  - name: Checkout
    uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
  - name: Set up Docker Buildx
    uses: docker/setup-buildx-action@4d04d5d9486b7bd6fa91e7baf45bbb4f8b9deedd # v4.0.0
  - name: Build image (${{ matrix.variant }})
    uses: docker/build-push-action@bcafcacb16a39f128d818304e6c9c0c18556b85f # v7.1.0
    with:
      context: .
      load: true
      tags: regis:size-check-${{ matrix.variant }}
      build-args: |
        VARIANT=${{ matrix.variant }}
      cache-from: type=gha,scope=${{ matrix.variant }}
      cache-to: type=gha,mode=max,scope=${{ matrix.variant }}
  - name: Enforce size limit (${{ matrix.variant }} ≤ ${{ matrix.ceiling }})
    uses: wemake-services/docker-image-size-limit@f5970eb0c2180ac296475bfd22c5a58955370051 # 2.2.0
    with:
      image: regis:size-check-${{ matrix.variant }}
      size: ${{ matrix.ceiling }}
      show_current_size: true
```

Replace the long comment block on size measurement with a one-line pointer:

```yaml
# See docs/superpowers/specs/2026-05-31-image-size-round-3-design.md for
# the breakdown behind these ceilings.
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci-image-size.yml
git commit -m "ci(image-size): per-variant ceilings (slim 150MB, full 400MB)"
```

---

## Task 17: CI — `ci-tools-manifest.yml` (validate sha256s)

**Files:**

- Create: `.github/workflows/ci-tools-manifest.yml`

- [ ] **Step 1: Write the workflow**

```yaml
# .github/workflows/ci-tools-manifest.yml
name: CI / Tools Manifest

on:
  pull_request:
    paths:
      - regis/tools/manifest.yaml
      - regis/schemas/tools-manifest.schema.json
      - .github/workflows/ci-tools-manifest.yml
  schedule:
    - cron: "0 6 * * 1" # weekly
  workflow_dispatch:

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
      - uses: actions/setup-python@<pinned-sha>
        with: { python-version: "3.11" }
      - run: pip install pyyaml jsonschema
      - name: Validate manifest against schema
        run: |
          python - <<'PY'
          import json, yaml, jsonschema
          from pathlib import Path
          s = json.loads(Path('regis/schemas/tools-manifest.schema.json').read_text())
          d = yaml.safe_load(Path('regis/tools/manifest.yaml').read_text())
          jsonschema.validate(d, s)
          print('schema OK')
          PY
      - name: Recompute and verify sha256s
        run: |
          python - <<'PY'
          import hashlib, urllib.request, yaml, sys
          from pathlib import Path
          tools = yaml.safe_load(Path('regis/tools/manifest.yaml').read_text())['tools']
          bad = []
          for name, t in tools.items():
              for arch in ('amd64', 'arm64'):
                  arch_alt = (t.get('arch_alt') or {}).get(arch, arch)
                  url = (t['url_template']
                         .replace('{version}', t['version'])
                         .replace('{arch_alt}', arch_alt)
                         .replace('{arch}', arch))
                  print('GET', url)
                  data = urllib.request.urlopen(url, timeout=120).read()
                  got = hashlib.sha256(data).hexdigest()
                  want = t['sha256'][arch]
                  if got != want:
                      bad.append((name, arch, want, got))
          if bad:
              for n, a, w, g in bad:
                  print(f'MISMATCH {n}/{a}: manifest={w} actual={g}', file=sys.stderr)
              sys.exit(1)
          print('All sha256s OK')
          PY
```

- [ ] **Step 2: Pin the action SHA**

Replace `<pinned-sha>` for `actions/setup-python` with the SHA used in another workflow in this repo (run `grep -h "setup-python@" .github/workflows/*.yml | sort -u`).

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci-tools-manifest.yml
git commit -m "ci(tools): validate tools manifest sha256s on PR and weekly"
```

---

## Task 18: CI — `ci-tools-fetch-smoke.yml`

**Files:**

- Create: `.github/workflows/ci-tools-fetch-smoke.yml`

- [ ] **Step 1: Write the workflow**

```yaml
# .github/workflows/ci-tools-fetch-smoke.yml
name: CI / Tools Fetch Smoke

on:
  pull_request:
    paths:
      - regis/tools/**
      - regis/utils/process.py
      - regis/analyzers/**
      - regis/utils/{grype,syft,trufflehog,regctl}.py
      - Dockerfile
      - .github/workflows/ci-tools-fetch-smoke.yml
  workflow_dispatch:

permissions:
  contents: read

jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
      - uses: docker/setup-buildx-action@4d04d5d9486b7bd6fa91e7baf45bbb4f8b9deedd # v4.0.0
      - name: Build slim image
        uses: docker/build-push-action@bcafcacb16a39f128d818304e6c9c0c18556b85f # v7.1.0
        with:
          context: .
          load: true
          tags: regis:slim-smoke
          build-args: |
            VARIANT=slim
      - name: Cache empty → check
        run: docker run --rm -e REGIS_OFFLINE=1 regis:slim-smoke bootstrap tools --check
      - name: Cold fetch all tools
        id: fetch
        run: |
          start=$(date +%s)
          docker run --rm -v "$PWD/.regis-cache:/home/nonroot/.cache/regis" \
            regis:slim-smoke bootstrap tools
          echo "duration=$(( $(date +%s) - start ))" >> $GITHUB_OUTPUT
      - name: Annotate cold-fetch duration
        run: echo "::notice::Cold fetch took ${{ steps.fetch.outputs.duration }}s"
      - name: Analyze alpine:3.20 with warm cache
        run: |
          docker run --rm -v "$PWD/.regis-cache:/home/nonroot/.cache/regis" \
            regis:slim-smoke analyze docker.io/library/alpine:3.20 --output json
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci-tools-fetch-smoke.yml
git commit -m "ci(tools): end-to-end smoke for lazy fetch + warm-cache analyze"
```

---

## Task 19: Documentation — tools management, config, CLI reference

**Files:**

- Create: `docs/website/docs/usage/tools-management.md`
- Modify: `docs/website/docs/usage/configuration.md` (env vars table)
- Modify: `docs/website/docs/reference/cli.md` (bootstrap tools + doctor)

- [ ] **Step 1: Write tools-management.md**

Create `docs/website/docs/usage/tools-management.md`. Outline (the engineer expands each section with full prose, drawing from the spec):

- **Frontmatter**: `id: tools-management`, `title: Managing analyzer tools`.
- **Lead paragraph**: `:latest` is slim, only regis + regctl baked, scanners downloaded on first use.
- **Section "When are tools fetched?"**: Lazy (default), explicit pre-warm via `regis bootstrap tools`, status via `--check` or `regis doctor`.
- **Section "Cache location"**: resolution order `$REGIS_CACHE_DIR` → `$XDG_CACHE_HOME/regis/tools/` → `~/.cache/regis/tools/`; layout `<cache>/<tool>/<version>/linux-<arch>/<tool>`.
- **Section "Air-gapped environments"**: option 1 use `:latest-full`, option 2 set `REGIS_TOOLS_MIRROR` (document mirror URL template `<mirror>/<tool>/<version>/<tool>_<version>_linux_<arch>{ext}`).
- **Section "Environment variables"**: table of 4 vars (`REGIS_CACHE_DIR`, `REGIS_TOOLS_MIRROR`, `REGIS_OFFLINE`, `REGIS_REQUIRE_COSIGN`).
- **Section "Signature verification"**: cosign best-effort, set `REGIS_REQUIRE_COSIGN=1` to enforce.
- **Section "CI cache examples"** with two YAML snippets:

GitHub Actions snippet:

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/regis/tools
    key: regis-tools-${{ hashFiles('regis/tools/manifest.yaml') }}
- run: docker run -v "$HOME/.cache/regis:/home/nonroot/.cache/regis" \
    ghcr.io/trivoallan/regis:latest analyze $IMAGE
```

GitLab CI snippet:

```yaml
cache:
  key:
    files: [regis/tools/manifest.yaml]
  paths: [.regis-cache/]
script:
  - docker run -v "$PWD/.regis-cache:/home/nonroot/.cache/regis" \
    ghcr.io/trivoallan/regis:latest analyze $IMAGE
```

- [ ] **Step 2: Add the 4 env vars to `configuration.md`**

In the `REGIS_*` table, append rows for `REGIS_CACHE_DIR`, `REGIS_TOOLS_MIRROR`, `REGIS_OFFLINE`, `REGIS_REQUIRE_COSIGN`, each linking to `tools-management.md`.

- [ ] **Step 3: Update `cli.md`**

Add a section for `regis bootstrap tools`:

```text
$ regis bootstrap tools --check
  ⏩ grype        0.112.0    not cached (will fetch on first use)
  ⏩ syft         1.44.0     not cached (will fetch on first use)
  ...

$ regis bootstrap tools
  ✓ grype        -> /home/user/.cache/regis/tools/grype/0.112.0/linux-amd64/grype
  ...

```

And document the new "Tools" section in `regis doctor`.

- [ ] **Step 4: Commit**

```bash
git add docs/website/docs/usage/tools-management.md docs/website/docs/usage/configuration.md docs/website/docs/reference/cli.md
git commit -m "docs(tools): document lazy fetch, env vars, CI cache patterns"
```

---

## Task 20: README + What's New + Renovate

**Files:**

- Modify: `README.md`
- Modify: `renovate.json` or `.github/renovate.json5` (whichever exists)

- [ ] **Step 1: Add "lazy by default" note to README**

In `README.md`, near the install / docker pull section, add:

```markdown
> **Image variants**: `:latest` is slim (~110 MB) and downloads scanner
> binaries on first use. For air-gapped CI, use `:latest-full` (~370 MB)
> which bakes everything in. See
> [Managing analyzer tools](https://trivoallan.github.io/regis/docs/usage/tools-management/).
```

- [ ] **Step 2: Add a Renovate regex manager for the manifest**

Append to the existing Renovate config (`renovate.json` or `.github/renovate.json5`):

```json
{
  "customManagers": [
    {
      "customType": "regex",
      "fileMatch": ["^regis/tools/manifest\\.yaml$"],
      "matchStrings": [
        "(?<depName>grype):\\s*\\n\\s*version:\\s*\"(?<currentValue>[^\"]+)\""
      ],
      "datasourceTemplate": "github-releases",
      "packageNameTemplate": "anchore/grype",
      "extractVersionTemplate": "^v(?<version>.+)$"
    }
  ]
}
```

Add equivalent blocks for `syft` (`anchore/syft`), `trufflehog` (`trufflesecurity/trufflehog`), `regctl` (`regclient/regclient`), `dockle` (`goodwithtech/dockle`), `hadolint` (`hadolint/hadolint`).

Renovate updates the `version:` field; CI workflow `ci-tools-manifest.yml` then catches the sha256 mismatch and the engineer recomputes via `scripts/compute_tool_hashes.sh`. (Auto-update of sha256 is out of scope for this round.)

- [ ] **Step 3: Apply the `whats-new` PR label**

This is a manual step on the PR; the script `scripts/generate_whats_new.py` will harvest the `## Summary` section automatically.

- [ ] **Step 4: Commit**

```bash
git add README.md renovate.json
git commit -m "docs(readme): announce slim/full image variants"
```

---

## Task 21: Memory bank update

**Files:**

- Modify: `docs/memory-bank/activeContext.md`
- Modify: `docs/memory-bank/progress.md`

- [ ] **Step 1: Append to `activeContext.md` Recent Changes**

```markdown
- [2026-06-XX] **Docker image size — round 3** (this PR):
  - Lazy-loaded scanner binaries (grype, syft, trufflehog, hadolint, dockle) via
    new `regis.tools` package (manifest + fetcher + cosign).
  - Switched runtime base to `gcr.io/distroless/python3-debian12:nonroot`
    (Python 3.11). Runtime user 1001 → 65532.
  - Two published variants: `:latest` (slim ~110 MB) and `:latest-full`
    (~370 MB). CI ceilings 150 MB / 400 MB.
  - New CI: `ci-tools-manifest.yml` (weekly sha256 re-check),
    `ci-tools-fetch-smoke.yml` (cold-fetch + warm-analyze).
  - Breaking: `:latest` no longer ships scanners; runtime user uid changed; no
    shell in image (debug via `:debug` tag if needed).
```

- [ ] **Step 2: Move round-3 from In Progress to Completed in `progress.md`** once the PR merges.

- [ ] **Step 3: Commit**

```bash
git add docs/memory-bank/
git commit -m "docs(memory-bank): record round-3 image trim + lazy-load fetcher"
```

---

## Final verification before opening the PR

- [ ] `pipenv run pytest` — all pass, coverage ≥ 90 %.
- [ ] `pipenv run ruff check .` — clean.
- [ ] `pipenv run ruff format --check .` — clean.
- [ ] `trunk check` — clean.
- [ ] `docker buildx build --build-arg VARIANT=slim --load -t regis:slim .` succeeds and image is <150 MB.
- [ ] `docker buildx build --build-arg VARIANT=full --load -t regis:full .` succeeds and image is <400 MB.
- [ ] `docker run --rm regis:slim bootstrap tools --check` lists 6 tools as `⏩ not cached`.
- [ ] `docker run --rm -v $PWD/.cache:/home/nonroot/.cache/regis regis:slim bootstrap tools` succeeds.
- [ ] PR labelled `whats-new` with a `## Summary` describing the breaking change.

---

## Out of scope (deferred)

- UPX-packing of `regis:latest-full` binaries (not needed once slim hits target).
- Auto-update of sha256 in Renovate flow (version bump triggers CI mismatch; engineer recomputes manually).
- `:debug` image variant (decide post-launch based on debugging friction reports).
- Custom-built `distroless/cc-debian12` + Python 3.14 (re-evaluate if <100 MB becomes a goal).
- Splitting analyzers across more images (orthogonal to size).
