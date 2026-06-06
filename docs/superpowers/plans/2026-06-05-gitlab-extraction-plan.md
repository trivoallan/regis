# GitLab Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the entire GitLab integration out of the `regis` core into a dedicated `trivoallan/regis-gitlab` repo (a GitHub-hosted `include: remote` CI template that posts to the MR CI-natively), then remove the GitLab story from the core — dropping the `python-gitlab` dependency.

**Architecture:** Mirrors the `regis-action` extraction. Single branch / single core PR with a **manual gate in the middle**: Part A authors the `regis-gitlab` content under `regis-gitlab-staging/`; the maintainer pushes it to the real repo and cuts `v1`; Part B removes the GitLab story from the core and points the docs at `regis-gitlab@v1`, then deletes the staging dir. The template reproduces today's `regis gitlab update-mr` behaviour (MR comment + coloured labels + description checklists) with `curl`+`jq` instead of `python-gitlab`.

**Tech Stack:** GitLab CI YAML, POSIX sh (busybox/alpine), `curl`, `jq`, GitHub Actions (release-please), Python/Click (core removal), pytest.

**Spec:** `docs/superpowers/specs/2026-06-05-gitlab-extraction-design.md`.

**Branch:** fresh branch off the latest `main` (e.g. `tritri/gitlab-extraction`).

**GUARDRAIL (absolute):** never read, stage, commit, or push the core repo's **root** `.gitlab-ci.yml` — it is a confidential client example. The extracted template derives from the cookiecutter `regis/cookiecutters/gitlab-ci/`, never from that file.

---

## Part A — Author the `regis-gitlab` content (staging)

All Part-A files live under `regis-gitlab-staging/` in the core repo (the maintainer relocates them to the real repo at the manual gate). Nothing under `regis-gitlab-staging/` ships in the core package.

### Task A1: Scaffold the staging tree and README

**Files:**

- Create: `regis-gitlab-staging/README.md`
- Create: `regis-gitlab-staging/.gitignore`

- [ ] **Step 1: Create the README** (absorbs the current "Guide GitLab CI" + `CI-VARIABLES.md`)

Create `regis-gitlab-staging/README.md`:

````markdown
# regis-gitlab

