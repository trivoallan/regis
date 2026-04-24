# Improve the Validation-MR Pipeline (before backport into regis)

## Context

A downstream consumer pipeline orchestrates `regis` analysis with a
human-in-the-loop validation step (analyze → archive → validate via GitLab MR
labels → apply → pages). This richer 5-stage pattern is **simpler and better**
than the current 3-stage `request → analyze → report` template shipped in
`regis/cookiecutters/gitlab-ci/`, and is planned for backport. Before the
backport, this plan collects improvements — correctness fixes, security
hardening, simplifications, and small regis CLI enhancements — so that the
version we ship is clean.

## Findings on the shared YAML

### Real bugs (will break at runtime)

1. **`apk` on a Debian image (apply_validation)** — the regis Docker image is
   `python:3.14-slim` (`Dockerfile:13`), not Alpine. The line

   ```sh
   apk add --no-cache jq curl 2>/dev/null || true
   ```

   silently no-ops. `curl` is baked in (`Dockerfile:34`) but **`jq` is not
   installed**, so every subsequent `jq` call in `apply_validation` fails. The
   `|| true` above masks the root cause; the job dies on the first `jq` line.
   Additionally, the image runs as non-root user `regis` (`Dockerfile:94`), so
   even `apt-get install` would fail without `sudo`.

2. **Dashboard doesn't refresh after validation** — `apply_validation` pushes
   with `-o ci.skip` to avoid re-triggering. In the same pipeline, `pages`
   runs in the `deploy` stage after `apply`, but GitLab jobs each re-checkout
   `CI_COMMIT_SHA` (the original merge commit) — they do **not** see the
   commit `apply_validation` just pushed. Result: the published dashboard
   still shows `validation.status = pending`.

3. **Loose rule match on `apply_validation`** —
   `$CI_COMMIT_MESSAGE =~ /validation\//` fires on **any** commit message
   containing that substring (including an unrelated commit titled "update
   validation/foo docs"). The job then wastes a pipeline (or worse, fails
   noisily when no MR matches the SHA).

### Correctness / robustness gaps

4. **Metadata is clobbered on rerun** — `regis analyze --rerun metadata`
   **replaces** `report.metadata` wholesale
   (`regis/commands/analyze.py:283-285`). The pipeline works around this by
   reading the existing metadata and merging with `jq` before calling regis.
   This is the biggest source of shell complexity in `apply_validation`.

5. **Fragile stdout parsing** — `regis archive add` prints
   `Archived to <path>` (`regis/commands/archive.py:66`); the pipeline parses
   it with `sed -n 's|^Archived to ||p' | head -1`. Any log line reordering
   breaks it.

6. **`eval regis analyze ... $META_ARGS`** — `eval` of shell-interpolated
   metadata is a code-injection risk if any validator's username or free-text
   meta contains backticks, `$(...)`, etc.

7. **No retry on `git pull --ff-only` + `git push`** — a concurrent push to
   `main` between fetch and push aborts the job. `archive_report` and
   `apply_validation` both do this once.

8. **Branch name collision** — `validation/<archive>/<timestamp>` with
   second-precision timestamps collides if two analyses complete within the
   same second.

9. **`.validations/*.yaml` markers accumulate on `main`** — never cleaned up
   after merge.

### Security

10. **Label gate is spoofable** — any user with Developer role can apply
    `validated` / `rejected` labels on an MR. True validation authority
    requires GitLab **scoped labels** restricted to Maintainers, or an
    allow-list of approvers checked in `apply_validation`.

11. **Informal `.validations/*.yaml` marker** — no schema, parsed with `grep`
    - `sed`. Any malformed marker crashes `apply_validation` with a cryptic
      error.

12. **`REGIS_CI_TOKEN` is a group-level Maintainer token** with
    `api + write_repository`. Could be scoped to the single repo.

### Simplification / DRY

