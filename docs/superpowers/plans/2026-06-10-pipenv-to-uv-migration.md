# Pipenv → uv Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace pipenv with uv as the Python environment/dependency manager across local dev, CI, the Docker image, and docs.

**Architecture:** `pyproject.toml` stays the single source of truth; dev tooling moves to PEP 735 `[dependency-groups]`, transitive security floors move to `[tool.uv].constraint-dependencies`, and a committed `uv.lock` governs every install path — including the Docker image, which switches from free-resolving `pip install .` to `uv sync --locked`.

**Tech Stack:** uv 0.11.x, astral-sh/setup-uv v8.2.0, setuptools + setuptools-scm (unchanged build backend), Python 3.13 (dev pin) / 3.11 (image).

**Spec:** `docs/superpowers/specs/2026-06-10-pipenv-to-uv-migration-design.md`

**Context for workers:**

- Work happens on the current worktree branch; each task ends with a commit.
- `versioned_docs/` and `CHANGELOG.md` must NEVER be edited (frozen snapshots / Release Please generated).
- Repo convention: GitHub Actions and `COPY --from` images are SHA-pinned with a `# vX.Y.Z` comment.
- There is no new Python code in this migration, so "tests" are the existing suite plus explicit verification commands — run them exactly as written.

---

## Task 1: Dependency layout — pyproject.toml, uv.lock, drop Pipfile

**Files:**

- Modify: `pyproject.toml` (the `[project.optional-dependencies]` block, lines ~46-53)
- Create: `.python-version`
- Create: `uv.lock` (generated)
- Delete: `Pipfile`, `Pipfile.lock`

- [ ] **Step 1: Replace the dev extra with a PEP 735 dependency group**

In `pyproject.toml`, delete this block:

```toml
[project.optional-dependencies]
dev = [
  "pytest>=7.4",
  "pytest-cov>=4.1",
  "responses>=0.24",
  "genbadge[coverage]>=1.1",
  "httpx>=0.28",
]
```

and put in its place (same location in the file):

```toml
[dependency-groups]
dev = [
  "pytest>=7.4",
  "pytest-cov>=4.1",
  "responses>=0.24",
  "genbadge[coverage]>=1.1",
  "httpx>=0.28",
  "ruff",
  "jsonschema2md",
  "json-schema-for-humans",
  "types-PyYAML",
  "types-requests",
  "types-jsonschema",
]

[tool.uv]
constraint-dependencies = [
  "urllib3>=2.7.0",
  "idna>=3.15",
  "pillow>=12.2.0",
  "chardet>=5.0.0",
  "charset-normalizer>=2.0.0",
]
```

Rationale (from spec): the six new group entries and the five constraints come from the
Pipfile (`[dev-packages]` + transitive security floors in `[packages]`); the Pipfile's
runtime duplicates are already in `[project].dependencies` and are simply dropped.
`json-schema-for-humans` is dev tooling (used by `cd-docs.yml`), not a runtime dep.

- [ ] **Step 2: Pin the dev Python version**

Create `.python-version` containing exactly:

```text
3.13
```

