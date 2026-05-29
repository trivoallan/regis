# Docker Image Size Reduction — Round 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Squeeze additional size out of the published `ghcr.io/trivoallan/regis` image beyond the round-1 4-stage refactor (244 MB → 186 MB tar), via a menu of **independent, individually-measurable** optimizations.

**Architecture:** Each task is a self-contained, revertible optimization with a build-and-measure gate. Tasks are ordered by ROI/risk and can be applied or skipped independently. No base-image change (debian `python:3.14-slim` stays, per round-1 decision).

**Tech Stack:** Docker (BuildKit, multi-stage), Python 3.14, pip + venv, click, pytest, GitHub Actions, `wemake-services/docker-image-size-limit`.

**Prior work:** `docs/memory-bank/plans/2026-05-22-docker-image-size-reduction-design.md` (round 1, merged in PR #606).

---

## Current size breakdown (arm64, decompressed layers via `docker history`)

| Layer                                        | Size       | Notes                                                           |
| -------------------------------------------- | ---------- | --------------------------------------------------------------- |
| debian base                                  | 109 MB     | `python:3.14-slim` rootfs — out of scope (base change deferred) |
| **apt: skopeo + git + jq + ca-certificates** | **208 MB** | skopeo is core; **git + jq are removable** (Task 1)             |
| trivy binary                                 | 150 MB     | Go binary; UPX deferred (risky)                                 |
| venv (`/opt/venv`)                           | 95.6 MB    | includes server stack (fastapi/uvicorn/pydantic) — **Task 2**   |
| dockle binary                                | 24.9 MB    | core analyzer                                                   |
| hadolint binary                              | 24.0 MB    | core analyzer                                                   |
| python build/symlink layers                  | ~50 MB     | base python tooling                                             |

Compressed tar (`docker save`): **186 MB**. CI ceiling currently **250 MB**.

## What this plan does NOT do (investigated, deferred to their own brainstorm)

- **Replace skopeo with `crane`** (go-containerregistry static binary, ~40 MB vs skopeo's ~180 MB with deps). Biggest single win, but requires rewriting `regis/analyzers/skopeo.py` and `regis/analyzers/freshness.py` (different CLI surface, different JSON shape). Behavior-risky — needs its own design + spec.
- **Switch base to alpine / wolfi.** musl libc compatibility risk with skopeo and Python wheels. Explicitly ruled out in round 1.
- **UPX-compress trivy/dockle/hadolint.** Can roughly halve Go binaries but breaks in some runtimes and adds decompression-at-startup cost. High risk, low confidence.

---

## File Structure

| File                                           | Responsibility                                               | Tasks   |
| ---------------------------------------------- | ------------------------------------------------------------ | ------- |
| `Dockerfile`                                   | Build definition — apt line, pip install flags, venv prune   | 1, 2, 3 |
| `pyproject.toml`                               | Move server deps to `[project.optional-dependencies].server` | 2       |
| `regis/commands/dashboard.py`                  | Guard `serve` with helpful error when server extra absent    | 2       |
| `tests/test_dashboard.py`                      | Test the missing-server-extra guard                          | 2       |
| `.github/workflows/ci-image-size.yml`          | Tighten the size ceiling                                     | 4       |
| `README.md`                                    | Update size badge / note                                     | 4       |
| `docs/memory-bank/{activeContext,progress}.md` | Record round-2 results                                       | 4       |

---

## Task 1: Drop `git` and `jq` from the runtime apt layer

**ROI:** ~45 MB decompressed / ~12–18 MB compressed. **Risk:** Low.

**Rationale:** `git` is used only by `regis bootstrap archive --repo` (git init/add/commit/push at `regis/commands/bootstrap.py:350-427`), a flow that is already host-only (requires Node.js, absent from the image) and already guarded by `require_tool("git")`. `jq` has no runtime caller — the only `--jq` reference is `gh api --jq` (gh's built-in flag; gh isn't in the image). Removing both from the apt install also drops git's transitive deps (perl-modules, liberror-perl, git-man, less).

**Files:**

- Modify: `Dockerfile` (final-stage apt block)

- [ ] **Step 1: Verify `git` and `jq` have no runtime caller**

Run:

```bash
cd /Users/tristan/Documents/Workspaces/trivoallan/regis/.claude/worktrees/brave-hertz-928168
grep -rn '"git"\|run_cmd(\["git\|subprocess.*git' regis/ --include="*.py" | grep -v test
grep -rn '"jq"\|run_cmd(\["jq\|subprocess.*\bjq\b' regis/ --include="*.py" | grep -v test
```

Expected: `git` appears only in `regis/commands/bootstrap.py` (the `--repo` flow). `jq` returns no `run_cmd`/`subprocess` hits (only the `gh api --jq` flag string). If either appears in an analyzer or the analyze path, STOP and report — this task's premise is wrong.

- [ ] **Step 2: Edit the final-stage apt block in `Dockerfile`**

Find this block (in the `final` stage):

```dockerfile
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
      skopeo \
      git \
      jq \
      ca-certificates && \
    rm -rf /var/lib/apt/lists/*
```

Replace it with (drop the `git` and `jq` lines):

```dockerfile
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
      skopeo \
      ca-certificates && \
    rm -rf /var/lib/apt/lists/*
```

- [ ] **Step 3: Lint the Dockerfile**

Run: `hadolint Dockerfile`
Expected: No new errors vs. the pre-existing DL3008 hint.

- [ ] **Step 4: Build and capture size**

Run:

```bash
docker build -t regis:r2-task1 . && \
docker save regis:r2-task1 | wc -c | awk '{ printf "tar: %.1f MB\n", $1/1024/1024 }'
```

Expected: build succeeds; tar size noticeably below 186 MB (record the value).

- [ ] **Step 5: Smoke test — core path unaffected, git/jq gone**

Run:

```bash
docker run --rm regis:r2-task1 list >/dev/null && echo "list OK"
docker run --rm --entrypoint sh regis:r2-task1 -c 'command -v git || echo git_GONE'
docker run --rm --entrypoint sh regis:r2-task1 -c 'command -v jq || echo jq_GONE'
docker run --rm --entrypoint sh regis:r2-task1 -c 'command -v skopeo'
docker run --rm regis:r2-task1 analyze docker.io/library/alpine:3.19 >/dev/null 2>&1; echo "analyze exit=$?"
```

Expected: `list OK`; `git_GONE`; `jq_GONE`; skopeo path printed; analyze exits 0 (or a non-zero playbook gate, but no traceback).

- [ ] **Step 6: Commit**

```bash
git add Dockerfile
git commit -m "build(deps): drop git and jq from the runtime image

git is only used by the host-only 'bootstrap archive --repo' flow
(already guarded by require_tool('git')); jq has no runtime caller
(the only --jq usage is gh's built-in flag). Removing them also drops
git's transitive deps (perl-modules, git-man, less)."
```

If the trunk pre-commit hook auto-formats, re-stage and re-commit. Never `--no-verify`.

---

## Task 2: Move the server stack (`fastapi` + `uvicorn[standard]`) to an optional `[server]` extra

**ROI:** ~35–50 MB decompressed / ~15 MB compressed (drops `pydantic-core` rust wheel, `uvloop`, `watchfiles`, `websockets`, `httptools`, `starlette`, `h11`, `python-dotenv`). **Risk:** Moderate.

> **⚠ DECISION GATE — read before implementing.**
> The image **bundles the dashboard assets** (`regis/dashboard_assets`), and `regis dashboard serve` (`regis/commands/dashboard.py:153`) starts a FastAPI/Uvicorn server to view reports. Removing the server stack from the image **breaks in-container `regis dashboard serve`** — analogous to the round-1 decision that made `bootstrap archive --dev/--repo` host-only.
>
> - **Proceed** if the published image is positioned as a **CI analyzer** (`analyze`/`check`/`rules`), and serving the dashboard is expected to run on a host (`pip install 'regis[server]'`) or a dedicated image.
> - **Skip this task** if in-container `regis dashboard serve` must keep working.
>
> This is a product-capability call. Confirm the positioning before executing this task.

**Files:**

- Modify: `pyproject.toml` (move 2 deps from `dependencies` to `[project.optional-dependencies].server`)
- Modify: `regis/commands/dashboard.py` (guard the lazy import in `serve_cmd`)
- Modify: `tests/test_dashboard.py` (test the guard)
- Modify: `Dockerfile` (no change needed — `pip install .` already installs core only once deps move to an extra; add a clarifying comment)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_dashboard.py` (ensure `import sys`, `from click.testing import CliRunner`, and `from regis.cli import main` are present at the top — add any that are missing, do not duplicate):

```python
class TestServeWithoutServerExtra:
    """`regis dashboard serve` must fail helpfully when server deps are absent."""

    def test_serve_without_server_extra_raises_hint(self, monkeypatch):
        # Simulate the optional server extra not being installed: making
        # `import uvicorn` raise ImportError by mapping it to None in sys.modules.
        monkeypatch.setitem(sys.modules, "uvicorn", None)
        runner = CliRunner()
        result = runner.invoke(main, ["dashboard", "serve"])
        assert result.exit_code != 0
        assert "regis[server]" in result.output
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pipenv run pytest tests/test_dashboard.py::TestServeWithoutServerExtra -v`
Expected: FAIL — currently `import uvicorn` mapped to None raises an uncaught `ImportError` (not a `ClickException`), so the output won't contain `regis[server]`.

- [ ] **Step 3: Add the guard constant and wrap the lazy import in `dashboard.py`**

In `regis/commands/dashboard.py`, add a module-level constant near the top (after the imports, before the first `@click` decorator):

```python
_SERVER_EXTRA_HINT = (
    "The 'regis dashboard serve' command requires the optional server "
    "dependencies (FastAPI + Uvicorn), which are not bundled in the "
    "published Docker image to keep it small.\n\n"
    "Install them with:\n"
    "  pip install 'regis[server]'\n\n"
    "Then run 'regis dashboard serve' from that environment."
)
```

Then find the body of `serve_cmd` (around line 163) which currently begins:

```python
    """Serve the interactive dashboard and preview the report locally."""
    import uvicorn

    from regis.server.app import create_app
```

Replace those import lines with a guarded version:

```python
    """Serve the interactive dashboard and preview the report locally."""
    try:
        import uvicorn

        from regis.server.app import create_app
    except ImportError as exc:
        raise click.ClickException(_SERVER_EXTRA_HINT) from exc
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pipenv run pytest tests/test_dashboard.py::TestServeWithoutServerExtra -v`
Expected: PASS.

- [ ] **Step 5: Move the deps in `pyproject.toml`**

In `pyproject.toml`, remove these two lines from the `dependencies = [ ... ]` array:

```toml
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.34",
```

Then add a `server` group to the existing `[project.optional-dependencies]` block (which currently only has `dev`). The block should read:

```toml
[project.optional-dependencies]
server = [
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.34",
]
dev = [
  "pytest>=7.4",
  "pytest-cov>=4.1",
  "responses>=0.24",
  "genbadge[coverage]>=1.1",
  "httpx>=0.28",
]
```

- [ ] **Step 6: Ensure the dev/test environment still has the server deps**

The `dev` extra must pull the server deps so the existing server tests keep running. Add `regis[server]` to `dev` by appending this line inside the `dev = [ ... ]` array:

```toml
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.34",
```

(Listing them directly in `dev` is simpler than self-referential extras and guarantees the test env is unchanged.)

- [ ] **Step 7: Re-sync the dev environment and run the full suite**

Run:

```bash
pipenv run pip install -e '.[dev]'
pipenv run pytest
```

Expected: All tests pass, coverage ≥ 90 %. The server route tests (`tests/test_server_*.py`) still run because `dev` includes the server deps.

- [ ] **Step 8: Add a clarifying comment to the Dockerfile**

In `Dockerfile`, the `python-builder` stage has:

```dockerfile
RUN VERSION=$(grep -oP '(?<=version = ")[^"]+' pyproject.toml) && \
    SETUPTOOLS_SCM_PRETEND_VERSION="$VERSION" pip install .
```

Add a comment line immediately above the `RUN` so it's explicit that the image is core-only:

```dockerfile
# Core install only — the optional [server] extra (FastAPI/Uvicorn) is
# intentionally excluded to keep the runtime image small. Use a host or a
# dedicated image with `pip install 'regis[server]'` for `dashboard serve`.
RUN VERSION=$(grep -oP '(?<=version = ")[^"]+' pyproject.toml) && \
    SETUPTOOLS_SCM_PRETEND_VERSION="$VERSION" pip install .
```

- [ ] **Step 9: Build and verify the image is core-only and still imports**

Run:

```bash
docker build -t regis:r2-task2 . && \
docker save regis:r2-task2 | wc -c | awk '{ printf "tar: %.1f MB\n", $1/1024/1024 }'
docker run --rm --entrypoint python regis:r2-task2 -c "import regis.cli; print('cli import OK')"
docker run --rm --entrypoint python regis:r2-task2 -c "import importlib.util as u; print('fastapi present:', bool(u.find_spec('fastapi')))"
docker run --rm regis:r2-task2 dashboard serve 2>&1 | head -5; echo "serve exit=${PIPESTATUS[0]}"
docker run --rm regis:r2-task2 list >/dev/null && echo "list OK"
```

Expected: tar size below the Task 1 value; `cli import OK`; `fastapi present: False`; `dashboard serve` prints the `regis[server]` hint and exits non-zero; `list OK`.

- [ ] **Step 10: Commit**

```bash
git add pyproject.toml regis/commands/dashboard.py tests/test_dashboard.py Dockerfile
git commit -m "feat(server)!: make FastAPI/Uvicorn an optional [server] extra

BREAKING CHANGE: 'fastapi' and 'uvicorn[standard]' move from core
dependencies to a new optional [server] extra. The published Docker
image no longer bundles them, so in-container 'regis dashboard serve'
now errors with guidance to 'pip install regis[server]'. Core commands
(analyze, check, rules, bootstrap playbook) are unaffected. The dev
extra still pulls the server deps so the test suite is unchanged."
```

If the trunk pre-commit hook auto-formats, re-stage and re-commit. Never `--no-verify`.

---

## Task 3: Trim the venv — skip bytecode compilation and prune caches

**ROI:** ~5–10 MB decompressed. **Risk:** Low (slightly slower first import; acceptable for a CLI).

**Rationale:** `PYTHONDONTWRITEBYTECODE=1` is already set, but `pip install` compiles `.pyc` by default during install. `--no-compile` skips that. Any residual `__pycache__` directories are pruned before the venv is copied to the final stage.

**Files:**

- Modify: `Dockerfile` (`python-builder` stage)

- [ ] **Step 1: Edit the `pip install` line and add a prune step in `python-builder`**

In `Dockerfile`, the `python-builder` install line (from Task 2, or the original if Task 2 was skipped) becomes `--no-compile` and is followed by a prune. Replace:

```dockerfile
RUN VERSION=$(grep -oP '(?<=version = ")[^"]+' pyproject.toml) && \
    SETUPTOOLS_SCM_PRETEND_VERSION="$VERSION" pip install .
```

with:

```dockerfile
RUN VERSION=$(grep -oP '(?<=version = ")[^"]+' pyproject.toml) && \
    SETUPTOOLS_SCM_PRETEND_VERSION="$VERSION" pip install --no-compile . && \
    find /opt/venv -type d -name __pycache__ -prune -exec rm -rf {} + && \
    find /opt/venv -type f -name '*.pyc' -delete
```

(If Task 2 added the clarifying comment above this line, keep the comment.)

- [ ] **Step 2: Lint and build**

Run:

```bash
hadolint Dockerfile
docker build -t regis:r2-task3 . && \
docker save regis:r2-task3 | wc -c | awk '{ printf "tar: %.1f MB\n", $1/1024/1024 }'
```

Expected: no new hadolint errors; tar size at or below the Task 2 value.

- [ ] **Step 3: Smoke test — CLI still works without bytecode cache**

Run:

```bash
docker run --rm regis:r2-task3 list >/dev/null && echo "list OK"
docker run --rm regis:r2-task3 --help >/dev/null && echo "help OK"
docker run --rm --entrypoint sh regis:r2-task3 -c 'find /opt/venv -name "__pycache__" | head -1 | grep -q . && echo "pycache PRESENT" || echo "pycache CLEAN"'
```

Expected: `list OK`; `help OK`; `pycache CLEAN`.

- [ ] **Step 4: Commit**

```bash
git add Dockerfile
git commit -m "build(deps): skip bytecode compilation and prune venv caches

pip install --no-compile + pruning __pycache__/*.pyc shaves the venv
layer. PYTHONDONTWRITEBYTECODE=1 keeps runtime from regenerating .pyc."
```

---

## Task 4: Re-measure, tighten the CI ceiling, update badge and memory bank

**Files:**

- Modify: `.github/workflows/ci-image-size.yml`
- Modify: `README.md`
- Modify: `docs/memory-bank/activeContext.md`
- Modify: `docs/memory-bank/progress.md`

- [ ] **Step 1: Measure the final image after the applied tasks**

Run (against whichever of the Task 1/2/3 images is the latest applied — rebuild the real `Dockerfile`):

```bash
docker build -t regis:r2-final . && \
echo "decompressed: $(docker image inspect regis:r2-final --format='{{.Size}}' | awk '{printf "%.1f MB", $1/1024/1024}')" && \
echo "tar: $(docker save regis:r2-final | wc -c | awk '{printf "%.1f MB", $1/1024/1024}')"
```

Record the tar size as `<R2_TAR_MB>`.

- [ ] **Step 2: Tighten the CI ceiling**

In `.github/workflows/ci-image-size.yml`, find:

```yaml
with:
  image: "regis:size-check"
  size: "250MB"
```

Replace `250MB` with a new ceiling = `ceil(<R2_TAR_MB>) + 30` MB (≈10–15 % headroom). For example, if `<R2_TAR_MB>` is 158, use `190MB`:

```yaml
with:
  image: "regis:size-check"
  size: "190MB"
```

Use your actual measured value, not the example.

- [ ] **Step 3: Update the README size note (if hardcoded)**

If `README.md` contains a hardcoded size figure or a static badge from round 1, update it to the new measured value. If it uses the dynamic `ghcr-badge` shield, no change is needed — verify with:

```bash
grep -n "image%20size\|image size\|ghcr-badge" README.md
```

If a hardcoded MB number is present, update it to `<R2_TAR_MB>` rounded.

- [ ] **Step 4: Update the memory bank**

Add to the top of `## Recent Changes` in `docs/memory-bank/activeContext.md`:

```markdown
- [2026-05-29] **Docker image size — round 2**:
  - Dropped `git` + `jq` from the runtime apt layer (git is host-only via the bootstrap `--repo` flow; jq unused at runtime).
  - Moved `fastapi` + `uvicorn[standard]` to a `[server]` optional extra; in-container `dashboard serve` now errors with a `pip install regis[server]` hint (breaking, consistent with the round-1 bootstrap decision).
  - `pip install --no-compile` + venv `__pycache__` prune.
  - Tightened CI ceiling from 250 MB to <R2_CEILING> MB. Final tar size: <R2_TAR_MB> MB.
```

Add to the top of `## Completed (Recent)` in `docs/memory-bank/progress.md`:

```markdown
- **Docker image size reduction — round 2 (2026-05-29)**:
  - Removed git/jq from runtime; FastAPI/Uvicorn → optional `[server]` extra; `--no-compile` venv.
  - Tar size 186 MB → <R2_TAR_MB> MB. CI ceiling tightened to <R2_CEILING> MB.
  - Deferred (own brainstorm): crane-for-skopeo, alpine/wolfi base, UPX.
```

Replace `<R2_TAR_MB>` and `<R2_CEILING>` with the real values from Steps 1–2.

- [ ] **Step 5: Run lint + full suite one more time**

Run:

```bash
pipenv run pytest
trunk check Dockerfile pyproject.toml .github/workflows/ci-image-size.yml README.md docs/memory-bank/activeContext.md docs/memory-bank/progress.md
```

Expected: tests pass (≥ 90 % coverage); no new trunk issues.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/ci-image-size.yml README.md docs/memory-bank/activeContext.md docs/memory-bank/progress.md
git commit -m "ci(build): tighten docker image size ceiling after round-2 trims

Lowers the enforced ceiling to lock in the round-2 reductions (git/jq
removal, optional server extra, --no-compile venv) and records the new
baseline in the memory bank."
```

---

## Self-Review

**Spec coverage** (against the "options to reduce further" goal):

- git/jq removal → Task 1 ✓
- Python footprint reduction (server stack) → Task 2 ✓
- venv trim → Task 3 ✓
- Lock in gains + observability → Task 4 ✓
- skopeo/crane, alpine, UPX → explicitly documented as deferred (out of scope, need own brainstorm) ✓

**Placeholder scan:**

- `<R2_TAR_MB>` and `<R2_CEILING>` are measured values resolved in Task 4 from real builds — documented inputs, not invented placeholders. The CI-ceiling example (`190MB`) is explicitly flagged as an example to replace.
- No "TBD", "add error handling", or "similar to Task N" patterns. Every code/edit step shows the actual content.

**Type / name consistency:**

- `_SERVER_EXTRA_HINT` defined and used consistently in Task 2.
- The guard test invokes `["dashboard", "serve"]` — matches the actual command (`dashboard_group.command(name="serve")` at `regis/commands/dashboard.py:109`).
- `[project.optional-dependencies].server` name is consistent across pyproject edit (Task 2 Step 5), the commit message, and the `pip install 'regis[server]'` hint.
- Dockerfile `pip install` line is edited by both Task 2 (comment) and Task 3 (`--no-compile` + prune) — Task 3 explicitly notes to keep Task 2's comment, avoiding a conflict if both are applied.

**Independence check:** Tasks 1, 2, 3 touch disjoint concerns (apt line / pyproject+dashboard / pip flags) and can be applied in any subset. Task 4 adapts to whichever were applied by re-measuring. ✓
