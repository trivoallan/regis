# Plan: Playbook Creation Skill

> Feature: `create-playbook` — Claude Code OMC skill for interactive playbook authoring
> Created: 2026-04-20
> Roadmap: Next (1–3 months), after playbook bundle format ships

---

## Context

Regis playbooks are currently authored by hand as YAML files. The upcoming v0.29 introduces a
**bundle format** (directory with `playbook.yaml` + `README.md` + `inputs.schema.json`). The
`create-playbook` skill guides users through this interactively inside Claude Code, outputting a
ready-to-use playbook bundle.

The skill ships inside the regis-cli repo at `.claude/skills/create-playbook/` and is available to
any user who has OMC installed and has the repo open.

---

## Phase 0: Documentation Discovery (DONE)

### Allowed APIs & Sources

| Artifact           | Path                                                                        | Key facts                                                                               |
| ------------------ | --------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Playbook schema    | `regis/schemas/playbook/definition.schema.json`                             | Only `name` is required; `rules`, `tiers`, `badges`, `integrations` are optional arrays |
| Default playbook   | `regis/playbooks/default.yaml`                                              | 175 lines; canonical rule set; copy-ready tiers/badges/GitLab integration               |
| GitLab CI template | `regis/cookiecutters/gitlab-ci/{{cookiecutter.project_slug}}/playbook.yaml` | 98 lines; best full example with rules + tiers + badges + checklists                    |
| Playbook loader    | `regis/playbook/loader.py`                                                  | Accepts YAML file path or HTTP URL                                                      |
| Skill format       | `SKILL.md` with `---` frontmatter                                           | Fields: `name`, `description`, `argument-hint` (optional)                               |

### Available providers (from default.yaml)

`trivy`, `skopeo`, `sbom`, `hadolint`, `freshness`, `size`, `popularity`, `endoflife`,
`scorecarddev`, `provenance`

### Anti-patterns to avoid

- Do NOT invent rule slugs — copy from `regis/playbooks/default.yaml:15-119`
- Do NOT use deprecated `pages`/`sections`/`sidebar` fields
- Skills do NOT use `AskUserQuestion` tool — interaction is natural conversation
- `inputs.schema.json` does not exist yet; Phase 3 defines its format (JSON Schema draft-07)

---

## Phase 1: Discover Available Rule Templates

**Goal:** Build an accurate catalog of every provider's rule templates before writing the skill.

**Tasks:**

1. Grep each analyzer's `default_rules()` method for rule slugs and their options:
   ```bash
   grep -rn "def default_rules" regis/analyzers/
   grep -rn "\"slug\"" regis/analyzers/
   ```
2. Read `regis/analyzers/trivy.py` — extract all rule template slugs and required `options` keys
3. Repeat for: `hadolint.py`, `sbom.py`, `freshness.py`, `endoflife.py`, `scorecarddev.py`
4. Compile into `references/available-rules.md` (one section per provider)

**Output:** `references/available-rules.md` with verified rule slugs, options, and descriptions

**Verification:**

- Every slug in the catalog must appear in the source file (grep check)
- Cross-reference with `regis/playbooks/default.yaml` rules section

---

## Phase 2: Skill Scaffold

**Goal:** Create the directory structure and minimal `SKILL.md`.

**Tasks:**

1. Create `.claude/skills/create-playbook/` in the repo root
2. Create `SKILL.md` with frontmatter:
   ```yaml
   ---
   name: create-playbook
   description: >
     Create a Regis playbook bundle interactively. Guides the user through naming,
     rule selection (trivy, hadolint, sbom, freshness, endoflife, scorecarddev),
     tier configuration, CI integration (GitLab/GitHub), and inputs schema.
     Use whenever the user says "create a playbook", "new playbook", "setup regis",
     or asks how to configure policy-as-code for their container images.
   argument-hint: "<image-type or use-case>"
   ---
   ```
3. Create subdirectory `references/`
4. Copy `regis/cookiecutters/gitlab-ci/.../playbook.yaml` content into
   `references/playbook-examples.md` as a annotated reference

**Copy-ready pattern:** Frontmatter format from any skill in
`~/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/`

**Verification:**

- `SKILL.md` exists and opens without parse errors
- Frontmatter has valid YAML (no tabs, proper quoting)

---

## Phase 3: Wizard Workflow (Core)

**Goal:** Write the full interactive workflow in `SKILL.md`.

**Workflow stages:**

### Stage 1 — Context gathering

Prompt for:

- Playbook name + description
- Target CI system: GitLab CI / GitHub Actions / standalone
- Image type hint (optional — helps pre-select relevant rules)

