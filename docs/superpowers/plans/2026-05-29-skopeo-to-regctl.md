# skopeo → regctl Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `skopeo` external binary with `regctl` across all five
analyzer call sites, rename the `skopeo` analyzer to `oci`, redesign its output
schema, and drop skopeo from the Docker image.

**Architecture:** A single new wrapper `regis/utils/regctl.py` centralizes regctl
invocation + credential injection + reference building. All five analyzers
(`oci`, `freshness`, `versioning`, `size`, `hadolint`) route their registry
inspection through it, replacing two duplicated `_run_skopeo` helpers and three
inline `subprocess.run(["skopeo", …])` blocks. The Docker image fetches regctl
as a static binary (same pattern as hadolint/dockle) and drops the skopeo apt
layer.

**Tech Stack:** Python 3.14, Click, pytest, JSON Schema (draft-07), JSON Logic,
Docker multi-stage build, Trunk (lint/format), regctl `v0.11.5`.

**Spec:** `docs/superpowers/specs/2026-05-29-skopeo-to-regctl-design.md`

**Conventions for every task below:**
- Fast test loop: `pipenv run pytest <path> --no-cov`. Full gate before PR:
  `pipenv run pytest` (fails under 90 % coverage).
- Commit messages: Conventional Commits with mandatory scope (see spec §10).
  Trunk's pre-commit hook auto-fixes; re-stage and commit the produced changes if
  the first `git commit` is blocked.
- Patch targets in tests: patch at the source module
  (`regis.utils.regctl.subprocess`, `regis.analyzers.<name>.*`), never
  `regis.cli.*`.

---

## Task 1: Verify regctl behavior and capture fixtures (spike)

This resolves spec Open Questions 1, 2, 4, 6 empirically so later TDD uses real
output shapes, not guesses. No production code changes — this produces a
reference note and saved fixtures.

**Files:**
- Create: `tests/fixtures/regctl/` (captured JSON outputs)
- Create: `docs/superpowers/plans/2026-05-29-regctl-probe-notes.md` (findings)

- [ ] **Step 1: Install regctl locally**

```bash
# macOS
brew install regclient   # provides `regctl`
# or download the pinned binary:
#   curl -sSfL https://github.com/regclient/regclient/releases/download/v0.11.5/regctl-darwin-arm64 -o /usr/local/bin/regctl && chmod +x /usr/local/bin/regctl
regctl version
```
Expected: prints a version (note the exact invocation — `version` vs `--version`).

- [ ] **Step 2: Probe a multi-arch public image and capture outputs**

Run each command against a stable public image and save stdout verbatim:

```bash
mkdir -p tests/fixtures/regctl
REF=docker.io/library/alpine:3.20

regctl manifest get "$REF" --format raw-body            > tests/fixtures/regctl/index_raw.json
regctl manifest get "$REF" --platform linux/amd64 --format raw-body > tests/fixtures/regctl/manifest_amd64_raw.json
regctl image inspect "$REF" --platform linux/amd64       > tests/fixtures/regctl/image_inspect_amd64.json
regctl image inspect "$REF" --platform linux/amd64 --format '{{jsonPretty .}}' > tests/fixtures/regctl/image_inspect_amd64_pretty.json
regctl tag ls docker.io/library/alpine                   > tests/fixtures/regctl/tag_ls.txt
```

- [ ] **Step 3: Confirm the field shapes and record them**

In `2026-05-29-regctl-probe-notes.md`, record concrete answers:
- Default vs `--format '{{jsonPretty .}}'` output of `image inspect` — which is
  valid JSON? Where are `created`, `config.User`, `config.Env`,
  `config.ExposedPorts`, `config.Labels`, `history`, `architecture`, `os`?
- `manifest get --format raw-body` on a multi-arch ref: does it return the
  index (with `manifests[]`) so `mediaType`-based branching still works?
- `manifest get --platform … --format raw-body`: does it return a single
  manifest with `layers[].size`, `config.size`?
- `tag ls`: newline-per-tag plain text? Confirm `splitlines()` parses it.
- Does `docker.io/library/alpine` work, or is `registry-1.docker.io`
  normalization still needed? (Open Q1)
- Does `regctl version` exit 0 and print on stdout? (Open Q4)
- Is `RepoTags` (skopeo) == full repo tag list, confirming `tag ls` can replace
  versioning's second call? (Open Q6)

- [ ] **Step 4: Commit the fixtures and notes**

```bash
git add tests/fixtures/regctl docs/superpowers/plans/2026-05-29-regctl-probe-notes.md
git commit -m "test(analyzer/skopeo): capture regctl output fixtures for migration"
```

> If any probe answer contradicts the spec's command mapping (§3), STOP and
> reconcile the spec before continuing — the remaining tasks assume these shapes.

---

## Task 2: regctl subprocess wrapper

