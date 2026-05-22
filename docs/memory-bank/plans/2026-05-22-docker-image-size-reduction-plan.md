# Docker Image Size Reduction — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce the published `ghcr.io/trivoallan/regis` Docker image by ≥50 % via a 4-stage multi-stage build, removing Node.js/pnpm and build tooling from the runtime layer, and enforce a hardcoded size limit in CI.

**Architecture:** Split build into 4 stages (`frontend-builder`, `python-builder`, `tools-fetcher`, `final`). Frontend dashboard is consumed by python-builder before `pip install` so it's packaged as `package-data`. Tools (trivy/hadolint/dockle) come from a curl-only fetch stage. Final stage is `python:3.14-slim` with only `skopeo git jq ca-certificates` and the pre-built venv + tool binaries copied in. Bootstrap commands check for Node/pnpm presence and emit a structured error pointing the user to install on the host.

**Tech Stack:** Docker (BuildKit), Python 3.14, pip + venv, click, pytest, GitHub Actions, `wemake-services/docker-image-size-limit`, Release Please.

**Design doc:** `docs/memory-bank/plans/2026-05-22-docker-image-size-reduction-design.md`

**PR sequence:**

1. **PR 1** — `chore(release): keep minor bumps for breaking changes pre-1.0` (Task 1)
2. **PR 2** — `feat(build)!: drop Node from runtime image and adopt 4-stage build` (Tasks 2–14)
3. **PR 3** — `ci(build): enforce docker image size limit` (Tasks 15–17)

Merge order: PR 1 first, then PR 2, then PR 3.

---

## PR 1 — Release Please config (single task)

### Task 1: Add `bump-minor-pre-major` to release-please-config.json

**Files:**

- Modify: `release-please-config.json:2-5`

- [ ] **Step 1: Verify current file content**

Run: `cat release-please-config.json | jq '.packages["."] | keys'`
Expected: `["changelog-sections", "extra-files", "release-type"]` (no `bump-minor-pre-major` yet)

- [ ] **Step 2: Add the config option**

Modify `release-please-config.json`. After the `"release-type": "python",` line, add:

```json
      "bump-minor-pre-major": true,
```

Final file:

```json
{
  "packages": {
    ".": {
      "extra-files": [
        "regis/cookiecutters/playbook/cookiecutter.json",
        "regis/cookiecutters/archive/cookiecutter.json",
        "README.md",
        "docs/website/docusaurus.config.ts",
        "docs/website/package.json"
      ],
      "release-type": "python",
      "bump-minor-pre-major": true,
      "changelog-sections": [
        { "type": "feat", "section": "Features" },
        { "type": "fix", "section": "Bug Fixes" },
        { "type": "perf", "section": "Performance Improvements" },
        { "type": "revert", "section": "Reverts" },
        { "type": "chore", "section": "Miscellaneous Chores", "hidden": true },
        { "type": "docs", "section": "Documentation", "hidden": true },
        { "type": "style", "section": "Styles", "hidden": true },
        { "type": "refactor", "section": "Code Refactoring", "hidden": true },
        { "type": "test", "section": "Tests", "hidden": true },
        { "type": "build", "section": "Build System", "hidden": true },
        { "type": "ci", "section": "Continuous Integration", "hidden": true }
      ]
    }
  }
}
```

- [ ] **Step 3: Validate JSON**

Run: `jq . release-please-config.json > /dev/null && echo OK`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git checkout -b chore/release-please-pre-major-minor-bumps
git add release-please-config.json
git commit -m "chore(release): keep minor bumps for breaking changes pre-1.0

In pre-1.0 SemVer, breaking changes should bump the minor version, not
the major. With release-please's default behavior, a 'feat!:' commit
would jump 0.31.0 → 1.0.0. Setting bump-minor-pre-major=true keeps the
expected 0.31.0 → 0.32.0 progression until we explicitly graduate to
v1."
```

- [ ] **Step 5: Open PR and merge**

```bash
git push -u origin chore/release-please-pre-major-minor-bumps
gh pr create --title "chore(release): keep minor bumps for breaking changes pre-1.0" \
  --body "$(cat <<'EOF'
## Summary

- Adds \`bump-minor-pre-major: true\` to release-please-config.json so a future \`feat!:\` commit in pre-1.0 bumps the minor (0.x → 0.x+1.0) instead of jumping to 1.0.0.

## Test plan

- [x] \`jq . release-please-config.json\` succeeds
- [ ] Next release after merge produces correct version bump

EOF
)"
```