### Stage 2 — Rule selection

Present providers grouped by concern:

- **Vulnerabilities:** `trivy` (cve-count, fix-available, age)
- **Code quality:** `hadolint` (violations)
- **Supply chain:** `sbom`, `scorecarddev`, `provenance`
- **Lifecycle:** `freshness`, `endoflife`, `popularity`

For each selected provider, prompt for key options (e.g., trivy max CVE counts per level).

Reference: `regis/playbooks/default.yaml:15-119` for option defaults.

### Stage 3 — Tier configuration

Ask for scoring thresholds (Gold/Silver/Bronze or custom names).
Default: Gold >90, Silver >70, Bronze >50 (from `default.yaml:7-14`).

### Stage 4 — CI integration

- **GitLab:** configure badges, checklist items (with `show_if`/`check_if` JSON Logic),
  MR template URL
- **GitHub Actions:** note that SARIF export is on the roadmap; offer badge config
- **None:** skip

Reference pattern: `regis/cookiecutters/gitlab-ci/.../playbook.yaml:50-98`

### Stage 5 — Inputs schema (optional)

If the user needs non-image validation (project IDs, security doc URLs):

- Ask for each input field: name, type, description, required/optional
- Generate `inputs.schema.json` (JSON Schema draft-07)

Format (new, not yet in codebase — define it here):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "project_id": {
      "type": "string",
      "description": "Internal project identifier"
    }
  },
  "required": ["project_id"]
}
```

### Stage 6 — Output generation

Write three files into the user-specified directory:

1. `playbook.yaml` — assembled from stages 2–4
2. `README.md` — auto-generated with playbook purpose, rule summary, how to run
3. `inputs.schema.json` — from stage 5 (only if inputs were configured)

**Verification checklist:**

- [ ] Each stage asks exactly one focused question before proceeding
- [ ] Stage 2 rule options have correct defaults from `default.yaml`
- [ ] Generated `playbook.yaml` validates against `regis/schemas/playbook/definition.schema.json`
      (`pipenv run python -c "import jsonschema, yaml, json; ..."`)
- [ ] No deprecated fields (`pages`, `sections`, `sidebar`) in output

---

## Phase 4: Reference Files

**Goal:** Create `references/available-rules.md` and `references/playbook-examples.md`.

**`references/available-rules.md` structure:**

```markdown
## trivy

| Rule slug     | Required options | Description                         |
| ------------- | ---------------- | ----------------------------------- |
| cve-count     | level, max_count | Fail if CVE count exceeds threshold |
| fix-available | level            | Fail if fixable CVEs exist          |

...
```

Sourced from Phase 1 grep output.

**`references/playbook-examples.md` structure:**

- Minimal playbook (name only)
- Security-focused playbook (trivy + hadolint + sbom)
- Full playbook (all sections, GitLab integration)

Source: annotated excerpts from `regis/playbooks/default.yaml` and
`regis/cookiecutters/gitlab-ci/.../playbook.yaml`

---

## Phase 5: Validation

**Goal:** Verify the skill produces valid, runnable playbooks.

**Tests:**

1. Run the skill in a fresh context with scenario: "GitLab CI, trivy + hadolint, Gold/Silver tiers"
2. Validate generated `playbook.yaml`:
   ```bash
   cd /path/to/test-output
   pipenv run python -c "
   import jsonschema, yaml, json
   schema = json.load(open('regis/schemas/playbook/definition.schema.json'))
   playbook = yaml.safe_load(open('playbook.yaml'))
   jsonschema.validate(playbook, schema)
   print('Valid')
   "
   ```
3. Run `pipenv run regis analyze --playbook ./playbook.yaml <test-image>` (smoke test)
4. Grep output for deprecated fields: `grep -E 'pages:|sections:|sidebar:' playbook.yaml`

**Acceptance criteria:**

- `jsonschema.validate` passes
- No deprecated fields in output
- README.md is non-empty and references rule names correctly

---

## Files to Create

```text
regis-cli/
└── .claude/
    └── skills/
        └── create-playbook/
            ├── SKILL.md                       ← main skill file
            └── references/
                ├── available-rules.md         ← rule catalog (Phase 1 output)
                └── playbook-examples.md       ← annotated copy-ready examples
```

## Files to Read (do not modify)

- `regis/schemas/playbook/definition.schema.json` — validation only
- `regis/playbooks/default.yaml` — reference for rule defaults
- `regis/cookiecutters/gitlab-ci/.../playbook.yaml` — copy patterns
- `regis/analyzers/*.py` — extract rule slugs and options