**Files:**
- Create: `regis/utils/regctl.py`
- Test: `tests/utils/test_regctl.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/utils/test_regctl.py
"""Tests for the shared regctl subprocess wrapper."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from regis.analyzers.base import AnalyzerError
from regis.registry.client import RegistryClient
from regis.utils.regctl import image_ref, run_regctl


def _client(username=None, password=None, registry="docker.io"):
    c = MagicMock(spec=RegistryClient)
    c.registry = registry
    c.username = username
    c.password = password
    return c


def test_image_ref_tag():
    assert image_ref("docker.io", "library/alpine", "3.20") == "docker.io/library/alpine:3.20"


def test_image_ref_digest_uses_at_separator():
    ref = image_ref("docker.io", "library/alpine", "sha256:abc")
    assert ref == "docker.io/library/alpine@sha256:abc"


def test_image_ref_normalizes_dockerhub():
    assert image_ref("registry-1.docker.io", "library/alpine", "3.20").startswith("docker.io/")


@patch("regis.utils.regctl.subprocess.run")
def test_run_regctl_no_creds(mock_run):
    mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="OUT", stderr="")
    out = run_regctl(_client(), ["tag", "ls", "docker.io/library/alpine"])
    assert out == "OUT"
    cmd = mock_run.call_args.args[0]
    assert cmd[0] == "regctl"
    assert "--host" not in cmd


@patch("regis.utils.regctl.subprocess.run")
def test_run_regctl_inline_creds(mock_run):
    mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="OUT", stderr="")
    run_regctl(_client("alice", "s3cret"), ["tag", "ls", "x"])
    cmd = mock_run.call_args.args[0]
    assert "--host" in cmd
    host_val = cmd[cmd.index("--host") + 1]
    assert host_val == "reg=docker.io,user=alice,pass=s3cret"


@patch("regis.utils.regctl.subprocess.run")
def test_run_regctl_comma_password_uses_docker_config(mock_run):
    mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="OUT", stderr="")
    run_regctl(_client("alice", "pa,ss"), ["tag", "ls", "x"])
    cmd = mock_run.call_args.args[0]
    env = mock_run.call_args.kwargs["env"]
    assert "--host" not in cmd
    assert "DOCKER_CONFIG" in env


@patch("regis.utils.regctl.subprocess.run", side_effect=FileNotFoundError())
def test_run_regctl_missing_binary_raises(mock_run):
    with pytest.raises(AnalyzerError, match="regctl not found"):
        run_regctl(_client(), ["version"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pipenv run pytest tests/utils/test_regctl.py --no-cov -v`
Expected: FAIL — `ModuleNotFoundError: regis.utils.regctl`.

- [ ] **Step 3: Implement the wrapper**

```python
# regis/utils/regctl.py
"""Subprocess wrapper for the regctl OCI registry client.

Centralizes regctl invocation, credential injection, and reference building for
every analyzer that inspects remote images. Replaces the per-analyzer skopeo
wrappers.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import subprocess  # nosec B404
import tempfile
from typing import TYPE_CHECKING

from regis.analyzers.base import AnalyzerError

if TYPE_CHECKING:
    from regis.registry.client import RegistryClient

logger = logging.getLogger(__name__)

#: Default timeout for regctl calls (seconds).
DEFAULT_TIMEOUT = 60


def image_ref(registry: str, repository: str, ref: str) -> str:
    """Build a regctl image reference (no ``docker://`` scheme).

    Uses ``@`` for digests (``sha256:…``) and ``:`` for tags. Normalizes the
    Docker Hub API host to ``docker.io``.
    """
    if registry == "registry-1.docker.io":
        registry = "docker.io"
    separator = "@" if ref.startswith("sha256:") else ":"
    return f"{registry}/{repository}{separator}{ref}"


def _temp_docker_config(client: RegistryClient) -> str:
    """Write a temp Docker config.json with the client's credentials.

    Used when credentials contain a comma, which would break regctl's
    ``--host`` comma-separated ``key=val`` parsing. Returns the config dir to
    pass via ``DOCKER_CONFIG``.
    """
    auth = base64.b64encode(f"{client.username}:{client.password}".encode()).decode()
    config = {"auths": {client.registry: {"auth": auth}}}
    tmpdir = tempfile.mkdtemp(prefix="regis-regctl-")
    with open(os.path.join(tmpdir, "config.json"), "w", encoding="utf-8") as handle:
        json.dump(config, handle)
    return tmpdir


def run_regctl(
    client: RegistryClient,
    args: list[str],
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """Run regctl with *args*, injecting credentials if present.

    Credentials are passed inline via the global ``--host`` flag. If a
    credential contains a comma, they are written to a per-call temporary Docker
    config and passed via ``DOCKER_CONFIG`` instead (thread-safe: a fresh
    tempdir per call).

    Args:
        client: Registry client carrying the host and optional credentials.
        args: regctl subcommand and arguments, e.g. ``["image", "inspect", ref]``.
        timeout: Subprocess timeout in seconds.

    Returns:
        The command's stdout.

    Raises:
        AnalyzerError: if regctl is not installed.
        subprocess.CalledProcessError: if regctl exits non-zero.
    """
    cmd = ["regctl"]
    env = dict(os.environ)

    if client.username and client.password:
        if "," in client.username or "," in client.password:
            env["DOCKER_CONFIG"] = _temp_docker_config(client)
        else:
            cmd += [
                "--host",
                f"reg={client.registry},user={client.username},pass={client.password}",
            ]

    cmd += args
    logger.debug("Running regctl: %s", " ".join(c for c in cmd if "pass=" not in c))
    try:
        result = subprocess.run(  # nosec B603
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
            env=env,
        )
        return result.stdout
    except FileNotFoundError:
        raise AnalyzerError(
            "regctl not found. Ensure it is installed and in PATH."
        ) from None
```