Reusable GitLab CI template that runs [Regis](https://github.com/trivoallan/regis)
container-image security analysis on a merge request and posts the results back
to the MR — comment, labels, and a checklist in the description.

Versioned independently from the Regis core; consume it with `include: remote`.

## Usage

Add to your project's `.gitlab-ci.yml`:

```yaml
include:
  - remote: "https://raw.githubusercontent.com/trivoallan/regis-gitlab/v1/templates/regis-mr.yml"

variables:
  REGIS_IMAGE: "ghcr.io/trivoallan/regis:latest" # pin a tag in production
  REGIS_PLAYBOOK: "playbook.yaml"
```

Commit a `playbook.yaml` to your repo (scaffold one with `regis bootstrap playbook`).

## Required CI/CD variables

| Variable         | Required | Description                                                                 |
| ---------------- | -------- | --------------------------------------------------------------------------- |
| `GITLAB_TOKEN`   | Yes      | Project/group access token with `api` scope (posts comments, labels, push). |
| `IMAGE_URL`      | Web run  | Image to analyze when triggering the pipeline manually (web UI).            |
| `REGIS_IMAGE`    | No       | Regis image (default `ghcr.io/trivoallan/regis:latest`).                    |
| `REGIS_PLAYBOOK` | No       | Playbook path (default `playbook.yaml`).                                    |

## How it works

1. **request** (web trigger): creates a `regis/analyze/<ts>` branch + MR carrying the image URL.
2. **analyze** (MR event): runs `regis analyze --html` into `reports/`.
3. **report** (MR event): commits the report to the branch and posts to the MR
   (comment with the HTML report link, coloured labels from the playbook, and a
   checklist appended to the MR description).

## Versioning

`@v1` is a floating major tag. Pin `@vX.Y.Z` for reproducibility. The template's
`@vN` ref and the `REGIS_IMAGE` tag are independent.
````

- [ ] **Step 2: Create `regis-gitlab-staging/.gitignore`**

```gitignore
reports/
*.tmp
```

- [ ] **Step 3: Commit**

```bash
git add regis-gitlab-staging/README.md regis-gitlab-staging/.gitignore
git commit -m "$(cat <<'EOF'
feat(gitlab): scaffold regis-gitlab staging (README + gitignore)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

### Task A2: Author the reusable template `templates/regis-mr.yml`

**Files:**

- Create: `regis-gitlab-staging/templates/regis-mr.yml`

This is the core deliverable. It adapts the cookiecutter pipeline
(`regis/cookiecutters/gitlab-ci/{{cookiecutter.project_slug}}/.gitlab-ci.yml`) and replaces the
`regis gitlab update-mr` Python call with a POSIX-sh `curl`+`jq` block that faithfully reproduces
the three behaviours of `regis/gitlab_cli.py::update_mr`: (1) post an MR comment with the report
link, (2) create + apply plain labels and coloured badge labels
(`.playbook.labels` / `.playbook.badge_labels[]` with `class`→colour
`success=388e3c warning=fbc02d error=d32f2f information=1976d2`, default `607d8b`), (3) prepend the
report link to the MR description and append `.playbook.mr_description_checklists`.

- [ ] **Step 1: Write the template**

Create `regis-gitlab-staging/templates/regis-mr.yml`:

```yaml
# Regis — Request-to-MR reusable template
# Consume via:
#   include:
#     - remote: "https://raw.githubusercontent.com/trivoallan/regis-gitlab/v1/templates/regis-mr.yml"
# Required: GITLAB_TOKEN (api scope). See README for all variables.

variables:
  REGIS_IMAGE: "ghcr.io/trivoallan/regis:latest"
  REGIS_PLAYBOOK: "playbook.yaml"

stages:
  - request
  - analyze
  - report

regis_request:
  stage: request
  image: alpine:latest
  rules:
    - if: $CI_PIPELINE_SOURCE == "web" && $IMAGE_URL
  before_script:
    - apk add --no-cache git
  script:
    - |
      BRANCH="regis/analyze/$(date +%Y%m%d-%H%M%S)"
      git config user.name "regis-ci"
      git config user.email "regis-ci@noreply"
      git checkout -b "$BRANCH"
      echo "$IMAGE_URL" > .regis-image-url
      git add .regis-image-url
      git commit -m "chore(regis): request analysis of $IMAGE_URL"
      git push \
        -o merge_request.create \
        -o merge_request.title="Regis Analysis: $IMAGE_URL" \
        -o merge_request.description="Automated security analysis requested via pipeline." \
        -o merge_request.remove_source_branch \
        "https://oauth2:${GITLAB_TOKEN}@${CI_SERVER_HOST}/${CI_PROJECT_PATH}.git" \
        "$BRANCH"

regis_analyze:
  stage: analyze
  image: $REGIS_IMAGE
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  script:
    - |
      if [ -f .regis-image-url ]; then
        IMAGE_URL=$(cat .regis-image-url)
      fi
      regis analyze "$IMAGE_URL" \
        --playbook "$REGIS_PLAYBOOK" \
        --html \
        --output-dir reports \
        --meta "trigger.user=$GITLAB_USER_LOGIN" \
        --meta "trigger.url=$CI_JOB_URL" \
        --meta "gitlab.mr_url=$CI_MERGE_REQUEST_PROJECT_URL/-/merge_requests/$CI_MERGE_REQUEST_IID"
  artifacts:
    paths:
      - reports/
    expire_in: 30 days

regis_report:
  stage: report
  image: alpine:latest
  needs:
    - regis_analyze
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  before_script:
    - apk add --no-cache git curl jq
  script:
    - |
      set -eu

      # Push the report artifact back onto the MR source branch
      git config user.name "regis-ci"
      git config user.email "regis-ci@noreply"
      git add reports/ || true
      git commit -m "chore(report): analysis complete" || true
      git push "https://oauth2:${GITLAB_TOKEN}@${CI_SERVER_HOST}/${CI_PROJECT_PATH}.git" \
        HEAD:"$CI_MERGE_REQUEST_SOURCE_BRANCH_NAME" || true

      MR_API="${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/merge_requests/${CI_MERGE_REQUEST_IID}"
      PROJ_API="${CI_API_V4_URL}/projects/${CI_PROJECT_ID}"
      REPORT_URL="${CI_PROJECT_URL}/-/jobs/${CI_JOB_ID}/artifacts/file/reports/report.html"
      REPORT_JSON="reports/report.json"
      TOKEN_HEADER="PRIVATE-TOKEN: ${GITLAB_TOKEN}"

      # 1. Comment with the report link
      COMMENT="🚀 **regis Analysis Complete!**

      The full HTML security report is ready: [View Analysis Report](${REPORT_URL})"
      curl -sf --header "$TOKEN_HEADER" --request POST \
        --data-urlencode "body=${COMMENT}" "${MR_API}/notes" >/dev/null \
        || echo "Warning: failed to post MR comment"

      # 2. Labels: plain + coloured badge labels -> comma-separated list
      LABELS=""
      add_label() {
        [ -z "${1:-}" ] && return 0
        if [ -z "$LABELS" ]; then LABELS="$1"; else LABELS="${LABELS},$1"; fi
      }
      for l in $(jq -r '.playbook.labels // [] | .[]' "$REPORT_JSON"); do
        add_label "$l"
      done
      # create badge labels with their colour if missing
      jq -r '.playbook.badge_labels // [] | .[] | [.name, .class] | @tsv' "$REPORT_JSON" \
      | while IFS="$(printf '\t')" read -r name cls; do
          [ -z "$name" ] && continue
          case "$cls" in
            success) color=388e3c ;;
            warning) color=fbc02d ;;
            error) color=d32f2f ;;
            information) color=1976d2 ;;
            *) color=607d8b ;;
          esac
          curl -s --header "$TOKEN_HEADER" --request POST \
            --data-urlencode "name=${name}" --data-urlencode "color=#${color}" \
            "${PROJ_API}/labels" >/dev/null || true
        done
      # collect badge label names (separate pass: the while-subshell can't mutate LABELS)
      for name in $(jq -r '.playbook.badge_labels // [] | .[].name' "$REPORT_JSON"); do
        add_label "$name"
      done

      # 3. MR description: prepend report link if absent, append checklists
      CUR_DESC=$(curl -sf --header "$TOKEN_HEADER" "$MR_API" | jq -r '.description // ""')
      NEW_DESC="$CUR_DESC"
      case "$CUR_DESC" in
        *"View Analysis Report"*) ;;
        *) NEW_DESC=$(printf '📝 **[View Analysis Report](%s)**\n\n%s' "$REPORT_URL" "$CUR_DESC") ;;
      esac
      CHECKLIST=$(jq -r '
        (.playbook.mr_description_checklists // [])
        | map(
            (if .title then "\n\n---\n\n## " + .title + "\n" else "" end)
            + ((.items // [])
               | map(if type == "object"
                      then "- [" + (if .checked then "x" else " " end) + "] " + .label
                      else "- [ ] " + . end)
               | join("\n"))
          )
        | join("\n")
      ' "$REPORT_JSON")
      if [ -n "$CHECKLIST" ]; then
        NEW_DESC="${NEW_DESC}${CHECKLIST}"
      fi

      # 4. Apply description + labels (add_labels appends; idempotent)
      if [ -n "$LABELS" ]; then
        curl -sf --header "$TOKEN_HEADER" --request PUT \
          --data-urlencode "description=${NEW_DESC}" \
          --data-urlencode "add_labels=${LABELS}" \
          "$MR_API" >/dev/null || echo "Warning: failed to update MR"
      else
        curl -sf --header "$TOKEN_HEADER" --request PUT \
          --data-urlencode "description=${NEW_DESC}" \
          "$MR_API" >/dev/null || echo "Warning: failed to update MR"
      fi
```

- [ ] **Step 2: Lint the template as YAML**

Run: `python -c "import yaml,sys; yaml.safe_load(open('regis-gitlab-staging/templates/regis-mr.yml')); print('valid yaml')"`
Expected: `valid yaml`

- [ ] **Step 3: Sanity-check the embedded shell with shellcheck (best-effort)**

Run (if `shellcheck` is available): extract the `regis_report` script body to a temp file and `shellcheck -s sh` it; fix any error-level (not style) findings. If `shellcheck` is unavailable, skip and note it.

- [ ] **Step 4: Commit**

```bash
git add regis-gitlab-staging/templates/regis-mr.yml
git commit -m "$(cat <<'EOF'
feat(gitlab): add CI-native regis-mr.yml reusable template

Reproduces `regis gitlab update-mr` (comment + coloured labels + MR
description checklists) with curl+jq, dropping the python-gitlab dependency.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

### Task A3: Example consumer + example playbook

**Files:**

- Create: `regis-gitlab-staging/examples/.gitlab-ci.yml`
- Create: `regis-gitlab-staging/examples/playbook.yaml`

- [ ] **Step 1: Example `.gitlab-ci.yml`**

Create `regis-gitlab-staging/examples/.gitlab-ci.yml`:

```yaml
# Minimal consumer of the regis-gitlab template.
include:
  - remote: "https://raw.githubusercontent.com/trivoallan/regis-gitlab/v1/templates/regis-mr.yml"

variables:
  REGIS_IMAGE: "ghcr.io/trivoallan/regis:latest"
  REGIS_PLAYBOOK: "playbook.yaml"
```

- [ ] **Step 2: Example playbook**

Copy the cookiecutter's example playbook verbatim as the example:

Run: `cp "regis/cookiecutters/gitlab-ci/{{cookiecutter.project_slug}}/playbook.yaml" regis-gitlab-staging/examples/playbook.yaml`

Then open `regis-gitlab-staging/examples/playbook.yaml` and replace any `{{ cookiecutter.* }}`
Jinja placeholders with concrete values (e.g. project name → `Example Policy`). Verify it is valid:
Run: `pipenv run regis playbook validate regis-gitlab-staging/examples/playbook.yaml`
Expected: `✓ ... is valid.`

- [ ] **Step 3: Commit**

```bash
git add regis-gitlab-staging/examples/
git commit -m "$(cat <<'EOF'
docs(gitlab): add example consumer pipeline and playbook

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

### Task A4: Repo CI for regis-gitlab (lint + release automation)

**Files:**

- Create: `regis-gitlab-staging/.github/workflows/ci.yml`
- Create: `regis-gitlab-staging/.github/workflows/tag-major.yml`
- Create: `regis-gitlab-staging/release-please-config.json`
- Create: `regis-gitlab-staging/.release-please-manifest.json`

- [ ] **Step 1: Lint workflow** — create `regis-gitlab-staging/.github/workflows/ci.yml`

```yaml
name: Lint template
on:
  push:
    branches: [main]
  pull_request:
permissions:
  contents: read
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate YAML
        run: |
          python -c "import yaml; yaml.safe_load(open('templates/regis-mr.yml')); print('template valid')"
          python -c "import yaml; yaml.safe_load(open('examples/.gitlab-ci.yml')); print('example valid')"
      - name: yamllint
        run: |
          pipx run yamllint -d "{extends: default, rules: {line-length: disable, document-start: disable}}" templates/ examples/
```

- [ ] **Step 2: Floating major tag workflow** — create `regis-gitlab-staging/.github/workflows/tag-major.yml`

```yaml
name: Update floating major tag
on:
  push:
    tags:
      - "v*.*.*"
permissions:
  contents: write
jobs:
  tag-major:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Move floating vN tag
        run: |
          set -eu
          TAG="${GITHUB_REF_NAME}"          # e.g. v1.2.3
          MAJOR="${TAG%%.*}"                 # e.g. v1
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git tag -f "$MAJOR" "$TAG"
          git push -f origin "$MAJOR"
```

- [ ] **Step 3: release-please config** — create `regis-gitlab-staging/release-please-config.json`

```json
{
  "packages": {
    ".": {
      "release-type": "simple",
      "bump-minor-pre-major": true
    }
  },
  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json"
}
```

- [ ] **Step 4: release-please manifest** — create `regis-gitlab-staging/.release-please-manifest.json`

```json
{
  ".": "0.0.0"
}
```

- [ ] **Step 5: Verify all staging YAML/JSON parse**

Run:

```bash
python -c "import yaml; [yaml.safe_load(open(f)) for f in ['regis-gitlab-staging/templates/regis-mr.yml','regis-gitlab-staging/examples/.gitlab-ci.yml','regis-gitlab-staging/.github/workflows/ci.yml','regis-gitlab-staging/.github/workflows/tag-major.yml']]; print('all yaml ok')"
python -c "import json; [json.load(open(f)) for f in ['regis-gitlab-staging/release-please-config.json','regis-gitlab-staging/.release-please-manifest.json']]; print('all json ok')"
```

Expected: `all yaml ok` then `all json ok`.

- [ ] **Step 6: Commit**

```bash
git add regis-gitlab-staging/.github regis-gitlab-staging/release-please-config.json regis-gitlab-staging/.release-please-manifest.json
git commit -m "$(cat <<'EOF'
ci(gitlab): add regis-gitlab repo CI (lint, release-please, tag-major)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## MANUAL GATE (maintainer)

Automated agents STOP here and hand off. The maintainer:

1. Creates the GitHub repo `trivoallan/regis-gitlab`.
2. Copies the contents of `regis-gitlab-staging/` to the new repo root and pushes to `main`.
3. Cuts `v1.0.0` and pushes it; confirms `tag-major.yml` creates the floating `v1`.
4. Sets branch protection (required check: `Lint template`).
5. Adds the `RELEASE_PLEASE_TOKEN` PAT secret (so release PRs trigger CI).
6. Confirms `https://raw.githubusercontent.com/trivoallan/regis-gitlab/v1/templates/regis-mr.yml` resolves.

Only once `regis-gitlab@v1` is live does Part B proceed (so the core docs point at a real ref).

---

## Part B — Remove the GitLab story from the core (breaking)

### Task B1: Remove `regis gitlab` command + test

**Files:**

- Delete: `regis/gitlab_cli.py`
- Modify: `regis/cli.py` (remove the gitlab import + registration)
- Delete: `tests/test_gitlab_cli.py`

- [ ] **Step 1: Baseline** — Run `pipenv run regis --help`; confirm `gitlab` is listed.

- [ ] **Step 2: Edit `regis/cli.py`** — delete the import line `from regis.gitlab_cli import gitlab_cmd` and the registration line `main.add_command(gitlab_cmd, name="gitlab")`. Leave all other commands untouched.

- [ ] **Step 3: Delete the module + test**

```bash
git rm regis/gitlab_cli.py tests/test_gitlab_cli.py
```

- [ ] **Step 4: Verify**

Run: `pipenv run regis --help` → expect no `gitlab` command.
Run: `grep -rn "gitlab_cli\|gitlab_cmd\|create-request\|update-mr\|update_mr\|create_request" regis/ tests/` → expect no matches.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
feat(cli)!: remove the regis gitlab commands (extracted to regis-gitlab)

BREAKING CHANGE: `regis gitlab create-request` / `regis gitlab update-mr`
are removed. Use the reusable template at trivoallan/regis-gitlab@v1.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

### Task B2: Remove `bootstrap gitlab-ci` + cookiecutter + test

**Files:**

- Modify: `regis/commands/bootstrap.py` (remove the `bootstrap_gitlab_ci` command)
- Delete: `regis/cookiecutters/gitlab-ci/`
- Delete: `tests/test_bootstrap_gitlab_ci.py`

- [ ] **Step 1: Edit `regis/commands/bootstrap.py`** — delete the entire `@bootstrap.command(name="gitlab-ci")` decorator and its `def bootstrap_gitlab_ci(output_dir: str, no_input: bool) -> None:` function body (the whole block). Leave `bootstrap_playbook` and `bootstrap_tools` intact. Remove any now-unused imports that were used **only** by `bootstrap_gitlab_ci` (verify with a grep before removing — `cookiecutter`, `resources`, `Path` may still be used by `bootstrap_playbook`; only remove an import if grep shows zero remaining uses in the file).

- [ ] **Step 2: Delete the cookiecutter tree + test**

```bash
git rm -r regis/cookiecutters/gitlab-ci
git rm tests/test_bootstrap_gitlab_ci.py
```

- [ ] **Step 3: Verify**

Run: `pipenv run regis bootstrap --help` → expect `playbook` and `tools` only, no `gitlab-ci`.
Run: `grep -rn "gitlab-ci\|gitlab_ci" regis/ tests/` → expect no matches.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
feat(cli)!: remove bootstrap gitlab-ci scaffolder (extracted to regis-gitlab)

BREAKING CHANGE: `regis bootstrap gitlab-ci` is removed. Consume the
reusable template at trivoallan/regis-gitlab@v1 instead.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

### Task B3: Drop the `python-gitlab` dependency

**Files:**

- Modify: `pyproject.toml` (remove `python-gitlab>=4.4.0`)
- Modify: `Pipfile.lock` (regenerated)

- [ ] **Step 1: Confirm nothing else imports it**

Run: `grep -rn "import gitlab\|from gitlab" regis/ tests/`
Expected: no matches (Tasks B1/B2 removed the only user).

- [ ] **Step 2: Remove the dependency line** in `pyproject.toml`:

```toml
  "python-gitlab>=4.4.0",
```

- [ ] **Step 3: Regenerate the lockfile and reinstall**

Run: `pipenv lock && pipenv install --dev`
Expected: resolves without `python-gitlab`.

Run: `pipenv run pip list 2>/dev/null | grep -i python-gitlab || echo "python-gitlab gone"`
Expected: `python-gitlab gone`.

- [ ] **Step 4: Run the full suite**

Run: `pipenv run pytest --no-cov -q`
Expected: PASS, no import errors.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml Pipfile.lock
git commit -m "$(cat <<'EOF'
build(deps): drop python-gitlab (GitLab integration extracted)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

### Task B4: Prune the core GitLab docs

**Files:**

- Modify: `docs/website/docs/usage/integrations/gitlab.md` (replace body with a pointer + migration note)
- Modify: `docs/website/docs/reference/cli.md` (remove `### gitlab` + `bootstrap gitlab-ci`)
- Modify: `docs/website/docs/roadmap.md` (move the GitLab CI items to "extracted")

- [ ] **Step 1: Rewrite `integrations/gitlab.md`** — replace the bulk of the page with a pointer, mirroring how `integrations/github.md` points at `regis-action`. Keep the page's frontmatter and title; replace the body with:

````markdown
## Reusable GitLab CI template

GitLab integration ships as a reusable CI template from its own repository,
[`trivoallan/regis-gitlab`](https://github.com/trivoallan/regis-gitlab), versioned
independently from the Regis core.

```yaml
include:
  - remote: "https://raw.githubusercontent.com/trivoallan/regis-gitlab/v1/templates/regis-mr.yml"

variables:
  REGIS_IMAGE: "ghcr.io/trivoallan/regis:latest"
  REGIS_PLAYBOOK: "playbook.yaml"
```

:::note Migrating from the built-in commands
The `regis gitlab` commands and the `regis bootstrap gitlab-ci` scaffolder were
removed from the core. The reusable template at
[`trivoallan/regis-gitlab`](https://github.com/trivoallan/regis-gitlab) replaces
them; it posts the MR comment, labels, and checklist itself.
:::
````

(Remove any remaining `regis gitlab` / `bootstrap gitlab-ci` references from the rest of the page.)

- [ ] **Step 2: Edit `reference/cli.md`** — remove the `### gitlab` section (the `gitlab create-request` / `gitlab update-mr` entries) and the `bootstrap gitlab-ci` entry from the bootstrap section. Leave `### bootstrap` (playbook/tools) and other commands intact.

- [ ] **Step 3: Edit `roadmap.md`** — update the `bootstrap gitlab-ci` "Recently shipped" row (and any "Guide GitLab CI" near-term item) to note the integration moved to `trivoallan/regis-gitlab`. Keep the table well-formed.

- [ ] **Step 4: Verify no residual references in current docs**

Run: `grep -rn "regis gitlab\|bootstrap gitlab-ci\|gitlab update-mr\|gitlab create-request" docs/website/docs/ | grep -v versioned_docs`
Expected: no matches. (`versioned_docs/**` stay intact.)

- [ ] **Step 5: Build the docs**

Run the Docusaurus build under `docs/website`; confirm no broken links.

- [ ] **Step 6: Commit**

```bash
git add docs/website/docs
git commit -m "$(cat <<'EOF'
docs(gitlab): point integration docs at trivoallan/regis-gitlab

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

### Task B5: Remove the staging dir + final verification & PR

**Files:**

- Delete: `regis-gitlab-staging/` (only after the maintainer has relocated it to the real repo)

- [ ] **Step 1: Confirm the manual gate is done** — verify `https://raw.githubusercontent.com/trivoallan/regis-gitlab/v1/templates/regis-mr.yml` resolves (the docs now point at it). If not yet live, STOP and wait.

- [ ] **Step 2: Remove the staging directory**

```bash
git rm -r regis-gitlab-staging
git commit -m "$(cat <<'EOF'
chore(gitlab): drop regis-gitlab staging dir (pushed to its own repo)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 3: Full lint + suite with coverage**

Run: `pipenv run ruff check . && pipenv run pytest`
Expected: lint clean; suite PASS; coverage ≥ 90 %.

- [ ] **Step 4: Trunk**

Run: `trunk check`
Expected: green (commit any auto-fixes).

- [ ] **Step 5: Open the PR**

Push the branch and open a PR titled `feat(cli)!: extract GitLab integration to regis-gitlab`. In `## Summary`, document the breaking change (`regis gitlab` + `bootstrap gitlab-ci` removed), the `python-gitlab` drop, and the migration (`include: remote: …/regis-gitlab/v1/…`). Confirm Release Please bumps the minor version (pre-v1).

---

## Notes for the implementer

- **Never touch the core root `.gitlab-ci.yml`** (confidential client example).
- Part B is breaking → pre-v1 minor bump (`bump-minor-pre-major`).
- The template's `regis_report` job intentionally runs on `alpine:latest` (curl/jq/git), not the
  regis image — the report stage no longer needs `regis` once posting is CI-native.
- `versioned_docs/**` snapshots are frozen — never edit them.