Merge before starting PR 2.

---

## PR 2 — Image refactor + Node removal (Tasks 2–14)

### Task 2: Extend `require_tool` to accept an optional install hint

**Files:**

- Modify: `regis/utils/process.py:39-44`
- Modify: `tests/test_cli.py` (or appropriate process tests file — find existing tests for `require_tool`)

- [ ] **Step 1: Locate existing tests for `require_tool`**

Run: `grep -rn "require_tool" tests/ | head`

If no dedicated test file exists, create `tests/test_utils_process.py`.

- [ ] **Step 2: Write failing tests**

Create or append to `tests/test_utils_process.py`:

```python
"""Tests for regis.utils.process helpers."""

from unittest.mock import patch

import click
import pytest

from regis.utils.process import require_tool


class TestRequireTool:
    @patch("regis.utils.process.shutil.which", return_value="/usr/bin/git")
    def test_returns_path_when_tool_present(self, _mock_which):
        assert require_tool("git") == "/usr/bin/git"

    @patch("regis.utils.process.shutil.which", return_value=None)
    def test_raises_with_default_message_when_missing(self, _mock_which):
        with pytest.raises(click.ClickException) as exc_info:
            require_tool("nonexistent")
        assert "'nonexistent' not found in PATH" in exc_info.value.message

    @patch("regis.utils.process.shutil.which", return_value=None)
    def test_raises_with_install_hint_when_provided(self, _mock_which):
        hint = "Install via: brew install foo"
        with pytest.raises(click.ClickException) as exc_info:
            require_tool("foo", install_hint=hint)
        assert "'foo' not found in PATH" in exc_info.value.message
        assert hint in exc_info.value.message
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pipenv run pytest tests/test_utils_process.py -v`
Expected: `test_raises_with_install_hint_when_provided` FAILS with `TypeError: require_tool() got an unexpected keyword argument 'install_hint'`

- [ ] **Step 4: Update `require_tool` implementation**

In `regis/utils/process.py`, replace the existing `require_tool`:

```python
def require_tool(name: str, install_hint: str | None = None) -> str:
    """Ensure a CLI tool is available in PATH or raise ClickException.

    Args:
        name: Tool binary name to look up in PATH.
        install_hint: Optional multi-line guidance appended to the error
            message when the tool is missing.
    """
    path = shutil.which(name)
    if not path:
        message = f"'{name}' not found in PATH. Please install it."
        if install_hint:
            message = f"{message}\n\n{install_hint}"
        raise click.ClickException(message)
    return path
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pipenv run pytest tests/test_utils_process.py -v`
Expected: 3 PASS

- [ ] **Step 6: Verify existing callers still work**

Run: `pipenv run pytest -x`
Expected: All existing tests pass (the new optional kwarg is backward compatible).

- [ ] **Step 7: Commit**

```bash
git checkout -b feat/build-drop-node-runtime
git add regis/utils/process.py tests/test_utils_process.py
git commit -m "refactor(cli): add optional install_hint to require_tool"
```

---

### Task 3: Add `_NODE_INSTALL_HINT` constant in bootstrap.py and call it on `--dev`/`--repo`

**Files:**

- Modify: `regis/commands/bootstrap.py:1-15` (imports / module-level)
- Modify: `regis/commands/bootstrap.py:233-237` and `:284-285` (existing `require_tool` calls)
- Modify: `tests/test_bootstrap.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_bootstrap.py`:

```python
class TestBootstrapArchiveNodeChecks:
    """Verify --dev/--repo emit a helpful error when Node/pnpm are missing."""

    @patch("regis.commands.bootstrap.shutil.which", return_value=None)
    def test_dev_without_node_raises_with_install_hint(self, _mock_which, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["bootstrap", "archive", "--dev", "--no-input", str(tmp_path)],
        )
        assert result.exit_code != 0
        assert "not found in PATH" in result.output
        assert "nvm" in result.output or "fnm" in result.output
        assert "host" in result.output.lower()

    @patch("regis.commands.bootstrap.shutil.which", return_value=None)
    def test_repo_without_node_raises_with_install_hint(self, _mock_which, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["bootstrap", "archive", "--repo", "--no-input", str(tmp_path)],
        )
        assert result.exit_code != 0
        assert "not found in PATH" in result.output
        assert "nvm" in result.output or "fnm" in result.output

    @patch("regis.commands.bootstrap.shutil.which")
    def test_dev_with_node_but_no_pnpm_raises(self, mock_which, tmp_path):
        # node present, pnpm absent
        mock_which.side_effect = lambda name: "/usr/bin/node" if name == "node" else None
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["bootstrap", "archive", "--dev", "--no-input", str(tmp_path)],
        )
        assert result.exit_code != 0
        assert "pnpm" in result.output
        assert "corepack" in result.output.lower() or "npm install -g" in result.output
```