Create `tests/utils/__init__.py` if the directory needs it (mirror existing test
package layout — check `tests/commands/` for the convention).

- [ ] **Step 4: Run tests to verify they pass**

Run: `pipenv run pytest tests/utils/test_regctl.py --no-cov -v`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add regis/utils/regctl.py tests/utils/
git commit -m "feat(analyzer): add shared regctl subprocess wrapper"
```

---

## Task 3: New `oci` analyzer output schema

**Files:**
- Create: `regis/schemas/analyzer/oci.schema.json`
- Delete (in Task 4): `regis/schemas/analyzer/skopeo.schema.json`
- Test: `tests/test_oci_analyzer.py` (schema-validity check; analyzer tests added in Task 4)

- [ ] **Step 1: Write the new schema**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "oci.output",
  "type": "object",
  "required": ["analyzer", "repository", "tag", "platforms"],
  "properties": {
    "analyzer": {
      "type": "string",
      "const": "oci",
      "description": "Unique identifier for the OCI metadata analyzer."
    },
    "repository": { "type": "string", "description": "The image repository that was analyzed." },
    "tag": { "type": "string", "description": "The image tag that was analyzed." },
    "platforms": {
      "type": "array",
      "description": "List of platform variants available for this tag.",
      "items": {
        "type": "object",
        "required": ["architecture", "os"],
        "properties": {
          "architecture": { "type": "string", "description": "Processor architecture (e.g. 'amd64')." },
          "os": { "type": "string", "description": "Operating system (e.g. 'linux')." },
          "variant": { "type": ["string", "null"], "description": "Architecture variant (e.g. 'v7')." },
          "digest": { "type": "string", "description": "Manifest digest for this variant." },
          "created": { "type": ["string", "null"], "description": "ISO timestamp of variant creation." },
          "labels": {
            "type": "object",
            "description": "OCI labels for this variant.",
            "additionalProperties": { "type": "string" }
          },
          "layers_count": { "type": "integer", "minimum": 0, "description": "Number of layers." },
          "size": { "type": "integer", "minimum": 0, "description": "Total image size in bytes (config + layers)." },
          "user": { "type": ["string", "null"], "description": "Default user from image config." },
          "exposed_ports": { "type": "array", "items": { "type": "string" }, "description": "Exposed ports (e.g. '80/tcp')." },
          "env": { "type": "array", "items": { "type": "string" }, "description": "Environment variables (KEY=VALUE)." }
        }
      }
    },
    "tags": { "type": "array", "items": { "type": "string" }, "description": "Tags in the repository." }
  },
  "additionalProperties": false,
  "$id": "https://trivoallan.github.io/regis/schemas/analyzer/oci.schema.json"
}
```

Note vs the old schema: `size`, `exposed_ports`, `env` are now declared
explicitly (fixing the latent gap — the rules reference them); the top-level
`inspect` raw dump is removed.

- [ ] **Step 2: Write a schema-validity test**

```python
# tests/test_oci_analyzer.py
"""Tests for the oci analyzer (formerly skopeo)."""

from __future__ import annotations

import json
from importlib import resources

import jsonschema


def test_oci_schema_is_valid_draft7():
    schema_text = (
        resources.files("regis.schemas").joinpath("analyzer/oci.schema.json").read_text()
    )
    schema = json.loads(schema_text)
    jsonschema.Draft7Validator.check_schema(schema)
    assert schema["properties"]["analyzer"]["const"] == "oci"
```

- [ ] **Step 3: Run it**

Run: `pipenv run pytest tests/test_oci_analyzer.py --no-cov -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add regis/schemas/analyzer/oci.schema.json tests/test_oci_analyzer.py
git commit -m "feat(schema): add redesigned oci analyzer output schema"
```

---

## Task 4: Rename + rewrite the `skopeo` analyzer to `oci`

This is the breaking commit (slug rename + schema change). Use the captured
fixtures (Task 1) to build accurate mocks.

**Files:**
- Create: `regis/analyzers/oci.py` (rewrite of `skopeo.py`)
- Delete: `regis/analyzers/skopeo.py`, `regis/schemas/analyzer/skopeo.schema.json`
- Modify: `pyproject.toml` (entry point), `regis/playbooks/default/playbook.yaml`
- Test: `tests/test_oci_analyzer.py` (extend), delete `tests/test_skopeo_analyzer.py` + `tests/test_analyzer_skopeo.py`

- [ ] **Step 1: Write failing analyzer tests**

Append to `tests/test_oci_analyzer.py`. Build `INDEX_RAW`, `MANIFEST_RAW`,
`IMAGE_INSPECT` constants from the Task-1 fixtures (load them or inline a
trimmed copy).

