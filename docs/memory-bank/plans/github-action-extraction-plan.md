# Plan — GitHub Action Extraction to `trivoallan/regis-action`

## Context

The Regis GitHub Action lived at the core repo root (`action.yml`, a pure-YAML
**composite** action) and was published on the Marketplace as
`trivoallan/regis@vX`. This coupled the action's release cadence to the core,
forced a SHA-pinning exception in `ci-lint.yml`, and prevented clean action
versioning. This work extracts the action into a dedicated, independently
versioned repository `trivoallan/regis-action`, mirroring the 2026-06-01
`regis-dashboard` decouple (see `decisionLog.md`).

Validated decisions:

- **Full extraction**: create `trivoallan/regis-action` and host the action there.
- **Clean break** core-side: `action.yml` removed (breaking); consumers migrate to `trivoallan/regis-action@v1`.
- **Independent versioning**: `v1.x` via release-please; the `version:` input still targets a core image `ghcr.io/trivoallan/regis:<tag>`.
- **Fresh start**: no `git filter-repo` (content is trivial).

## Part A — New repo `trivoallan/regis-action`

Files (staged under `regis-action-staging/` in the core branch pending push):

1. `action.yml` — verbatim copy of the core action (references `ghcr.io/trivoallan/regis:${version}`, unchanged).
2. `README.md` — usage + inputs/outputs + migration note, `uses: trivoallan/regis-action@v1`.
3. `LICENSE` (MIT), `.gitignore`.
4. `.github/workflows/ci.yml` — yamllint + actionlint + dogfood (`uses: ./` on `ghcr.io/trivoallan/regis:latest`).
5. `.github/workflows/release-please.yml` — `release-type: simple`.
6. `.github/workflows/tag-major.yml` — moves the floating `v1` tag on release.
7. `release-please-config.json` + `.release-please-manifest.json` (seed `1.0.0`).
8. `CHANGELOG.md` seed.

**Manual setup (out of code)**: repo CI secrets (App token / PAT to trigger
downstream CI, as for regis-dashboard), branch protection, Marketplace
publication from a tagged release, and the initial `v1.0.0` + `v1` tags.

## Part B — Core cleanup (branch `claude/github-action-extraction-6zdu5`)

- Remove `action.yml` and `.github/workflows/ci-action-dogfood.yml`.
- `ci-lint.yml`: drop the `trivoallan/regis@` SHA-pinning exception.
- `README.md` + `docs/website/docs/usage/integrations/github.md`: repoint `uses:` to `trivoallan/regis-action@v1`, add migration note. **Leave `versioned_docs/` snapshots intact.**
- Memory Bank: `decisionLog.md`, `activeContext.md`, `progress.md`, this plan.
- Commit: `feat(ci)!` (breaking → pre-major minor bump).

## Status / Outcome (2026-06-04)

- `trivoallan/regis-action` repo **created** via the GitHub API.
- Pushing files to it was **blocked** by the session MCP repo scope
  (`trivoallan/regis` only) — no `add_repo`/`list_repos` tool available to
  expand scope. New-repo content staged under `regis-action-staging/`.
- Core cleanup (Part B) **completed** on the branch.

## Follow-ups (manual)

1. Push `regis-action-staging/` content to `trivoallan/regis-action` `main`
   (or re-run with an expanded MCP scope), then delete the staging dir.
2. Wire repo secrets + branch protection; cut the initial `v1.0.0` release so
   `@v1` resolves; (re)publish to the Marketplace from the new repo.
3. Verify a third-party `uses: trivoallan/regis-action@v1` run end-to-end.

## Verification

- Core: `pipenv run ruff check .`, `trunk check`, `pipenv run pytest --no-cov` green.
- `grep -RIn 'trivoallan/regis@' . :!docs/website/versioned_docs` → only migration notes remain.
- New repo (post-push): CI `ci.yml` green (actionlint + dogfood); release-please PR appears; `tag-major.yml` maintains `v1`.