(Carries over the Pipfile's `[requires] python_version = "3.13"`. `requires-python >= 3.10` in `pyproject.toml` is unchanged.)

- [ ] **Step 3: Generate the lockfile**

Run: `uv lock`
Expected: `Resolved N packages` and a new `uv.lock` file at the repo root. No errors. (If resolution fails on a constraint, report — do not loosen constraints silently.)

- [ ] **Step 4: Sync the environment**

Run: `uv sync --locked`
Expected: creates `.venv/`, installs the project editable + the `dev` group. Exit 0.

- [ ] **Step 5: Sanity-check the environment**

Run: `uv run regis --help && uv run python -c "import cookiecutter; print('ok')"`
Expected: regis usage text, then `ok`.

- [ ] **Step 6: Run the full test suite (coverage gates active)**

Run: `uv run pytest`
Expected: all tests PASS, total coverage ≥ 90 %, per-file gate green. This validates that uv's resolution didn't break anything despite potentially newer pins than the old pipenv lock.

- [ ] **Step 7: Lint**

Run: `uv run ruff check .`
Expected: `All checks passed!`

- [ ] **Step 8: Remove the pipenv files**

Run: `git rm Pipfile Pipfile.lock`

- [ ] **Step 9: Commit**

```bash
git add pyproject.toml .python-version uv.lock
git commit -m "build(deps): migrate dependency management from pipenv to uv"
```

(The Trunk pre-commit hook may auto-format; re-stage and amend if it modifies files.)

---

## Task 2: ci-test.yml — run the test workflow with uv

**Files:**

- Modify: `.github/workflows/ci-test.yml:36-58`

- [ ] **Step 1: Replace the Python/pipenv steps**

Replace this block (lines 36-58):

```yaml
- name: Setup Python
  uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6.2.0
  with:
    python-version: "3.13"
    cache: pipenv

- name: Install dependencies
  run: |
    pip install pipenv
    pipenv sync --dev

- name: Diagnostic - check environment
  run: |
    pipenv run pip list
    pipenv run python -c "import cookiecutter; print('cookiecutter import ok')"

- name: Run pytest
  run: pipenv run pytest

- name: Generate coverage badge
  if: always()
  continue-on-error: true
  run: pipenv run genbadge coverage -i coverage.xml -o coverage-badge.svg
```

with:

```yaml
- name: Setup uv
  uses: astral-sh/setup-uv@fac544c07dec837d0ccb6301d7b5580bf5edae39 # v8.2.0
  with:
    enable-cache: true

- name: Install dependencies
  run: uv sync --locked

- name: Diagnostic - check environment
  run: |
    uv pip list
    uv run python -c "import cookiecutter; print('cookiecutter import ok')"

- name: Run pytest
  run: uv run pytest

- name: Generate coverage badge
  if: always()
  continue-on-error: true
  run: uv run genbadge coverage -i coverage.xml -o coverage-badge.svg
```

Notes: `actions/setup-python` is removed entirely — `uv sync` installs Python 3.13 from `.python-version`. `cache: pipenv` would hard-fail once `Pipfile.lock` is gone, so it cannot be kept. setup-uv's `enable-cache: true` caches on `uv.lock`.

- [ ] **Step 2: Lint the workflow**

Run: `trunk check .github/workflows/ci-test.yml`
Expected: no new issues (actionlint/yamllint clean).

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci-test.yml
git commit -m "ci(test): run test workflow with uv"
```

---

## Task 3: ci-security.yml — export audited requirements with uv

**Files:**

- Modify: `.github/workflows/ci-security.yml:36-62`

- [ ] **Step 1: Replace the Python/pipenv/pip-audit steps**

Replace this block (lines 36-62):

```yaml
- name: Setup Python
  uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6.2.0
  with:
    python-version: "3.13"
    cache: pipenv

- name: Install dependencies
  run: |
    pip install pipenv
    pipenv sync --dev

- name: Run pip-audit (HIGH/CRITICAL gate)
  run: |
    pipenv requirements > requirements-ci.txt
    pipenv run pip install pip-audit
    set +e
    pipenv run pip-audit -r requirements-ci.txt --format=json --output pip-audit-report.json
    audit_exit_code=$?
    set -e
    if [ ! -s pip-audit-report.json ]; then
      echo "pip-audit did not produce JSON output"
      exit 1
    fi
    python scripts/enforce_pip_audit_severity.py pip-audit-report.json --min-severity HIGH
    if [ "$audit_exit_code" -ne 0 ]; then
      echo "pip-audit reported vulnerabilities; severity gate applied above"
    fi
```

with:

```yaml
- name: Setup uv
  uses: astral-sh/setup-uv@fac544c07dec837d0ccb6301d7b5580bf5edae39 # v8.2.0
  with:
    enable-cache: true

- name: Run pip-audit (HIGH/CRITICAL gate)
  run: |
    uv export --no-dev --no-emit-project --no-hashes -o requirements-ci.txt
    set +e
    uvx pip-audit -r requirements-ci.txt --format=json --output pip-audit-report.json
    audit_exit_code=$?
    set -e
    if [ ! -s pip-audit-report.json ]; then
      echo "pip-audit did not produce JSON output"
      exit 1
    fi
    python3 scripts/enforce_pip_audit_severity.py pip-audit-report.json --min-severity HIGH
    if [ "$audit_exit_code" -ne 0 ]; then
      echo "pip-audit reported vulnerabilities; severity gate applied above"
    fi
```

Notes:

- No `uv sync` needed: `uv export` works from `uv.lock` alone, `uvx` runs pip-audit in an isolated ephemeral env (replaces the `pipenv run pip install pip-audit` dance), and `scripts/enforce_pip_audit_severity.py` is stdlib-only (argparse/json/urllib — verified), so the runner's `python3` suffices.
- `--no-dev --no-emit-project` keeps the audit surface identical to today's `pipenv requirements`: runtime dependencies at locked versions, project itself excluded.
- `--no-hashes` because pip-audit in `-r` mode treats a hashed requirements file as `--require-hashes`, which rejects the export's environment markers split across resolution branches.

- [ ] **Step 2: Lint the workflow**

Run: `trunk check .github/workflows/ci-security.yml`
Expected: no new issues.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci-security.yml
git commit -m "ci(security): export audited requirements with uv"
```

---

## Task 4: cd-docs.yml — run the docs pipeline with uv

**Files:**

- Modify: `.github/workflows/cd-docs.yml` (lines 12, 70, 74, 84-93, 180, 185, 202, 208-209)

- [ ] **Step 1: Update the push path filter**

Line 12: in the `paths:` list, replace the `- Pipfile` entry with `- uv.lock` (keep the existing 6-space indentation).

- [ ] **Step 2: Update the change-detection regexes**

Line 70, replace `Pipfile$` with `uv\.lock$` inside the existing regex:

```bash
            if grep -Eq '^(regis/|scripts/generate_whats_new\.py$|CHANGELOG\.md$|uv\.lock$|pyproject\.toml$|package\.json$|pnpm-lock\.yaml$|\.github/workflows/cd-docs\.yml$)' "$changed_files_file"; then
```

Line 74, same substitution:

```bash
            if grep -Eq '^(regis/|tests/|uv\.lock$|pyproject\.toml$|\.github/workflows/cd-docs\.yml$)' "$changed_files_file"; then
```

- [ ] **Step 3: Replace the Python setup/install steps**

Replace (lines 84-93):

```yaml
- name: Setup Python
  uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6.2.0
  with:
    python-version: "3.13"
    cache: pipenv

- name: Install Python dependencies
  run: |
    pip install pipenv
    pipenv sync --dev
```

with:

```yaml
- name: Setup uv
  uses: astral-sh/setup-uv@fac544c07dec837d0ccb6301d7b5580bf5edae39 # v8.2.0
  with:
    enable-cache: true

- name: Install Python dependencies
  run: uv sync --locked
```

- [ ] **Step 4: Route remaining run commands through uv**

- Line 180: `pipenv run generate-schema-doc …` → `uv run generate-schema-doc …` (rest of the line unchanged)
- Line 185: `run: pipenv run regis rules list -f markdown -D docs/website/docs/reference/rules` → `run: uv run regis rules list -f markdown -D docs/website/docs/reference/rules`
- Line 202: `run: python scripts/generate_whats_new.py` → `run: uv run python scripts/generate_whats_new.py` (the synced env is guaranteed; the runner's bare `python` no longer is, since setup-python is gone)
- Lines 208-209:

```yaml
uv run pytest --cov --cov-report=xml -q --no-header
uv run genbadge coverage -i coverage.xml -o coverage-badge.svg
```

- [ ] **Step 5: Lint the workflow**

Run: `trunk check .github/workflows/cd-docs.yml`
Expected: no new issues.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/cd-docs.yml
git commit -m "ci(docs): run docs pipeline with uv"
```

---

## Task 5: Dockerfile — install the image venv from uv.lock

**Files:**

- Modify: `Dockerfile:10-38` (python-builder stage)
- Modify: `.github/workflows/ci-image-size.yml:12-13` (path filter)

- [ ] **Step 1: Rewrite the python-builder stage**

Replace lines 10-38 of `Dockerfile` (the whole `python-builder` stage, up to and including the `RUN … pip install …` block) with:

```dockerfile
FROM python:3.11-alpine AS python-builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# uv binary from the official distroless image — builder stage only, never
# shipped in the runtime image.
COPY --from=ghcr.io/astral-sh/uv:0.11.7@sha256:240fb85ab0f263ef12f492d8476aa3a2e4e1e333f7d67fbdd923d00a506a516a /uv /usr/local/bin/uv

# build-base: gcc/musl-dev for any source-wheel fallback
# linux-headers, libffi-dev, openssl-dev: required by cffi/cryptography-style
# C extensions if PyPI has no musl wheel for the version we resolve.
# hadolint ignore=DL3018
RUN apk add --no-cache build-base linux-headers libffi-dev openssl-dev

# uv targets /opt/venv directly; UV_PYTHON pins the image's CPython so uv
# does not fetch a managed interpreter (the repo's .python-version pins 3.13
# for dev, but the image intentionally stays on the 3.11 runtime base).
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON=/usr/local/bin/python3
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /src
COPY pyproject.toml uv.lock ./
COPY regis/ regis/

# Core install only, pinned exactly to uv.lock — the same lock pip-audit
# scans in CI. --no-editable bakes the package into site-packages; --no-dev
# keeps the dev dependency group out of the runtime venv.
SHELL ["/bin/ash", "-o", "pipefail", "-c"]
RUN VERSION=$(awk -F'"' '/^version = / { print $2; exit }' pyproject.toml) && \
    SETUPTOOLS_SCM_PRETEND_VERSION="$VERSION" uv sync --locked --no-dev --no-editable && \
    find /opt/venv -type d -name __pycache__ -prune -exec rm -rf {} + && \
    find /opt/venv -type f -name '*.pyc' -delete
```

Everything from `# Stage 3: tools-fetcher` onward is unchanged. Note: `PIP_NO_CACHE_DIR` is dropped from the ENV (no pip anymore); the dashboard comment block above the old RUN is replaced by the comment shown.

- [ ] **Step 2: Build the slim variant locally**

Run: `docker build --build-arg VARIANT=slim -t regis:uv-slim .`
Expected: build succeeds. Watch the `uv sync` step output: it must say it installed from the lock (`Installed N packages`), not resolve anew.

- [ ] **Step 3: Smoke-test the image**

Run: `docker run --rm regis:uv-slim --help && docker run --rm regis:uv-slim list`
Expected: regis CLI help text, then the analyzer list (HEALTHCHECK command works).

- [ ] **Step 4: Check the size budget**

Run: `docker image inspect regis:uv-slim --format '{{.Size}}' | awk '{printf "%.0f MB\n", $1/1024/1024}'`
Expected: in the same ballpark as before (~156 MB on arm64); must stay under the 200 MB CI ceiling. If it regressed by more than a few MB, inspect `/opt/venv` for unexpected additions before proceeding.

- [ ] **Step 5: Build and smoke the full variant**

Run: `docker build --build-arg VARIANT=full -t regis:uv-full . && docker run --rm regis:uv-full --help`
Expected: build succeeds (same builder stage), help text prints. Ceiling: 520 MB.

- [ ] **Step 6: Update the ci-image-size path filter**

In `.github/workflows/ci-image-size.yml`, replace lines 12-13:

```yaml
- Pipfile
- Pipfile.lock
```

with:

```yaml
- uv.lock
```

- [ ] **Step 7: Lint**

Run: `trunk check Dockerfile .github/workflows/ci-image-size.yml`
Expected: hadolint/actionlint clean (the existing `hadolint ignore=DL3018` carries over).

- [ ] **Step 8: Commit**

```bash
git add Dockerfile .github/workflows/ci-image-size.yml
git commit -m "build(deps): install image venv from uv.lock"
```

---

## Task 6: User-facing docs + agent rules

**Files:**

- Modify: `docs/website/docs/usage/getting-started.md:39-40`
- Modify: `docs/website/docs/usage/integrations/github.md:172-188`
- Modify: `docs/website/docs/reference/playbooks/default/examples/alpine.md:6`
- Modify: `docs/website/docs/reference/playbooks/default/examples/regis-cli.md:6`
- Modify: `.agent/rules/python.md:8`

**Do NOT touch anything under `docs/website/versioned_docs/`.**

- [ ] **Step 1: getting-started.md**

Replace lines 39-40:

```markdown
For developers wanting to contribute to the project, use **Pipenv**:
`pipenv install --dev`
```

with:

```markdown
For developers wanting to contribute to the project, use **[uv](https://docs.astral.sh/uv/)**:
`uv sync`
```

- [ ] **Step 2: github.md workflow example**

Replace the `Set up Python` / `Install regis` / `Run Analysis` steps (lines ~172-188):

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: "3.11"

- name: Install regis
  run: |
    pip install pipenv
    pipenv install --deploy

- name: Run Analysis
  run: |
    pipenv run regis analyze ghcr.io/${{ github.repository }}:latest \
```

with:

```yaml
- name: Set up uv
  uses: astral-sh/setup-uv@v8

- name: Install regis
  run: uv sync --locked --no-dev

- name: Run Analysis
  run: |
    uv run regis analyze ghcr.io/${{ github.repository }}:latest \
```

(The remaining `--auth/--html/--meta` lines of the `Run Analysis` block are unchanged. This is a user-facing example, so the action is tag-pinned like the other `@vN` examples on that page, not SHA-pinned.)

- [ ] **Step 3: Playbook examples**

In `alpine.md` line 6 and `regis-cli.md` line 6, replace the `pipenv run regis analyze …` prefix with `uv run regis analyze …` (rest of each command unchanged).

- [ ] **Step 4: Agent rules**

In `.agent/rules/python.md` line 8, replace:

```markdown
- Use [pipenv](https://pipenv.pypa.io/en/latest)
```

with:

```markdown
- Use [uv](https://docs.astral.sh/uv/)
```

- [ ] **Step 5: Verify no stale pipenv references remain in live docs**

Run: `grep -rn "pipenv" docs/website/docs .agent/ CLAUDE.md | grep -v versioned_docs`
Expected: only the `CLAUDE.md` hits remain (handled in Task 7).

- [ ] **Step 6: Commit**

```bash
git add docs/website/docs .agent/rules/python.md
git commit -m "docs(website): switch contributor and example commands to uv"
```

---

## Task 7: CLAUDE.md + memory bank + Serena memories

**Files:**

- Modify: `CLAUDE.md` (Commands block)
- Modify: `docs/memory-bank/techContext.md:40-82`
- Modify: `docs/memory-bank/dependencies.md:29,38,50`
- Modify: `.serena/memories/project_overview.md:5`
- Modify: `.serena/memories/suggested_commands.md:5-10`

- [ ] **Step 1: CLAUDE.md Commands block**

Replace the six pipenv lines of the Commands code block:

```bash
pipenv install --dev          # Install all dependencies
pipenv run pytest             # Full run with coverage (fails if total < 90% OR any file < 90%)
pipenv run pytest --no-cov    # Fast loop — disables both the global and per-file coverage gates
pipenv run ruff check .       # Lint
pipenv run ruff format .      # Format
pipenv run regis --help       # Run CLI locally
```

with:

```bash
uv sync                       # Install all dependencies (incl. dev group)
uv run pytest                 # Full run with coverage (fails if total < 90% OR any file < 90%)
uv run pytest --no-cov        # Fast loop — disables both the global and per-file coverage gates
uv run ruff check .           # Lint
uv run ruff format .          # Format
uv run regis --help           # Run CLI locally
```

(`trunk` and `pnpm` lines unchanged.)

- [ ] **Step 2: techContext.md**

- Line 41: `- \`pipenv\` — Python dependency management`→`- \`uv\` — Python dependency management (lockfile: \`uv.lock\`, dev deps in PEP 735 \`[dependency-groups]\`)`
- Line 62: `- \`pipenv\``→`- \`uv\``
- Lines 68-80 command block: apply the same six command substitutions as CLAUDE.md above.

- [ ] **Step 3: dependencies.md**

- Line 29: `Linting and formatting via Pipfile` → `Linting and formatting (dev dependency group)`
- Line 38: `- Pipfile currently targets Python 3.13 for the local environment` → `- \`.python-version\` pins Python 3.13 for the local environment (uv)`
- Line 50: `- \`regis\` package is editable in the local environment via Pipfile`→`- \`regis\` package is installed editable in the local environment by \`uv sync\``

- [ ] **Step 4: Serena memories**

- `.serena/memories/project_overview.md` line 5: `Python (pipenv)` → `Python (uv)`
- `.serena/memories/suggested_commands.md` lines 5-10: same six command substitutions as CLAUDE.md.

- [ ] **Step 5: Final repo-wide sweep**

Run: `grep -rln "pipenv" --exclude-dir=versioned_docs --exclude-dir=node_modules --exclude-dir=.git . | grep -v "docs/superpowers/" | grep -v CHANGELOG.md`
Expected: no output. (Specs/plans keep their historical mentions; CHANGELOG is generated.)

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md docs/memory-bank .serena/memories
git commit -m "docs(memory-bank): record pipenv-to-uv migration"
```

---

## Task 8: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Clean-room sync**

Run: `rm -rf .venv && uv sync --locked && uv run pytest`
Expected: fresh env from the lock, full suite PASS, coverage gates green.

- [ ] **Step 2: Full lint**

Run: `trunk check`
Expected: clean (or only pre-existing findings).

- [ ] **Step 3: pip-audit pipeline smoke (mirrors ci-security locally)**

```bash
uv export --no-dev --no-emit-project --no-hashes -o /tmp/requirements-ci.txt
uvx pip-audit -r /tmp/requirements-ci.txt --format=json --output /tmp/pip-audit-report.json || true
python3 scripts/enforce_pip_audit_severity.py /tmp/pip-audit-report.json --min-severity HIGH
```

Expected: export succeeds, pip-audit produces JSON, severity gate passes (no HIGH/CRITICAL). If the gate fails, the lock resolved a vulnerable version — fix by adding a floor to `[tool.uv].constraint-dependencies` and re-running `uv lock`, then re-run Task 1 steps 4-6.

- [ ] **Step 4: Confirm the branch is rebased on latest main**

Run: `git fetch origin main && git log --oneline origin/main..HEAD`
Expected: only this migration's commits. If `main` moved, rebase: `git rebase origin/main` (repo rule: always rebase, never merge main back).

- [ ] **Step 5: Done — hand off**

Use the superpowers:finishing-a-development-branch skill to open the PR. PR title: `build(deps): migrate from pipenv to uv`. Remember the repo rule: **delete this plan file from the branch before merge** (specs survive, plans don't).