```python
from unittest.mock import patch

from regis.analyzers.oci import OciAnalyzer
from regis.registry.client import RegistryClient
from unittest.mock import MagicMock


def _client():
    c = MagicMock(spec=RegistryClient)
    c.registry = "docker.io"
    c.username = None
    c.password = None
    return c


def test_oci_name_and_schema():
    a = OciAnalyzer()
    assert a.name == "oci"
    assert a.schema_file == "analyzer/oci.schema.json"


def test_oci_default_rules_use_oci_paths():
    rules = OciAnalyzer.default_rules()
    blob = json.dumps(rules)
    assert "results.oci." in blob
    assert "results.skopeo." not in blob


@patch("regis.analyzers.oci.run_regctl")
def test_oci_single_platform_report_validates(mock_regctl):
    # Map (args-tuple) -> stdout using captured fixtures.
    def _dispatch(client, args, *a, **k):
        if args[:2] == ["manifest", "get"] and "--platform" not in args:
            return SINGLE_MANIFEST_RAW         # not an index
        if args[:2] == ["manifest", "get"]:
            return MANIFEST_RAW                 # per-platform manifest w/ layers
        if args[:2] == ["image", "inspect"]:
            return IMAGE_INSPECT                # config blob
        if args[:2] == ["tag", "ls"]:
            return "3.19\n3.20\nlatest\n"
        raise AssertionError(args)
    mock_regctl.side_effect = _dispatch

    report = OciAnalyzer().analyze(_client(), "library/alpine", "3.20")
    OciAnalyzer().validate(report)             # must conform to oci.schema.json
    assert report["analyzer"] == "oci"
    plat = report["platforms"][0]
    assert plat["layers_count"] >= 1
    assert isinstance(plat["size"], int)
    assert isinstance(plat["env"], list)
    assert isinstance(plat["exposed_ports"], list)
    assert report["tags"] == ["3.19", "3.20", "latest"]
```

- [ ] **Step 2: Run to verify failure**

Run: `pipenv run pytest tests/test_oci_analyzer.py --no-cov -v`
Expected: FAIL — `ModuleNotFoundError: regis.analyzers.oci`.

- [ ] **Step 3: Create `regis/analyzers/oci.py`**

Start from `regis/analyzers/skopeo.py` and apply these transforms:
1. Module docstring + class: `SkopeoAnalyzer` → `OciAnalyzer`; `name = "oci"`;
   `schema_file = "analyzer/oci.schema.json"`.
2. Remove the local `_run_skopeo`; import `from regis.utils.regctl import
   run_regctl, image_ref`.
3. In `default_rules()`, replace every `results.skopeo.` with `results.oci.`
   (8 rules — paths only; slugs and messages otherwise unchanged).
4. Rewrite the regctl-calling methods. `analyze()` becomes:

```python
def analyze(self, client, repository, tag, platform=None):
    """Return per-platform OCI metadata and the repository tag list."""
    registry = client.registry
    raw = run_regctl(client, ["manifest", "get",
                              image_ref(registry, repository, tag),
                              "--format", "raw-body"])
    manifest = json.loads(raw)
    media_type = manifest.get("mediaType", "")
    platforms: list[dict[str, Any]] = []

    if platform:
        os_name, arch = (platform.split("/", 1) if "/" in platform else ("linux", platform))
        platforms.append(self._inspect_platform(client, registry, repository, tag,
                                                 {"os": os_name, "architecture": arch}))
    elif media_type in _INDEX_TYPES:
        entries = manifest.get("manifests", [])
        max_workers = min(10, len(entries) or 1)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self._inspect_platform, client, registry, repository,
                                entry.get("digest", ""), entry.get("platform", {}))
                for entry in entries
            ]
            for future in futures:
                try:
                    platforms.append(future.result())
                except Exception as exc:  # noqa: BLE001
                    logger.error("Failed to inspect platform: %s", exc)
    else:
        platforms.append(self._inspect_platform(client, registry, repository, tag, {}))

    tags: list[str] = []
    try:
        tags_out = run_regctl(client, ["tag", "ls", f"{_norm(registry)}/{repository}"])
        tags = [t for t in tags_out.splitlines() if t.strip()]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not fetch tag list for %s: %s", repository, exc)

    return {
        "analyzer": self.name,
        "repository": repository,
        "tag": tag,
        "platforms": platforms,
        "tags": tags,
    }
```

5. Rewrite `_inspect_platform` to use two regctl calls — `image inspect` for the
   config blob and `manifest get --platform` for layers/size:

```python
def _inspect_platform(self, client, registry, repository, ref, platform_info):
    """Inspect one platform: config blob (regctl image inspect) + manifest."""
    result: dict[str, Any] = {
        "architecture": platform_info.get("architecture", "unknown"),
        "os": platform_info.get("os", "unknown"),
    }
    if "variant" in platform_info:
        result["variant"] = platform_info["variant"]

    image_reference = image_ref(registry, repository, ref)
    plat = None
    if result["architecture"] != "unknown" and result["os"] != "unknown":
        plat = f"{result['os']}/{result['architecture']}"
        if result.get("variant"):
            plat = f"{plat}/{result['variant']}"

    # 1. Config blob: created, labels, user, env, exposed_ports, arch, os.
    try:
        args = ["image", "inspect", image_reference, "--format", "{{jsonPretty .}}"]
        if plat:
            args += ["--platform", plat]
        config = json.loads(run_regctl(client, args))
        cfg = config.get("config", {}) or {}
        result["created"] = config.get("created")
        result["labels"] = cfg.get("Labels") or {}
        result["user"] = cfg.get("User", "") or ""
        result["env"] = cfg.get("Env", []) or []
        result["exposed_ports"] = list((cfg.get("ExposedPorts") or {}).keys())
        if result["architecture"] == "unknown":
            result["architecture"] = config.get("architecture", "unknown")
        if result["os"] == "unknown":
            result["os"] = config.get("os", "unknown")
    except Exception:  # noqa: BLE001
        logger.debug("regctl image inspect failed for %s", image_reference, exc_info=True)
        result.setdefault("labels", {})
        result.setdefault("user", "unknown")
        result.setdefault("env", [])
        result.setdefault("exposed_ports", [])

    # 2. Manifest: layers_count, size, digest.
    try:
        m_args = ["manifest", "get", image_reference, "--format", "raw-body"]
        if plat:
            m_args += ["--platform", plat]
        manifest = json.loads(run_regctl(client, m_args))
        layers = manifest.get("layers", [])
        result["layers_count"] = len(layers)
        config_size = (manifest.get("config", {}) or {}).get("size", 0)
        result["size"] = config_size + sum(layer.get("size", 0) for layer in layers)
        if not result.get("digest"):
            result["digest"] = ref if ref.startswith("sha256:") else manifest.get("digest", "")
    except Exception:  # noqa: BLE001
        logger.debug("regctl manifest get failed for %s", image_reference, exc_info=True)
        result.setdefault("layers_count", 0)
        result.setdefault("size", 0)

    return result
```

