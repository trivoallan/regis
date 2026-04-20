---
name: create-playbook
description: >
  Create a Regis playbook bundle interactively. Guides the user through naming,
  rule selection (trivy, hadolint, sbom, freshness, scorecarddev, skopeo, dockle),
  tier configuration, CI integration (GitLab/GitHub), and optional inputs schema.
  Use whenever the user says "create a playbook", "new playbook", "setup regis",
  or asks how to configure policy-as-code for their container images.
argument-hint: "<image-type or use-case>"
---

# Skill: create-playbook

Guide the user through building a Regis playbook bundle in six focused stages. Ask
one question at a time — do not dump all questions at once. Wait for the answer
before moving to the next stage. Do not use the AskUserQuestion tool; conduct the
conversation naturally.

Refer to `references/available-rules.md` in this skill directory for the full rule
catalog (slugs, options, and defaults).

---

## Stage 1 — Context gathering

Ask the following, one at a time:

1. **Playbook name** — what should this playbook be called? (e.g., "My Security Policy")
2. **Description** (optional) — a short human-readable description for the README.
3. **Target CI system** — which system will run Regis?
   - `gitlab` — GitLab CI (merge request integration available)
   - `github` — GitHub Actions (SARIF export on roadmap)
   - `none` — standalone / no CI integration
4. **Output directory** — where should the bundle be written?
   (e.g., `./regis-policy`, `./ci/regis`)

Store all answers before moving to Stage 2.

---

## Stage 2 — Rule selection

Present the available providers grouped by concern. For each group, describe what it
checks, then ask which rules the user wants to enable.

After the user picks a rule, ask for its key options (using the defaults from
`references/available-rules.md` as suggestions).

### Group A — Vulnerabilities & secrets (`trivy`)

| Rule            | What it checks               | Key options                                                 |
| --------------- | ---------------------------- | ----------------------------------------------------------- |
| `cve-count`     | Max CVEs at a given severity | `level` (critical/high/medium/low), `max_count` (default 0) |
| `fix-available` | Max fixable CVEs             | `max_count` (default 0)                                     |
| `secret-scan`   | Embedded secrets/tokens      | `max_count` (default 0)                                     |

### Group B — Dockerfile quality

**`hadolint`**

| Rule             | What it checks             | Key options                                           |
| ---------------- | -------------------------- | ----------------------------------------------------- |
| `severity-count` | Dockerfile lint violations | `level` (error/warning/info), `max_count` (default 0) |

**`dockle`** (CIS Docker Benchmark)

| Rule             | What it checks         | Key options                                        |
| ---------------- | ---------------------- | -------------------------------------------------- |
| `severity-count` | CIS benchmark failures | `level` (fatal/warn/info), `max_count` (default 0) |

### Group C — Supply chain

**`sbom`**

| Rule                | What it checks             | Key options                                |
| ------------------- | -------------------------- | ------------------------------------------ |
| `has-sbom`          | Image must provide an SBOM | (none)                                     |
| `license-blocklist` | Block forbidden licenses   | `blocklist` (list of SPDX IDs, default []) |

**`scorecarddev`** (OpenSSF Scorecard)

| Rule        | What it checks                  | Key options                      |
| ----------- | ------------------------------- | -------------------------------- |
| `min-score` | Minimum OpenSSF Scorecard score | `min_score` (float, default 5.0) |

### Group D — Freshness (`freshness`)

| Rule  | What it checks                  | Key options                  |
| ----- | ------------------------------- | ---------------------------- |
| `age` | Image must be newer than N days | `max_days` (int, default 30) |

### Group F — Registry policy (`core`)

| Rule                        | What it checks                           | Key options                                                                   |
| --------------------------- | ---------------------------------------- | ----------------------------------------------------------------------------- |
| `registry-domain-whitelist` | Image must come from an allowed registry | `domains` (list, defaults: docker.io, registry-1.docker.io, quay.io, ghcr.io) |

Only add if the user wants to enforce source registry policy.

### Group E — Image configuration (`skopeo`)

| Rule                      | Key options                              |
| ------------------------- | ---------------------------------------- |
| `user-blacklist`          | `blacklist` (list, e.g. `["root", "0"]`) |
| `max-size`                | `max_mb` (float)                         |
| `layers-count`            | `max_count` (int)                        |
| `tag-blacklist`           | `blacklist` (list of tag patterns)       |
| `platforms-count`         | `min_count` (int, for multi-arch)        |
| `exposed-ports-whitelist` | `whitelist` (list of port numbers)       |
| `required-labels`         | `labels` (list of OCI label names)       |
| `env-blacklist`           | `blacklist` (list of env var names)      |

### Recommended starting point

For a typical production policy, suggest these defaults (and ask if the user wants
to adjust):

