xs# M002/S05: Dependency Upgrade — Slice Completion Record

**Milestone:** M002
**Slice:** S05
**Title:** Dependency upgrade
**Completed:** 2026-04-22
**Status:** DONE

## One-liner

Refreshed Pipfile.lock, root pnpm-lock.yaml, and all 11 GitHub Actions workflow SHA pins to their latest compatible versions.

## Narrative

Three parallel upgrade tracks executed cleanly. T01: `pipenv update` refreshed the Python lock file; marshmallow stayed on 3.26.2 (no v4 pin needed); 460 pytest tests pass at 90.74% coverage; ruff auto-fixed one unused import in tests/commands/test_analyze_markdown.py. T02: `pnpm update` at workspace root refreshed the single shared pnpm-lock.yaml (15 packages added, 2 removed); both docs/website and apps/dashboard builds succeeded; webpack stays pinned at 5.105.4 (D007) and tailwindcss stays at ^3.4.19 (v4 exclusion). T03: pinact 3.9.0 ran with `--exclude "trivoallan/regis"` (required — ci-action-dogfood.yml references the project itself); 11 of 12 workflow files updated; 3 major version bumps reviewed and accepted (attest-build-provenance v2→v4 backward-compatible wrapper; fetch-metadata v2→v3 Node.js runtime-only change; paths-filter v3→v4 Node.js runtime-only change).

## Verification

- `pipenv run pytest`: 460 passed, 90.74% coverage (≥90% threshold met).
- `pipenv run ruff check .`: 0 issues.
- `pipenv run regis --help`: exit 0.
- `cd docs/website && pnpm build`: exit 0, [SUCCESS].
- GitHub Actions SHA pin check: `grep -rh 'uses:.*@' .github/workflows/*.yml | grep -v 'trivoallan/regis' | grep -vE '@[0-9a-f]{40}' | grep -v '^#'` returns empty.
- `git diff --stat .github/workflows/`: 11 files changed, 48 insertions(+), 48 deletions(-).

## Key Decisions

- marshmallow stays on 3.26.2 — pipenv update did not pull in v4, so no Pipfile pin was needed.
- pnpm workspace uses a single root-level pnpm-lock.yaml — no per-directory lock files exist; run pnpm update at workspace root.
- pinact must be invoked with `--exclude 'trivoallan/regis'` because ci-action-dogfood.yml references the project itself as a GitHub Action and cannot be SHA-pinned.
- actions/attest-build-provenance v2→v4 accepted: v4 is a backward-compatible wrapper with unchanged inputs/outputs.
- dependabot/fetch-metadata v2→v3.1.0 accepted: only breaking change is Node.js v20→v24 runtime upgrade.
- dorny/paths-filter v3→v4.0.1 accepted: only breaking change is Node.js v24 runtime upgrade.

## Patterns Established

- `pinact run --exclude 'trivoallan/regis' --update` is the correct invocation for this repo.

## Deviations

T02 plan assumed per-directory pnpm-lock.yaml files; in reality the project uses a pnpm workspace with a single root-level lock file. T03 required --exclude flag not in original plan steps.

## Known Limitations

Pre-existing: @tremor/react 3.18.7 has unmet peer dependency on react@^18 (project runs React 19). This is not introduced by this upgrade.

## Follow-ups

None.

---

# S05: Dependency upgrade — UAT

**Milestone:** M002
**Written:** 2026-04-22

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: All deliverables are lock file updates and workflow file patches — there is no new runtime behavior to test. Correctness is proved by the test suite, build tools, and static analysis passing against the refreshed deps.

## Preconditions

- Working directory: `/Users/tristan/Documents/Workspaces/trivoallan/regis`
- pipenv virtualenv installed (`pipenv install --dev`)
- pnpm available at workspace root
- pinact available (`brew install suzuki-shunsuke/pinact/pinact`)

## Smoke Test

`pipenv run pytest --no-cov -q 2>&1 | tail -1` — should print `460 passed` (or more).

## Test Cases

### 1. Python test suite passes at ≥90% coverage

1. Run `pipenv run pytest 2>&1 | tail -5`
2. **Expected:** Output includes `460 passed` and `Total coverage: 90.74%` (or higher); exit code 0.

### 2. Ruff linter is clean

1. Run `pipenv run ruff check .`
2. **Expected:** No output (or only the deprecation warning about top-level settings); exit code 0.

### 3. Regis CLI loads correctly after upgrade

1. Run `pipenv run regis --help`
2. **Expected:** Usage text starting with `Usage: regis [OPTIONS] COMMAND [ARGS]...`; exit code 0.

### 4. Docs site builds with refreshed Node packages

1. Run `cd docs/website && pnpm build 2>&1 | tail -3`
2. **Expected:** Output contains `[SUCCESS] Generated static files in "build"`; exit code 0.

### 5. All GitHub Actions uses lines are SHA-pinned

1. Run `grep -rh "uses:.*@" .github/workflows/*.yml | grep -v "trivoallan/regis" | grep -vE "@[0-9a-f]{40}" | grep -v "^#"`
2. **Expected:** Empty output (all action refs are 40-char SHAs); exit code 0.

### 6. 11 workflow files were updated

1. Run `git diff --stat HEAD~1 .github/workflows/` (or compare against the pre-S05 commit)
2. **Expected:** At least 11 workflow files appear in the diff with SHA pin changes; no workflow file loses its version comment.

## Edge Cases

### marshmallow v4 not pulled in

1. Run `pipenv run pip show marshmallow | grep Version`
2. **Expected:** Version 3.x (e.g. `3.26.2`) — not 4.x. No `marshmallow = "<4"` pin is needed in Pipfile.

### webpack pin preserved in docs/website

1. Run `grep '"webpack"' docs/website/package.json`
2. **Expected:** `"webpack": "5.105.4"` (exact pin, not a range).

### tailwindcss stays on v3 in apps/dashboard

1. Run `grep '"tailwindcss"' apps/dashboard/package.json` (if directory exists)
2. **Expected:** `"tailwindcss": "^3.x.x"` — not `^4`.

## Failure Signals

- `pipenv run pytest` exits non-zero or coverage < 90% — a package upgrade broke a test or changed behavior.
- `pnpm build` in docs/website exits non-zero — a Node package update introduced a breaking change.
- `grep` for unpinned SHA lines returns any output — pinact missed a workflow file.

## Not Proven By This UAT

- Runtime behavior of GitHub Actions in CI — the SHA pin updates are verified statically; actual CI execution is left to the push-triggered pipeline.
- pip-audit gate — verified in CI (ci-test.yml); no HIGH/CRITICAL CVEs are expected since no new packages were added.

## Notes for Tester

The `@tremor/react 3.18.7` peer-dependency warning (needs react@^18, project is on 19) is pre-existing and unrelated to this upgrade. The `vscode-languageserver-types` critical dependency webpack warning in the docs build is also pre-existing.