6. Add a tiny module-local helper used above:

```python
def _norm(registry: str) -> str:
    return "docker.io" if registry == "registry-1.docker.io" else registry
```

(Keep `_INDEX_TYPES`; drop `DEFAULT_TIMEOUT`/`subprocess`/`AnalyzerError` imports
that are now only used by `run_regctl`. Keep `AnalyzerError` only if `analyze`
still raises it — in this rewrite it no longer does, so remove the unused
import.)

- [ ] **Step 4: Delete the old files and switch the entry point**

```bash
git rm regis/analyzers/skopeo.py regis/schemas/analyzer/skopeo.schema.json \
       tests/test_skopeo_analyzer.py tests/test_analyzer_skopeo.py
```

In `pyproject.toml`, change line 32:
```toml
oci = "regis.analyzers.oci:OciAnalyzer"
```
(was `skopeo = "regis.analyzers.skopeo:SkopeoAnalyzer"`). Reinstall so the entry
point is picked up: `pipenv run pip install -e . --no-deps -q`.

In `regis/playbooks/default/playbook.yaml`, change both `provider: skopeo` to
`provider: oci` (lines 22 and 116).

- [ ] **Step 5: Run tests to verify they pass**

Run: `pipenv run pytest tests/test_oci_analyzer.py --no-cov -v`
Expected: PASS.

- [ ] **Step 6: Commit (breaking)**

```bash
git add -A
git commit -m "feat(analyzer/skopeo)!: replace skopeo analyzer with regctl-based oci analyzer

BREAKING CHANGE: the 'skopeo' analyzer is renamed to 'oci'. Rule paths
results.skopeo.* become results.oci.* and playbooks must use provider: oci.
The output schema is redesigned (raw 'inspect' dump removed; size/exposed_ports/
env now declared)."
```

---

## Task 5: Migrate `freshness` analyzer

**Files:**
- Modify: `regis/analyzers/freshness.py` (`_get_created_date`)
- Test: `tests/test_freshness.py` (create if absent; otherwise extend the file
  that currently tests freshness — confirm with `grep -rl Freshness tests/`)

- [ ] **Step 1: Write the failing test**

```python
@patch("regis.analyzers.freshness.run_regctl")
def test_get_created_date_reads_config_created(mock_regctl):
    from regis.analyzers.freshness import _get_created_date
    mock_regctl.return_value = '{"created": "2026-01-02T03:04:05Z", "config": {}}'
    c = MagicMock(spec=RegistryClient); c.registry = "docker.io"; c.username = None; c.password = None
    assert _get_created_date(c, "library/alpine", "3.20") == "2026-01-02T03:04:05Z"
    args = mock_regctl.call_args.args[1]
    assert args[:2] == ["image", "inspect"]
    assert "--platform" in args and "linux/amd64" in args
```

- [ ] **Step 2: Run to verify failure**