```yaml
trivy / cve-count (critical, max 0)   — level: critical
trivy / cve-count (high, max 10)      — level: warning
trivy / fix-available (max 0)         — level: warning
hadolint / severity-count (error, 0)  — level: warning
sbom / has-sbom                       — level: warning
freshness / age (max_days: 90)        — level: info
```

For each enabled rule, assign it a unique `slug` (e.g., `cve-critical`, `cve-high`,
`cve-fixable`) and a playbook-level `level` (critical / warning / info) that controls
how rule failures affect the score. These are distinct: the rule option `level` filters
which CVE severity to count; the playbook `level` sets the weight of a failure.

---

## Stage 3 — Tier configuration

Explain that tiers assign a label (Gold / Silver / Bronze) based on the overall score.
Present the defaults:

| Tier   | Threshold  |
| ------ | ---------- |
| Gold   | score > 90 |
| Silver | score > 70 |
| Bronze | score > 50 |

Ask: "Would you like to keep these defaults or customize the tier names and thresholds?"

If customizing, collect name + threshold for each tier (up to three tiers).

---

## Stage 4 — CI integration

### GitLab CI

If the user chose `gitlab` in Stage 1:

1. **Badges** — which rule results should appear as GitLab project badges?
   Suggest: `cve-critical`, `cve-high`, `freshness`. Ask if they want to adjust.

2. **Checklist** — add a security checklist to merge requests?
   Suggest a checklist with:
   - Security review completed
   - No critical vulnerabilities detected (linked to the `cve-critical` rule)
   - Image does not run as root (linked to the `no-root` rule, if enabled)

   Ask if they want these items or different ones.

### GitHub Actions

If the user chose `github` in Stage 1:

Explain: "GitHub SARIF export is on the Regis roadmap but not yet available.
The playbook will still run and produce a score — CI integration will just use
the CLI exit code for now."

Offer to continue without CI-specific config.

### None

Skip this stage.

---

## Stage 5 — Inputs schema (optional)

Ask: "Do you need to validate non-image inputs passed to Regis (e.g., project IDs,
security doc URLs, approval ticket numbers)?"

- **No** — skip to Stage 6.
- **Yes** — for each input field, gather:
  - Field name (e.g., `security_doc_url`)
  - Type: `string`, `integer`, `boolean`, `array`
  - Description
  - Required or optional
  - Any format constraint (e.g., `uri`, `date`, enum values)

This produces an `inputs.schema.json` file (JSON Schema draft-07).

---

## Stage 6 — Output generation

Assemble the playbook bundle and write to the output directory specified in Stage 1.

### File 1: `playbook.yaml`

Construct valid YAML from stages 2–4. Use this structure:

```yaml
# Regis Playbook — <name>
# Docs: https://trivoallan.github.io/regis/docs/concepts/playbooks

name: "<name>"
description: "<description>" # omit if not provided

tiers:
  - name: Gold
    condition:
      ">": [{ var: rules_summary.score }, 90]
  - name: Silver
    condition:
      ">": [{ var: rules_summary.score }, 70]
  - name: Bronze
    condition:
      ">": [{ var: rules_summary.score }, 50]

rules:
  - provider: <provider>
    rule: <rule-slug>
    slug: <unique-slug>
    level: <critical|warning|info>
    options: # omit if no options
      <key>: <value>

badges: # omit if no CI or no badges requested
  - slug: <rule-slug>
    scope: <Scope>
    value: <Label>
    condition:
      "!": [{ var: rules.<slug>.passed }]
    class: <error|warning|success|information>

integrations: # only if GitLab chosen
  gitlab:
    badges:
      - <slug>
    checklists:
      - title: "Security Review"
        items:
          - label: Security review completed
          - label: <item>
            show_if: { "!!": [{ var: rules.<slug> }] }
            check_if: { var: rules.<slug>.passed }

  # links:
  #   - label: Return to Merge Request
  #     url: "{{ env.CI_MERGE_REQUEST_PROJECT_URL }}/-/merge_requests/{{ env.CI_MERGE_REQUEST_IID }}"
  # integrations.gitlab.templates:
  #   - url: https://example.com/evidence-template
```

### File 2: `README.md`

Generate automatically with:

- Playbook name and description
- Table of enabled rules: slug, provider, rule template, level, key options
- How to run:
  ```bash
  regis analyze --playbook ./<output-dir>
  ```

### File 3: `inputs.schema.json` (only if Stage 5 produced fields)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["<required-fields>"],
  "properties": {
    "<field>": {
      "type": "<type>",
      "description": "<description>"
    }
  }
}
```

### After writing

Show the user the file tree:

```text
<output-dir>/
├── playbook.yaml
├── README.md
└── inputs.schema.json   ← only if generated
```

Offer to validate the playbook:

```bash
regis analyze --playbook ./<output-dir> --dry-run
```

Or if running from the project root with Pipenv:

```bash
pipenv run regis analyze --playbook ./<output-dir> --dry-run
```