13. `ARCHIVE_NAME` case-mapping (`hub → catalogue`, `hub_private → demandes`)
    is duplicated in three jobs. Promote to a top-level variable or a
    single-source lookup.

14. `MR_DESC` for DEA/POC only differs by the emoji/prefix. A single template
    - one variable would remove the whole `if/else` block.

15. `[skip ci]` in commit messages is redundant with `-o ci.skip`. Pick one.

## Improvement plan

### A. Patch the YAML in-place (no regis code changes required)

- **Install `jq` correctly in `apply_validation`.** Drop the `apk` line;
  switch the job image to an alpine base (`alpine:3`) for the shell/API
  work, **or** keep the regis image and install `jq` via
  `apt-get install -y --no-install-recommends jq` (requires root override —
  add `docker_user: "0"` in `.tags` or a custom runner config). Preferred:
  use the alpine image for `apply_validation` — regis is only needed inside
  this job for the final `regis analyze --rerun metadata`, so split that into
  a dedicated child job that uses `$REGIS_IMAGE` and receives the merged
  metadata as an artifact.

- **Fix the `pages` staleness.** Make `apply_validation` declare the updated
  `report.json` (or the full `static/archives/…` subtree) as an artifact and
  add `needs: [apply_validation]` on `pages` with `dependencies:
[apply_validation]`. Then `cp -r` in `pages` overwrites the old files with
  the artifact before zipping. This removes the dependency on the git state.

- **Tighten the `apply_validation` rule.** Replace the `=~ /validation\//`
  check with an API lookup: the job still runs on every `main` push, but
  exits `0` immediately if the associated MR's `source_branch` does not start
  with `validation/`. This is already partially implemented lower in the job
  — move the check _before_ the `case` and remove the message-regex rule.

- **Retry `git push` with exponential backoff** (2s, 4s, 8s, 16s) in both
  `archive_report` and `apply_validation`, matching the repo convention.

- **Lengthen the branch-name timestamp** to include `$CI_JOB_ID` (or
  nanoseconds). `validation/<archive>/<timestamp>-<job_id>`.

- **Clean up the marker** — in `apply_validation`, `git rm
.validations/${TIMESTAMP}.yaml` before committing the rerun, so merged
  validations don't leave residue.

- **De-duplicate `ARCHIVE_NAME` and `MR_DESC`.** Add YAML anchors / `.hidden`
  jobs; move the `ctx → archive` mapping to a single bash function in a
  `before_script` sourced by the three jobs.

- **Drop `[skip ci]` from commit messages**; keep only `-o ci.skip` on pushes.

- **Replace `eval regis analyze … $META_ARGS`** with a loop that builds
  `regis` argv safely, or pipe the merged metadata as a JSON file and read it
  with a new flag (see B.1).

### B. Small regis CLI enhancements (make the pipeline shorter + safer)

These are optional but remove significant shell complexity and eliminate the
`eval` and `jq`-merge dances. Each is a small, testable PR.

1. **`regis analyze --rerun metadata --merge-meta`** — when set, merge new
   `--meta` values into `existing_report["metadata"]` instead of replacing
   it. File: `regis/commands/analyze.py:283-285`. One-line behavior change
   guarded by a flag, plus tests in `tests/commands/test_analyze_rerun.py`
   (new file). Eliminates the `EXISTING_META = jq …` block in
   `apply_validation`.

2. **`regis analyze --rerun metadata --meta-file <path>`** — read metadata
   from a JSON/YAML file; dot-notation flattening already in `_parse_meta`
   can be reused. Removes the need for `$META_ARGS` and `eval`. File:
   `regis/commands/analyze.py:56-64`.

3. **`regis archive add --json`** — emit a structured line like
   `{"report_path": "/abs/path", "manifest": "/abs/manifest.json"}` so the
   pipeline reads it with `jq -r .report_path`. File:
   `regis/commands/archive.py:56-67`. Backwards-compatible (default output
   unchanged).