Run: `pipenv run pytest tests/test_freshness.py --no-cov -v`
Expected: FAIL (imports `run_regctl` from freshness, which isn't wired yet).

- [ ] **Step 3: Rewrite `_get_created_date`**

```python
from regis.utils.regctl import image_ref, run_regctl

def _get_created_date(client: RegistryClient, repository: str, tag: str) -> str | None:
    """Extract the creation date from an image config using regctl."""
    ref = image_ref(client.registry, repository, tag)
    try:
        out = run_regctl(
            client,
            ["image", "inspect", ref, "--platform", "linux/amd64", "--format", "{{jsonPretty .}}"],
        )
        return json.loads(out).get("created")  # type: ignore[no-any-return]
    except Exception:
        logger.debug("regctl image inspect failed for %s", ref, exc_info=True)
        return None
```

Remove the now-unused `subprocess` import if nothing else in the file uses it
(check first — `grep -n subprocess regis/analyzers/freshness.py`).

- [ ] **Step 4: Run to verify pass**

Run: `pipenv run pytest tests/test_freshness.py --no-cov -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add regis/analyzers/freshness.py tests/test_freshness.py
git commit -m "feat(analyzer/freshness): read image created date via regctl"
```

---

## Task 6: Migrate `versioning` analyzer

**Files:**
- Modify: `regis/analyzers/versioning.py` (`analyze`)
- Test: `tests/test_versioning.py`

- [ ] **Step 1: Write the failing test**

```python
@patch("regis.analyzers.versioning.run_regctl")
def test_versioning_uses_tag_ls_and_derives_aliases(mock_regctl):
    mock_regctl.return_value = "1.0\n1.1\n1.1-glibc\nlatest\n"
    c = MagicMock(spec=RegistryClient); c.registry="docker.io"; c.username=None; c.password=None
    report = VersioningAnalyzer().analyze(c, "library/demo", "1.1")
    # tag ls is the only registry call now (RepoTags derived from it)
    assert mock_regctl.call_count == 1
    args = mock_regctl.call_args.args[1]
    assert args[:2] == ["tag", "ls"]
    assert "latest" in [a for p in report["patterns"] for a in p["examples"]] or report["patterns"]
```

(Adjust the assertion on `report` structure to match the analyzer's real schema
fields — inspect `regis/schemas/analyzer/versioning.schema.json` first.)

- [ ] **Step 2: Run to verify failure**

Run: `pipenv run pytest tests/test_versioning.py --no-cov -v`
Expected: FAIL.

- [ ] **Step 3: Rewrite the registry calls in `analyze`**

Replace the `skopeo list-tags` block (lines ~195–213):

```python
from regis.utils.regctl import run_regctl

registry = client.registry
repo_ref = f"{'docker.io' if registry == 'registry-1.docker.io' else registry}/{repository}"
try:
    tags_out = run_regctl(client, ["tag", "ls", repo_ref])
    tags = [t for t in tags_out.splitlines() if t.strip()]
except Exception as exc:  # noqa: BLE001
    msg = f"Failed to list tags via regctl for {repo_ref}: {exc}"
    logger.error(msg)
    raise AnalyzerError(msg) from exc
```

Then delete the separate `skopeo inspect` block (lines ~268–300) that fetched
`RepoTags`, and replace its consumers with the already-listed `tags`:

```python
# RepoTags == the full repository tag list, which we already have.
repo_tags = tags
aliases = sorted(t for t in repo_tags if t != tag)
```

Keep the downstream `release_lines` logic that uses `repo_tags` unchanged.
Remove the now-unused `subprocess`/`json` imports only if nothing else needs
them (check first).

- [ ] **Step 4: Run to verify pass**

Run: `pipenv run pytest tests/test_versioning.py --no-cov -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add regis/analyzers/versioning.py tests/test_versioning.py
git commit -m "feat(analyzer/versioning): list tags and derive aliases via regctl"
```

---

## Task 7: Migrate `size` analyzer

**Files:**
- Modify: `regis/analyzers/size.py` (remove `_run_skopeo`, both `inspect --raw`)
- Test: `tests/test_size.py`

- [ ] **Step 1: Write the failing test**

```python
@patch("regis.analyzers.size.run_regctl")
def test_size_single_manifest(mock_regctl):
    mock_regctl.return_value = json.dumps({
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {"size": 100},
        "layers": [{"size": 10}, {"size": 20}],
    })
    c = MagicMock(spec=RegistryClient); c.registry="docker.io"; c.username=None; c.password=None
    report = SizeAnalyzer().analyze(c, "library/alpine", "3.20")
    args = mock_regctl.call_args.args[1]
    assert args[:2] == ["manifest", "get"] and "raw-body" in args
    # assert on the report's size field per size.schema.json
```

- [ ] **Step 2: Run to verify failure**

Run: `pipenv run pytest tests/test_size.py --no-cov -v`
Expected: FAIL.

- [ ] **Step 3: Rewrite `size.py`**

Delete the `_run_skopeo` staticmethod (lines ~32–39). Add
`from regis.utils.regctl import image_ref, run_regctl`. Replace both
`self._run_skopeo(client, ["inspect", "--raw", target])` calls (lines ~55 and
~160) with:

```python
raw_stdout = run_regctl(
    client,
    ["manifest", "get", image_ref(registry, repository, tag), "--format", "raw-body"],
)
```

For the multi-arch branch (line ~160), `tag` may be a per-platform digest —
build the ref with `image_ref(registry, repository, <digest>)` exactly as that
branch already derives its target. Drop the `target = f"docker://…"` lines and
the `registry-1.docker.io → docker.io` block (now handled by `image_ref`).
Remove the unused `subprocess` import if nothing else uses it.

- [ ] **Step 4: Run to verify pass**

Run: `pipenv run pytest tests/test_size.py --no-cov -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add regis/analyzers/size.py tests/test_size.py
git commit -m "feat(analyzer/size): fetch manifests via regctl"
```

---

## Task 8: Migrate `hadolint` analyzer

**Files:**
- Modify: `regis/analyzers/hadolint.py` (the `cmd_skopeo` config fetch block)
- Test: `tests/test_hadolint.py`

- [ ] **Step 1: Write the failing test**

```python
@patch("regis.analyzers.hadolint.run_regctl")
def test_hadolint_fetches_history_via_regctl(mock_regctl):
    mock_regctl.return_value = json.dumps({
        "config": {},
        "history": [{"created_by": "RUN apk add curl"}],
    })
    c = MagicMock(spec=RegistryClient); c.registry="docker.io"; c.username=None; c.password=None
    # call the method/path that builds the pseudo-Dockerfile; assert it used
    # image inspect and consumed history. Match the analyzer's real entry point.
    args_after = mock_regctl.call_args.args[1] if mock_regctl.call_args else []
    # (fill in per the analyzer's actual analyze() signature/flow)
```

(Read `regis/analyzers/hadolint.py` `analyze()` fully first to target the right
call path; the test asserts `run_regctl` is called with
`["image", "inspect", …]` and that `history` drives the linted Dockerfile.)

- [ ] **Step 2: Run to verify failure**

Run: `pipenv run pytest tests/test_hadolint.py --no-cov -v`
Expected: FAIL.

- [ ] **Step 3: Rewrite the config fetch (lines ~73–96)**

```python
from regis.utils.regctl import image_ref, run_regctl

os_name, arch = (
    (platform.split("/", 1) if platform and "/" in platform
     else ("linux", platform) if platform else ("linux", "amd64"))
)
ref = image_ref(registry, repository, tag)
try:
    out = run_regctl(
        client,
        ["image", "inspect", ref, "--platform", f"{os_name}/{arch}", "--format", "{{jsonPretty .}}"],
    )
    config = json.loads(out)
except AnalyzerError:
    raise
except Exception as exc:  # noqa: BLE001
    msg = f"Failed to fetch config for {ref}: {exc}"
    logger.error(msg)
    raise AnalyzerError(msg) from exc

history = config.get("history", [])
```

The downstream `history`-based pseudo-Dockerfile reconstruction is unchanged
(regctl's config blob exposes `history` in the same shape as skopeo's
`inspect --config`). Remove the unused `subprocess` import if now unused.

- [ ] **Step 4: Run to verify pass**

Run: `pipenv run pytest tests/test_hadolint.py --no-cov -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add regis/analyzers/hadolint.py tests/test_hadolint.py
git commit -m "feat(analyzer/hadolint): fetch image config history via regctl"
```

---

## Task 9: Update the `doctor` command

**Files:**
- Modify: `regis/commands/doctor.py:13`
- Test: `tests/commands/test_doctor.py`

- [ ] **Step 1: Update the failing test**

In `tests/commands/test_doctor.py`, change the expected tool list / assertions
from `skopeo` to `regctl`:

```python
def test_doctor_lists_regctl(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}")
    # ... invoke doctor, assert "regctl" appears and "skopeo" does not
```

- [ ] **Step 2: Run to verify failure**

Run: `pipenv run pytest tests/commands/test_doctor.py --no-cov -v`
Expected: FAIL.

- [ ] **Step 3: Edit `_REQUIRED_TOOLS`**

```python
_REQUIRED_TOOLS: list[tuple[str, str]] = [
    ("trivy", "--version"),
    ("regctl", "version"),
    ("hadolint", "--version"),
    ("dockle", "--version"),
]
```
(Use `version`, not `--version`, per the Task-1 probe. If the probe showed
`regctl version` writes to stderr or needs `--version`, use what the probe
recorded.)

- [ ] **Step 4: Run to verify pass**

Run: `pipenv run pytest tests/commands/test_doctor.py --no-cov -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add regis/commands/doctor.py tests/commands/test_doctor.py
git commit -m "feat(cli)!: doctor checks for regctl instead of skopeo

BREAKING CHANGE: regis now requires the 'regctl' binary on PATH instead of 'skopeo'."
```

---

## Task 10: Dockerfile — fetch regctl, drop skopeo apt layer

**Files:**
- Modify: `Dockerfile`

No unit test; verified by image build (Task 12 full check).

- [ ] **Step 1: Pin the version in the tools-fetcher ENV (line ~52–53)**

```dockerfile
ENV HADOLINT_VERSION=2.12.0 \
    DOCKLE_VERSION=0.4.15 \
    REGCTL_VERSION=0.11.5
```

- [ ] **Step 2: Add a regctl fetch step in the tools-fetcher stage (after Dockle, before `USER curl_user`)**

```dockerfile
# regctl (static binary, like hadolint)
RUN case "$TARGETARCH" in \
      amd64|arm64) regctl_arch="$TARGETARCH" ;; \
      *) echo "Unsupported TARGETARCH: $TARGETARCH" >&2; exit 1 ;; \
    esac && \
    curl -sSfL "https://github.com/regclient/regclient/releases/download/v${REGCTL_VERSION}/regctl-linux-${regctl_arch}" \
      -o /tools/regctl && \
    chmod +x /tools/regctl
```

- [ ] **Step 3: Copy regctl in the final stage (after the dockle COPY, line ~126)**

```dockerfile
COPY --from=tools-fetcher /tools/regctl /usr/local/bin/regctl
```

- [ ] **Step 4: Remove skopeo from the runtime apt install (line ~109–114)**

```dockerfile
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
      ca-certificates && \
    rm -rf /var/lib/apt/lists/*
```
(Drop the `skopeo \` line; update the preceding comment that explains the apt
layer.)

- [ ] **Step 5: Build and smoke-test the image**

```bash
docker build -t regis:regctl-test .
docker run --rm regis:regctl-test regctl version
docker run --rm regis:regctl-test regis doctor
```
Expected: `regctl version` prints; `regis doctor` shows `✓ regctl` and no
`skopeo`. (If skopeo still appears as required, a call site was missed.)

- [ ] **Step 6: Commit**

```bash
git add Dockerfile
git commit -m "build!: replace skopeo apt layer with regctl static binary

BREAKING CHANGE: the runtime image no longer ships skopeo; regctl replaces it."
```

---

## Task 11: Docs, dashboard, and project instructions

**Files:**
- Modify (rename dir): `docs/website/docs/reference/rules/skopeo/` → `.../rules/oci/`
- Modify: `docs/website/docs/concepts/playbooks.md`, `concepts/rules.md`,
  `reference/analyzers/skopeo.md` (→ `oci.md`),
  `reference/schemas/analyzer/skopeo.schema.md` (→ `oci...`),
  `usage/troubleshooting.md`, `usage/custom-playbook.md`,
  `reference/analyzers/index.md`
- Modify: `apps/dashboard/src/components/AnalyzerSection.tsx`,
  `apps/dashboard/src/components/Dashboard/AnalyzerCoverageCard.tsx`
- Modify: `regis/rules/evaluator.py` (doc-comment example),
  `.claude/skills/create-playbook/**` (skopeo → oci, required-binary list),
  `CLAUDE.md`, project `README`

Do NOT touch `docs/website/versioned_docs/version-v0.31.0/**` (frozen snapshots).

- [ ] **Step 1: Mechanical replacements**

```bash
# results.skopeo.* -> results.oci.* and provider/name references (excluding versioned_docs)
grep -rl "results\.skopeo\|provider: skopeo\|analyzer/skopeo\|skopeo analyzer" \
  --include='*.md' --include='*.mdx' --include='*.tsx' --include='*.py' --include='*.yaml' \
  docs/website/docs apps/dashboard regis .claude CLAUDE.md README* 2>/dev/null
```
Replace `results.skopeo.` → `results.oci.`, `provider: skopeo` → `provider: oci`,
and rename the rules doc directory:
```bash
git mv docs/website/docs/reference/rules/skopeo docs/website/docs/reference/rules/oci
git mv docs/website/docs/reference/analyzers/skopeo.md docs/website/docs/reference/analyzers/oci.md
```

- [ ] **Step 2: Update required-binary mentions**

In `CLAUDE.md`, project `README`, the docs install/usage pages, and the
`create-playbook` skill: remove `skopeo`, add `regctl` from the
"required external binaries (must be on PATH)" list.

- [ ] **Step 3: Verify the docs build and dashboard typecheck**

```bash
pnpm --filter @regis/dashboard build
```
Expected: build succeeds with no `skopeo` symbol errors. Manually grep to
confirm no stray `results.skopeo` remain outside `versioned_docs`:
```bash
grep -rn "results\.skopeo" docs/website/docs apps/dashboard regis && echo "LEFTOVERS" || echo "clean"
```
Expected: `clean`.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "docs!: rename skopeo analyzer to oci and require regctl

BREAKING CHANGE: documentation, dashboard, and playbook references updated from
the skopeo analyzer (results.skopeo.*, provider: skopeo) to oci."
```

---

## Task 12: Full verification gate

**Files:** none (verification only)

- [ ] **Step 1: Full test suite with coverage**

Run: `pipenv run pytest`
Expected: all pass, coverage ≥ 90 %. Investigate any analyzer whose coverage
dropped (the regctl branches need test coverage equivalent to the old skopeo
branches).

- [ ] **Step 2: Lint and format**

Run: `pipenv run ruff check . && pipenv run ruff format --check . && trunk check`
Expected: clean (let `trunk check --fix` auto-fix, then re-stage).

- [ ] **Step 3: Confirm skopeo is fully gone from runtime code**

```bash
grep -rn "skopeo" regis/ | grep -v "versioned_docs" || echo "no skopeo references remain"
```
Expected: only intentional historical mentions (e.g. a CHANGELOG entry, or none).
There must be **zero** `subprocess`/`["skopeo"` call sites and no `skopeo` in
`doctor.py` or the `Dockerfile` apt install.

- [ ] **Step 4: End-to-end smoke run (optional, needs network)**

```bash
pipenv run regis analyze docker.io/library/alpine:3.20 --skip trivy --skip dockle --skip hadolint
```
Expected: the `oci` analyzer produces a valid report (platforms with `size`,
`layers_count`, `env`, `exposed_ports`); freshness/versioning/size succeed.

- [ ] **Step 5: Open the PR**

```bash
git push -u origin <branch>
gh pr create --fill --label whats-new
```
PR `## Summary` should describe the user-facing breaking change (skopeo → oci,
new required binary `regctl`, migration note for custom playbooks/rules). The
`whats-new` label harvests the Summary into the What's New page.

---

## Self-Review notes (for the implementer)

- **Spec coverage:** every spec section maps to a task — §2 call sites →
  Tasks 4–8; §3 mapping → Tasks 4–8; §4 auth → Task 2; §5 schema → Task 3;
  §6 rename → Tasks 4, 11; §7 Dockerfile → Task 10; §8 doctor/docs → Tasks 9, 11;
  §9 tests → embedded per task + Task 12; §10 versioning/rollout → commit messages
  + Task 12 Step 5; §11 open questions → Task 1.
- **Order dependency:** Task 2 (wrapper) must land before Tasks 4–8. Task 1
  (probe) must land before Task 2 so fixtures/output shapes are real. Tasks 5–9
  are independent of each other and may be parallelized across subagents.
- **If a probe answer (Task 1) contradicts §3,** update the spec first, then
  adjust the affected task's command strings.
