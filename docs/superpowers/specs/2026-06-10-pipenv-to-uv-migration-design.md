# Pipenv → uv migration — Design

**Date**: 2026-06-10
**Status**: Approved
**Commit scope**: `build(deps)`

## Goal

Replace pipenv with [uv](https://docs.astral.sh/uv/) as the project's Python
environment and dependency manager, across local development, CI, the Docker
image, and documentation — in a single PR.

## Context

- `pyproject.toml` is already the source of truth for runtime dependencies and
  ships a `dev` extra. The `Pipfile` partially duplicates it, installs the
  project editable, and carries dev-only tooling plus transitive security
  floor pins.
- Three workflows install through pipenv: `ci-test.yml`, `ci-security.yml`
  (lock export → pip-audit), `cd-docs.yml`.
- The Docker `python-builder` stage copies `Pipfile`/`Pipfile.lock` but
  installs with plain `pip install .` — the audited lock never governed the
  shipped image. The copy is vestigial; builds resolve dependencies freely at
  build time.
- Nothing outside the Pipfile and the pipenv CI flows references
  `regis[dev]`, so the `dev` extra can be removed safely.

## Decisions

1. **Full scope, one PR**: Pipfile removed; lockfile, CI, Dockerfile,
   CLAUDE.md, `.agent/rules`, current docs, and memory bank all migrated.
   `docs/website/versioned_docs/` are frozen snapshots and stay untouched.
2. **Dev dependencies move to PEP 735 `[dependency-groups]`** (`dev` group,
   uv's native default for `uv sync`). The published
   `[project.optional-dependencies].dev` extra is removed.
3. **The Docker image installs from `uv.lock`** (`uv sync --locked`), closing
   the gap between the lock pip-audit scans and the dependencies that ship.

## Design

### 1. Dependency files

- Delete `Pipfile` and `Pipfile.lock`.
- Add `uv.lock` (committed) and `.python-version` pinned to `3.13`
  (carries over the Pipfile's `[requires]` pin; `requires-python>=3.10`
  unchanged, the lock stays universal).
- Pipfile content triage:
  - Runtime duplicates (`click`, `requests`, `jsonschema`, `semver`,
    `json-logic-qubit`, `pyyaml`, `jinja2`, `cookiecutter`, `referencing`,
    `ruamel.yaml`): dropped — already in `[project].dependencies`.
  - Editable installs (`regis-cli`, `regis[dev]`): replaced by uv's project
    mode (`uv sync` installs the project editable by default).
  - Dev tooling → `[dependency-groups].dev`: `pytest>=7.4`, `pytest-cov>=4.1`,
    `responses>=0.24`, `genbadge[coverage]>=1.1`, `httpx>=0.28`, `ruff`,
    `jsonschema2md`, `json-schema-for-humans` (used by cd-docs),
    `types-PyYAML`, `types-requests`, `types-jsonschema`.
  - Transitive security floors → `[tool.uv].constraint-dependencies`:
    `urllib3>=2.7.0`, `idna>=3.15`, `pillow>=12.2.0`, `chardet>=5.0.0`,
    `charset-normalizer>=2.0.0`. Constraints shape resolution without
    polluting the package's declared dependencies.
  - Remove `[project.optional-dependencies].dev`.

### 2. CI workflows

Common pattern: replace `pip install pipenv` + `setup-python` `cache: pipenv`
with `astral-sh/setup-uv` (SHA-pinned, repo convention), built-in cache keyed
on `uv.lock`, then `uv sync --locked`.

- **ci-test.yml**: `uv run pytest`, `uv run genbadge coverage …`, sanity
  steps (`uv pip list`, cookiecutter import check) via `uv run`.
- **ci-security.yml**: `pipenv requirements > requirements-ci.txt` becomes
  `uv export --no-dev --no-emit-project -o requirements-ci.txt` (same scope
  as today: runtime dependencies only, project itself excluded). pip-audit
  invocation and `enforce_pip_audit_severity.py` unchanged.
- **cd-docs.yml**: sync + `uv run generate-schema-doc`, `uv run regis rules
  list …`, `uv run pytest`/`genbadge`; path filters and change-detection
  regexes referencing `Pipfile` switch to `uv.lock`.

### 3. Dockerfile (python-builder stage)

- Drop the vestigial `Pipfile Pipfile.lock` from the `COPY`; copy
  `pyproject.toml` + `uv.lock` instead.
- Bring uv into the builder stage only:
  `COPY --from=ghcr.io/astral-sh/uv:<version>@sha256:<digest> /uv /usr/local/bin/uv`
  (exact version and digest resolved at implementation time, SHA-pinned like
  the other actions/images in this repo).
- Install with `UV_PROJECT_ENVIRONMENT=/opt/venv uv sync --locked --no-dev
  --no-editable`, keeping `SETUPTOOLS_SCM_PRETEND_VERSION` (same awk
  extraction) and the `__pycache__`/`*.pyc` prune.
- Runtime stages (`final-slim`, `final-full`) unchanged; uv never reaches the
  final image, so the 200/520 MB size gates are unaffected.
- Outcome: the image ships exactly the versions pip-audit audits.

### 4. Docs, agent rules, memory

- `CLAUDE.md` Commands block: `uv sync`, `uv run pytest [--no-cov]`,
  `uv run ruff check/format .`, `uv run regis --help`.
- `.agent/rules/python.md`: pipenv reference → uv.
- `docs/website/docs/`: `usage/getting-started.md`,
  `usage/integrations/github.md`, and the two playbook examples
  (`alpine.md`, `regis-cli.md`) switch `pipenv` commands to `uv`.
  **`versioned_docs/` are frozen — do not touch.**
- Memory bank: `techContext.md` updated; Serena memories
  (`project_overview`, `suggested_commands`) refreshed.

### 5. Validation

- `uv run pytest` full suite — coverage gates (global + per-file ≥ 90 %)
  unchanged.
- `trunk check` clean.
- Docker build of both variants under the size ceilings; smoke
  `docker run … --help` (and the existing `ci-tools-fetch-smoke.yml` covers
  the cold-fetch path on PR).
- `uv export` output consumable by pip-audit (run locally once before
  relying on CI).

## Risks

- **Resolution drift**: the first `uv lock` may pick different versions than
  the current pipenv environment. The test suite is the gate; pin floors via
  constraints if a regression surfaces.
- **Project build path**: `uv sync` builds the project with the same
  setuptools backend as pip, so behavior should be identical — including the
  existing quirk that `README.md` is not copied into the Docker build context
  despite `readme = "README.md"`. Verify at build time.
- **Versioning**: `build(deps)` per the defined scopes (environment
  management). Non-breaking for users — the published package and the image
  keep the same contract; the removed `dev` extra was never documented or
  referenced.

## Out of scope

- Switching the build backend (stays setuptools + setuptools-scm).
- Renovate/Dependabot configuration changes (uv.lock support to be verified
  separately if needed).
- The frozen `versioned_docs/` snapshots.