Add the imports at the top of `tests/test_bootstrap.py` if missing:

```python
from unittest.mock import patch
from click.testing import CliRunner
from regis.cli import main
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pipenv run pytest tests/test_bootstrap.py::TestBootstrapArchiveNodeChecks -v`
Expected: 3 FAIL (current message doesn't mention nvm/fnm/host/corepack).

- [ ] **Step 3: Add `shutil` import and install-hint constants in bootstrap.py**

In `regis/commands/bootstrap.py`, after the existing imports (around line 10), add:

```python
import shutil
```

After the existing imports block (before the first `def`), add:

```python
_NODE_INSTALL_HINT = """\
This command requires Node.js on the host. The published Regis image
no longer bundles Node.js to keep container size minimal.

Install Node 20+ on the host:
  • nvm:  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash && nvm install --lts
  • fnm:  curl -fsSL https://fnm.vercel.app/install | bash && fnm install --lts
  • brew: brew install node

Then re-run this command from the host (not from inside a container).\
"""

_PNPM_INSTALL_HINT = """\
This command requires pnpm. Install via one of:
  • corepack:  corepack enable && corepack prepare pnpm@latest --activate
  • npm:       npm install -g pnpm
  • brew:      brew install pnpm\
"""
```

- [ ] **Step 4: Replace existing `require_tool` calls**

In `regis/commands/bootstrap.py`, find the block at line ~233:

```python
    if repo:
        click.echo("Checking required tools...", err=True)
        require_tool("pnpm")
        require_tool("git")
        click.echo("  ✓ pnpm and git found.", err=True)
```

Replace with:

```python
    if repo or dev:
        click.echo("Checking required tools...", err=True)
        require_tool("node", install_hint=_NODE_INSTALL_HINT)
        require_tool("pnpm", install_hint=_PNPM_INSTALL_HINT)
        if repo:
            require_tool("git")
        click.echo("  ✓ Node.js, pnpm, and git found.", err=True)
```

Then find the duplicate `require_tool("pnpm")` at line ~285 inside the `if dev:` block and remove it (the check is now done upfront):

```python
    if dev:
        require_tool("pnpm")   # ← DELETE THIS LINE
        click.echo("\nInstalling Node dependencies (pnpm install)...", err=True)
```

becomes:

```python
    if dev:
        click.echo("\nInstalling Node dependencies (pnpm install)...", err=True)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pipenv run pytest tests/test_bootstrap.py::TestBootstrapArchiveNodeChecks -v`
Expected: 3 PASS

- [ ] **Step 6: Run full test suite**

Run: `pipenv run pytest`
Expected: All tests pass, coverage ≥ 90%.

- [ ] **Step 7: Commit**

```bash
git add regis/commands/bootstrap.py tests/test_bootstrap.py
git commit -m "feat(cli)!: require Node.js and pnpm on host for bootstrap archive --dev/--repo

BREAKING CHANGE: The published Regis Docker image no longer bundles
Node.js. 'regis bootstrap archive --dev' and '--repo' now check for
Node and pnpm on the host upfront and emit a structured error with
install instructions (nvm/fnm/brew, corepack) when missing."
```

---

### Task 4: Extend `.dockerignore`

**Files:**

- Modify: `.dockerignore`

- [ ] **Step 1: Replace `.dockerignore` content**

Replace `.dockerignore` with:

```gitignore
# VCS / build / lockfiles
.git
.github
.gitignore
.gitlab-ci.yml
.serena
.agent
.claude
.omc
.trunk

# Python build artifacts
.venv
__pycache__
*.pyc
*.pyo
*.egg-info
dist
build
.pytest_cache
.ruff_cache
.coverage
coverage-badge.svg

# Node artifacts
node_modules
package-lock.json
apps/dashboard/build
apps/dashboard/.docusaurus

# Docs and tests (not needed at runtime)
docs
tests
CHANGELOG.md
*.md
!README.md

# Editor / OS
.DS_Store
.vscode
.idea
```

- [ ] **Step 2: Verify dockerignore is read correctly**

Run: `docker build --no-cache --target=python-builder -t regis:dockerignore-test . 2>&1 | grep -E "transferring context|Sending build context" | head`

Expected: build context size is small (under ~10 MB; today it's likely much larger due to docs/, tests/, etc.). Note: this step requires Task 5 first; skip and revisit after Task 5.

- [ ] **Step 3: Commit (deferred — bundle with Task 5)**

The `.dockerignore` change is committed together with the Dockerfile rewrite in Task 5 for atomicity.

---

### Task 5: Rewrite Dockerfile as 4-stage build

**Files:**

- Modify: `Dockerfile` (full rewrite)

- [ ] **Step 1: Write the new Dockerfile**

Replace `Dockerfile` with:

```dockerfile
# syntax=docker/dockerfile:1.7

# ──────────────────────────────────────────────────────────────────────────────
# Stage 1: frontend-builder — builds the Docusaurus dashboard
# ──────────────────────────────────────────────────────────────────────────────
FROM node:25-slim AS frontend-builder
RUN npm install -g pnpm@10.10.0
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml* ./
COPY apps/ apps/
RUN pnpm install --frozen-lockfile
WORKDIR /app/apps/dashboard
RUN pnpm run build

# ──────────────────────────────────────────────────────────────────────────────
# Stage 2: python-builder — compiles Python deps into a venv
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.14-slim AS python-builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /src
COPY pyproject.toml Pipfile Pipfile.lock ./
COPY regis/ regis/
COPY --from=frontend-builder /app/apps/dashboard/build regis/dashboard_assets

RUN VERSION=$(grep -oP '(?<=version = ")[^"]+' pyproject.toml) && \
    SETUPTOOLS_SCM_PRETEND_VERSION="$VERSION" pip install .

# ──────────────────────────────────────────────────────────────────────────────
# Stage 3: tools-fetcher — downloads external analyzer binaries
# ──────────────────────────────────────────────────────────────────────────────
FROM curlimages/curl:8.10.1 AS tools-fetcher
ARG TARGETARCH
ENV HADOLINT_VERSION=2.12.0 \
    DOCKLE_VERSION=0.4.15

USER root
WORKDIR /tools

# Trivy via the official install script
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
    | sh -s -- -b /tools

# Hadolint
RUN case "$TARGETARCH" in \
      amd64) hadolint_arch="x86_64" ;; \
      arm64) hadolint_arch="arm64" ;; \
      *) echo "Unsupported TARGETARCH: $TARGETARCH" >&2; exit 1 ;; \
    esac && \
    curl -sSfL "https://github.com/hadolint/hadolint/releases/download/v${HADOLINT_VERSION}/hadolint-Linux-${hadolint_arch}" \
      -o /tools/hadolint && \
    chmod +x /tools/hadolint

# Dockle
RUN case "$TARGETARCH" in \
      amd64) dockle_arch="64bit" ;; \
      arm64) dockle_arch="ARM64" ;; \
      *) echo "Unsupported TARGETARCH: $TARGETARCH" >&2; exit 1 ;; \
    esac && \
    curl -sSfL "https://github.com/goodwithtech/dockle/releases/download/v${DOCKLE_VERSION}/dockle_${DOCKLE_VERSION}_Linux-${dockle_arch}.tar.gz" \
      -o /tmp/dockle.tar.gz && \
    tar -xzf /tmp/dockle.tar.gz -C /tools dockle && \
    chmod +x /tools/dockle && \
    rm /tmp/dockle.tar.gz

# ──────────────────────────────────────────────────────────────────────────────
# Stage 4: final — minimal runtime image
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.14-slim AS final

LABEL org.opencontainers.image.title="regis" \
      org.opencontainers.image.description="Regis — Registry Scores. Container Security & Policy-as-Code Orchestration." \
      org.opencontainers.image.url="https://github.com/trivoallan" \
      org.opencontainers.image.source="https://github.com/trivoallan/regis" \
      org.opencontainers.image.documentation="https://trivoallan.github.io/regis/" \
      org.opencontainers.image.vendor="trivoallan" \
      org.opencontainers.image.authors="trivoallan" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PATH="/opt/venv/bin:$PATH"

# Minimal runtime dependencies only — no curl, no gnupg, no build-essential
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
      skopeo \
      git \
      jq \
      ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd -g 1001 regis && \
    useradd -u 1001 -g regis -m -d /home/regis regis
ENV HOME=/home/regis

# Copy artifacts from build stages
COPY --from=python-builder /opt/venv /opt/venv
COPY --from=tools-fetcher /tools/trivy /usr/local/bin/trivy
COPY --from=tools-fetcher /tools/hadolint /usr/local/bin/hadolint
COPY --from=tools-fetcher /tools/dockle /usr/local/bin/dockle

WORKDIR /home/regis
USER regis

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD regis list || exit 1

ENTRYPOINT ["regis"]
CMD ["--help"]
```

- [ ] **Step 2: Validate Dockerfile syntax with hadolint**

Run: `hadolint Dockerfile`
Expected: No errors (some info-level hints OK). Fix any errors before proceeding.

- [ ] **Step 3: Commit Dockerfile + dockerignore together**

```bash
git add Dockerfile .dockerignore
git commit -m "feat(build)!: rewrite Dockerfile as 4-stage build, drop Node.js from runtime

BREAKING CHANGE: The published image no longer contains Node.js, pnpm,
curl, gnupg, or build-essential. 'regis bootstrap archive --dev/--repo'
must now be run from the host. Other commands ('regis analyze', 'regis
check', 'regis bootstrap playbook', etc.) work unchanged.

Stages:
  • frontend-builder  → builds Docusaurus dashboard
  • python-builder    → compiles deps into /opt/venv
  • tools-fetcher     → downloads trivy/hadolint/dockle
  • final             → python:3.14-slim + skopeo + venv + tool binaries"
```

---

### Task 6: Local build and smoke test

**Files:** none

- [ ] **Step 1: Build the image locally**

Run: `docker build -t regis:size-check .`
Expected: Build succeeds. Note the final image size.

- [ ] **Step 2: Measure image size**

Run: `docker image inspect regis:size-check --format='{{.Size}}' | awk '{ printf "%.1f MB\n", $1 / 1024 / 1024 }'`
Record this value — you'll need it for Task 15.

- [ ] **Step 3: Verify no build tooling in the final image**

Run:

```bash
for tool in gcc curl npm pnpm node gnupg; do
  echo -n "$tool: "
  docker run --rm --entrypoint sh regis:size-check -c "command -v $tool 2>/dev/null || echo NOT_FOUND"
done
```

Expected: All six show `NOT_FOUND`.

- [ ] **Step 4: Verify required analyzers are present**

Run:

```bash
for tool in skopeo trivy hadolint dockle regis git jq; do
  echo -n "$tool: "
  docker run --rm --entrypoint sh regis:size-check -c "command -v $tool"
done
```

Expected: All seven print a path.

- [ ] **Step 5: Run `regis --help` and `regis list`**

```bash
docker run --rm regis:size-check --help
docker run --rm regis:size-check list
```

Expected: Both exit 0 and print expected output.

- [ ] **Step 6: Run a real analysis**

```bash
docker run --rm regis:size-check analyze docker.io/library/alpine:3.19
```

Expected: Analysis completes; analyzer outputs visible; exit 0 (or non-zero playbook gate is acceptable as long as no traceback).

- [ ] **Step 7: Verify bootstrap error message**

```bash
docker run --rm regis:size-check bootstrap archive --dev /tmp/test
```

Expected: Exit code 1; output contains "not found in PATH", "nvm", "fnm", "host".

- [ ] **Step 8: Inspect layers**

Run: `docker history --no-trunc regis:size-check`
Expected: No layer references npm, pnpm, node, gcc. Skopeo and dependencies visible via apt layer.

- [ ] **Step 9: No commit yet**

Smoke tests are diagnostic. If they fail, return to Task 5 and fix.

---

### Task 7: Verify behavior with `regis bootstrap playbook` (non-Node path)

**Files:** none

- [ ] **Step 1: Run bootstrap playbook from the container**

```bash
mkdir -p /tmp/regis-playbook-test && \
docker run --rm -v /tmp/regis-playbook-test:/home/regis/work regis:size-check \
  bootstrap playbook --no-input /home/regis/work/test-playbook
```

Expected: Exit 0; `/tmp/regis-playbook-test/test-playbook/` populated with playbook files.

- [ ] **Step 2: Cleanup**

```bash
rm -rf /tmp/regis-playbook-test
```

---

### Task 8: Update `README.md` (breaking change note)

**Files:**

- Modify: `README.md`

- [ ] **Step 1: Locate the Docker usage section**

Run: `grep -n "docker run\|ghcr.io" README.md | head`
Note line numbers for the Docker section.

- [ ] **Step 2: Add a breaking-change note**

Add a callout block immediately before the existing Docker usage section:

```markdown
> **⚠ Breaking change in v0.32.0** — The published image no longer bundles
> Node.js. `regis bootstrap archive --dev` and `--repo` must now be run from
> a host that has Node 20+ and pnpm installed (install via `nvm`, `fnm`, or
> `brew install node`). All other commands work unchanged.
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs(readme): document Node.js removal from Docker image"
```

---

### Task 9: Update `docs/website/docs/integrations/*` for Node prerequisite

**Files:**

- Modify: Pages under `docs/website/docs/` that mention `regis bootstrap archive` (locate with grep)

- [ ] **Step 1: Find pages that reference bootstrap archive**

Run: `grep -rln "bootstrap archive" docs/website/docs/`
Note the files.

- [ ] **Step 2: Add prerequisite note to each**

For each matching page that documents `--dev` or `--repo`, add a prerequisite note:

```markdown
:::note Prerequisite

`--dev` and `--repo` require Node.js 20+ and pnpm on the host. These commands
no longer work from inside the official Regis Docker image (see [v0.32.0
release notes](../whats-new.md)).

:::
```

- [ ] **Step 3: Commit**

```bash
git add docs/website/docs/
git commit -m "docs(integrations): note Node.js host requirement for bootstrap archive"
```

---

### Task 10: Update memory bank

**Files:**

- Modify: `docs/memory-bank/activeContext.md`
- Modify: `docs/memory-bank/progress.md`

- [ ] **Step 1: Add entry to `activeContext.md`**

Add at the top of the "## Recent Changes" section in `docs/memory-bank/activeContext.md`:

```markdown
- [2026-05-22] **Docker image refactor (breaking, v0.32.0)**:
  - Rewrote `Dockerfile` as 4-stage build (`frontend-builder`, `python-builder`, `tools-fetcher`, `final`).
  - Removed Node.js, pnpm, curl, gnupg, build-essential from runtime image.
  - `regis bootstrap archive --dev/--repo` now host-only with structured error message via `_NODE_INSTALL_HINT` / `_PNPM_INSTALL_HINT`.
  - Extended `require_tool()` with optional `install_hint` argument.
  - Strict `.dockerignore` (excludes docs/, tests/, \*.md except README).
  - `release-please-config.json`: `bump-minor-pre-major: true` so 0.31.0 → 0.32.0 instead of 1.0.0.
```

- [ ] **Step 2: Add entry to `progress.md`**

Append to the "## Completed (Recent)" section:

```markdown
- **Docker image size reduction (2026-05-22, v0.32.0)**:
  - 4-stage Dockerfile; runtime image strips Node.js + build tooling.
  - Image size reduced by ≥50%.
  - Breaking change: `bootstrap archive --dev/--repo` is host-only.
  - Hardcoded size limit enforced in CI via `wemake-services/docker-image-size-limit`.
```

- [ ] **Step 3: Commit**

```bash
git add docs/memory-bank/activeContext.md docs/memory-bank/progress.md
git commit -m "docs(memory-bank): record Docker image refactor for v0.32.0"
```

---

### Task 11: Add `whats-new` page entry (if process requires)

**Files:**

- Modify: `docs/website/docs/whats-new.md` only if it is **not** auto-generated. The PR label `whats-new` typically triggers auto-generation by `scripts/generate_whats_new.py`.

- [ ] **Step 1: Check whether `whats-new.md` is generated or hand-edited**

Run: `head -20 docs/website/docs/whats-new.md`

If it has a marker like `<!-- generated -->` or is excluded from manual edits per CLAUDE.md, skip this task — adding the `whats-new` label on the PR is enough.

If it is hand-edited, prepend a section like:

```markdown
## v0.32.0 — Smaller, leaner Docker image

The published `ghcr.io/trivoallan/regis` image is now ≥50% smaller.
Node.js and build tooling have been removed from the runtime layer.

**Breaking:** `regis bootstrap archive --dev` and `--repo` now require
Node.js on the host. See the [release notes](../changelog) for migration
guidance.
```

- [ ] **Step 2: Commit (only if file was edited)**

```bash
git add docs/website/docs/whats-new.md
git commit -m "docs(whats-new): announce smaller Docker image for v0.32.0"
```

---

### Task 12: Run full test suite + linting

**Files:** none

- [ ] **Step 1: Lint**

Run: `pipenv run ruff check .`
Expected: No errors.

Run: `pipenv run ruff format --check .`
Expected: No diffs.

- [ ] **Step 2: Run trunk**

Run: `trunk check`
Expected: No new issues.

- [ ] **Step 3: Run full test suite**

Run: `pipenv run pytest`
Expected: All tests pass, coverage ≥ 90%.

---

### Task 13: Push PR 2 and add `whats-new` label

**Files:** none

- [ ] **Step 1: Push branch**

```bash
git push -u origin feat/build-drop-node-runtime
```

- [ ] **Step 2: Open the PR**

```bash
gh pr create --title "feat(build)!: drop Node.js from runtime image, adopt 4-stage build" \
  --body "$(cat <<'EOF'
## Summary

- Rewrote \`Dockerfile\` as 4-stage build (frontend-builder, python-builder, tools-fetcher, final).
- Removed Node.js, pnpm, curl, gnupg, build-essential from the runtime image.
- \`regis bootstrap archive --dev/--repo\` now check for Node.js + pnpm on the host upfront with a structured error message.
- Extended \`.dockerignore\` to keep the build context minimal.
- Bumped \`require_tool()\` with an optional \`install_hint\` argument.

**Image size:** measured locally — record actual value here in the PR description.

## Breaking change

This is a major refactor of the published Docker image. \`bootstrap archive --dev\` and \`--repo\` no longer work from inside the container — they now require Node.js 20+ and pnpm on the host (install via nvm/fnm/brew + corepack).

Version will bump 0.31.0 → 0.32.0 (controlled by \`bump-minor-pre-major\` in release-please-config.json — merged in #PR-1).

## Test plan

- [x] Unit tests pass (\`pipenv run pytest\`)
- [x] \`docker build -t regis:size-check .\` succeeds
- [x] \`docker run regis:size-check --help\` exits 0
- [x] \`docker run regis:size-check list\` exits 0
- [x] \`docker run regis:size-check analyze docker.io/library/alpine:3.19\` succeeds
- [x] \`docker run regis:size-check bootstrap archive --dev /tmp/test\` exits 1 with helpful message
- [x] No \`gcc\`, \`curl\`, \`npm\`, \`pnpm\`, \`node\` in final image
- [x] Image size ≤50% of v0.31.0

EOF
)"
```

- [ ] **Step 3: Add `whats-new` label**

```bash
gh pr edit --add-label whats-new
```

- [ ] **Step 4: Wait for CI + reviewer approval; then merge**

After merge, **note the published image size on `main`** (from CI logs or by rebuilding locally). This value will set the limit in PR 3.

---

### Task 14: Tag a snapshot release (optional verification step)

**Files:** none

- [ ] **Step 1: Verify Release Please opens a PR with version 0.32.0**

After PR 2 merges, Release Please should open an autorelease PR. Verify the version is `0.32.0` (not `1.0.0`).

Run: `gh pr list --label 'autorelease: pending'`

If the version is wrong, do not merge — revisit PR 1 (`bump-minor-pre-major`) to ensure the config landed.

---

## PR 3 — CI size gate (Tasks 15–17)

### Task 15: Determine the hardcoded size limit

**Files:** none (preparation only)

- [ ] **Step 1: Pull the latest image from `main`**

```bash
docker pull ghcr.io/trivoallan/regis:latest
docker image inspect ghcr.io/trivoallan/regis:latest --format='{{.Size}}' \
  | awk '{ printf "%d MB\n", $1 / 1024 / 1024 }'
```

Record the size in MB. Call it `<MEASURED_MB>`.

- [ ] **Step 2: Pick the CI limit**

Choose a value that is `<MEASURED_MB> + 50 MB` (a ~10–15% headroom to absorb minor growth without false failures).

Record this as `<SIZE_LIMIT_MB>` (e.g., `850 MB`).

The action `wemake-services/docker-image-size-limit` accepts units like `850MB` or `850m`.

---

### Task 16: Create the CI size gate workflow

**Files:**

- Create: `.github/workflows/ci-image-size.yml`

- [ ] **Step 1: Write the workflow**

Create `.github/workflows/ci-image-size.yml`:

```yaml
name: CI / Image Size

on:
  pull_request:
    paths:
      - "Dockerfile"
      - ".dockerignore"
      - "pyproject.toml"
      - "Pipfile"
      - "Pipfile.lock"
      - "apps/dashboard/**"
      - ".github/workflows/ci-image-size.yml"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  image-size:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@4d04d5d9486b7bd6fa91e7baf45bbb4f8b9deedd # v4.0.0

      - name: Build image
        uses: docker/build-push-action@bcafcacb16a39f128d818304e6c9c0c18556b85f # v7.1.0
        with:
          context: .
          load: true
          tags: regis:size-check
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Enforce size limit
        uses: wemake-services/docker-image-size-limit@b14d40e88d1cd566aceb18ad7e07e9bd06b3a3a4 # v3.0.0
        with:
          image: "regis:size-check"
          size: "<SIZE_LIMIT_MB>MB"
```

Replace `<SIZE_LIMIT_MB>` with the value from Task 15.

Verify the SHA pin for `wemake-services/docker-image-size-limit` matches the latest release: `gh api repos/wemake-services/docker-image-size-limit/releases/latest --jq .tag_name,.target_commitish`. If the pinned SHA differs from the latest tagged release, update both the SHA and the trailing `# vX.Y.Z` comment.

- [ ] **Step 2: Validate workflow syntax**

Run: `gh workflow view ci-image-size.yml --yaml 2>/dev/null || cat .github/workflows/ci-image-size.yml`

Run trunk to lint the YAML:

```bash
trunk check .github/workflows/ci-image-size.yml
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git checkout -b ci/enforce-image-size-limit
git add .github/workflows/ci-image-size.yml
git commit -m "ci(build): enforce maximum docker image size on PRs

Adds a new CI workflow that builds the Regis image on each PR touching
the Dockerfile, .dockerignore, Python deps, or the dashboard sources,
and fails if the resulting image exceeds <SIZE_LIMIT_MB> MB. Prevents
regressions to the runtime image footprint after the v0.32.0 refactor."
```

Replace `<SIZE_LIMIT_MB>` in the commit message with the real value.

---

### Task 17: Add size badge to `README.md`

**Files:**

- Modify: `README.md`

- [ ] **Step 1: Add badge next to existing badges**

Locate the badge block near the top of `README.md` (look for `[![` shields).

Add a new shield (using shields.io's docker image size endpoint):

```markdown
[![Docker Image Size](https://img.shields.io/docker/image-size/trivoallan/regis/latest?label=image%20size)](https://github.com/trivoallan/regis/pkgs/container/regis)
```

Or, if the image is published only to GHCR (not Docker Hub), use a hardcoded badge with the measured size:

```markdown
[![Docker Image Size](https://img.shields.io/badge/image%20size-<MEASURED_MB>%20MB-blue)](https://github.com/trivoallan/regis/pkgs/container/regis)
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs(readme): add docker image size badge"
```

- [ ] **Step 3: Push and open PR**

```bash
git push -u origin ci/enforce-image-size-limit
gh pr create --title "ci(build): enforce docker image size limit" \
  --body "$(cat <<'EOF'
## Summary

- New CI workflow \`ci-image-size.yml\` runs on PRs touching the Dockerfile or its inputs.
- Uses \`wemake-services/docker-image-size-limit\` with a hardcoded ceiling of \`<SIZE_LIMIT_MB>MB\` (measured post-refactor + ~10% headroom).
- Adds image size badge to README.

## Test plan

- [x] Workflow YAML validated with \`trunk check\`
- [ ] Workflow runs on this PR and succeeds (image size below limit)
- [ ] Intentionally bloating the image in a follow-up branch fails the gate

EOF
)"
```

---

## Self-Review

**Spec coverage:**

- 4-stage Dockerfile → Task 5 ✓
- Node/pnpm removal + structured error → Tasks 2, 3 ✓
- `.dockerignore` extension → Task 4 ✓
- `release-please-config.json` `bump-minor-pre-major` → Task 1 ✓
- CI size gate via `wemake-services/docker-image-size-limit` → Task 16 ✓
- Documentation (README, integrations, memory bank, what's new) → Tasks 8, 9, 10, 11 ✓
- Smoke tests + tool absence checks → Task 6 ✓
- Multi-arch via `TARGETARCH` → Task 5 (Dockerfile uses ARG TARGETARCH) ✓
- Size badge → Task 17 ✓

**Placeholder scan:**

- `<MEASURED_MB>` and `<SIZE_LIMIT_MB>` are intentional template values resolved in Tasks 6/15 from actual measurements — these are documented inputs, not placeholders for the engineer to invent.
- No "TBD", "TODO", "implement later", "add error handling", or "similar to Task N" patterns.

**Type / name consistency:**

- `_NODE_INSTALL_HINT` and `_PNPM_INSTALL_HINT` constants — used consistently in Task 3.
- `require_tool(name, install_hint=...)` signature — consistent in Tasks 2 and 3.
- Stage names (`frontend-builder`, `python-builder`, `tools-fetcher`, `final`) — consistent in design doc and Task 5.
- `regis:size-check` tag — consistent in Tasks 6 and 16.