4. **`regis validation marker write|read`** (new subcommand group) — writes
   the `.validations/<id>.json` marker validated against a schema
   (`regis/schemas/validation_marker.schema.json`) and reads it back. Removes
   the `grep -E '^report_path:' | sed …` parser from `apply_validation` and
   gives the marker a first-class format. Optional; schedule for phase 2.

### C. Security hardening (document + enforce)

- **GitLab scoped labels** — document the setup in
  `docs/website/docs/usage/integrations/gitlab.md`: the `validated` and
  `rejected` labels should be scoped (`decision::validated`,
  `decision::rejected`) with Maintainer-only edit rights.

- **Approver allow-list check** — in `apply_validation`, after extracting
  `VALIDATOR`, assert `$VALIDATOR` belongs to the `regis-validators` group
  (env var `REGIS_VALIDATORS=user1,user2`). Reject if not.

- **Narrow `REGIS_CI_TOKEN` scope** — recommend a project-level token with
  the minimum scopes: `api` on the archive repo, no group access.

### D. Observability

- **MR comment on failure** — when `apply_validation` exits 1 (missing
  label, wrong approver, etc.), post a comment to the MR explaining why.
  Uses the existing `REGIS_CI_TOKEN` + `CI_MERGE_REQUEST_IID`.

- **Structured status trailer** — in the rerun commit message, include
  `Validation-MR: <iid>` and `Validation-Status: validated|rejected`, so git
  log alone tells the audit story.

## Critical files

| File                                                                         | Role in this plan                                             |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------- |
| `.gitlab-ci.yml` (downstream consumer pipeline)                              | Primary target for patches A                                  |
| `regis/commands/analyze.py` (L56-64, 232-301)                                | Home of `--merge-meta` and `--meta-file` (B.1 + B.2)          |
| `regis/commands/archive.py` (L45-67)                                         | Home of `--json` output (B.3)                                 |
| `regis/schemas/`                                                             | New `validation_marker.schema.json` (B.4, phase 2)            |
| `regis/cookiecutters/gitlab-ci/{{cookiecutter.project_slug}}/.gitlab-ci.yml` | Target for the eventual backport (out of scope for this plan) |
| `docs/website/docs/usage/integrations/gitlab.md`                             | Document scoped labels + approver allow-list (C)              |

## Recommended sequencing

1. **Phase 1 — patch the YAML only (A)**: self-contained, no regis release
   needed. Unblocks production.
2. **Phase 2 — ship regis CLI enhancements B.1–B.3** together in one minor
   release (e.g., 0.30.0). Update the patched YAML to use them.
3. **Phase 3 — `regis validation` subcommand (B.4) + docs (C) + MR comment
   on failure (D)**: polish before backporting into the cookiecutter.
4. **Phase 4 (out of scope here) — backport** the improved YAML into
   `regis/cookiecutters/gitlab-ci/` (possibly as a second template
   `gitlab-ci-validation/` to keep the minimal one around).

## Verification

- **YAML patches (A)**: run the pipeline on a dry-run fork with three
  scenarios — (i) `validated` label, (ii) `rejected` label, (iii) no label.
  Confirm: (i)+(ii) succeed, report metadata merged correctly, dashboard
  shows new status; (iii) fails with a clear error. Check that `pages` shows
  the updated status for (i) and (ii).
- **`--merge-meta` (B.1)**: unit tests in `tests/commands/test_analyze_rerun.py`
  covering (a) existing keys preserved, (b) new keys added, (c) conflicting
  keys overwritten. Run `pipenv run pytest`.
- **`archive add --json` (B.3)**: unit test asserting the first stdout line
  parses as JSON with `report_path` + `manifest` keys.
- **End-to-end**: after Phase 2, re-run the three-scenario pipeline against
  the new CLI and confirm `apply_validation` is now free of `jq` metadata
  merging and of `eval`.
