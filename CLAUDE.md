# CLAUDE.md

## Memory Bank (required)

This project uses a Memory Bank in `docs/memory-bank/`. At every session start:

1. Read `docs/memory-bank/RULES.md` — protocol rules (immutable).
2. Read `docs/memory-bank/activeContext.md` and `docs/memory-bank/progress.md`.
3. Read others as needed (`systemPatterns.md`, `techContext.md`, `productContext.md`, `projectbrief.md`).

Plans live in `docs/memory-bank/plans/<task-slug>-plan.md` — never at repo root.
Never modify `RULES.md` or write secrets into any memory bank file.

## Commands

```bash
pipenv install --dev          # Install all dependencies
pipenv run pytest             # Full run with coverage (fails if < 90%)
pipenv run pytest --no-cov    # Fast loop — no coverage check
pipenv run ruff check .       # Lint
pipenv run ruff format .      # Format
pipenv run regis --help       # Run CLI locally
trunk check                   # Run all linters
trunk check --fix             # Auto-fix
pnpm --filter @regis/dashboard start   # Launch report viewer (UI work)
pnpm --filter @regis/dashboard build   # Build viewer SPA
```

Required external binaries (must be on `PATH`): `grype`, `syft`, `trufflehog`, `regctl`, `hadolint`, `dockle`.

Use `--no-cov` for fast iteration; run the full suite before opening a PR.

## Architecture

```
regis/
  cli.py              # `regis` console script entry point
  analyzers/          # Pluggable analyzers (entry points in pyproject.toml)
  analyzers/discovery.py  # discover_analyzers() — entry point loader
  commands/           # CLI commands (analyze, archive, bootstrap, check, rules)
  utils/process.py    # run_cmd(), require_tool() — subprocess helpers
  utils/report.py     # write_report, run_playbooks, validate_report, render_*
  playbook/           # Playbook evaluation engine (context, sections, evaluator)
  rules/              # JSON Logic rule evaluation and merging
  registry/           # Registry client, auth, URL parser
  report/             # Report generation (Docusaurus SPA builder)
  schemas/            # JSON Schema files for analyzer outputs and playbooks
  playbooks/          # Built-in default playbook (default.yaml)
apps/dashboard/       # Docusaurus + Tremor report viewer (pnpm workspace)
```

## Agent patterns (Regis-specific)

- **Analyzer plugins**: subclass `BaseAnalyzer`, implement `analyze()`, `validate()`, `default_rules()`. Register via `project.entry-points."regis.analyzers"` in `pyproject.toml`.
- **Rule templates**: `default_rules()` can return both concrete rules and slug-identified templates; playbooks instantiate them via `rule: <slug>` + `options:`.
- **JSON Logic operators**: custom ops (`intersects`, `contains_all`, `subset`, `keys`, `get`, `env_contains`) registered in `rules/evaluator.py`.
- **Parallel analysis**: `ThreadPoolExecutor`, default 4 workers (`--max-workers` overrides). Each thread gets its own `RegistryClient`.
- **Test patch targets**: patch at the _new_ module location after the CLI split — `regis.commands.analyze.{RegistryClient,_discover_analyzers}`, `regis.commands.check.{RegistryClient,version}`, `regis.utils.process.{shutil,subprocess}`, `regis.utils.report.jsonschema`. **Not** `regis.cli.*`.
- **Lazy imports**: `from module import X` inside a function body — patch at the source (`module.X`), not the importing module.

## Craftsmanship

- **Spec-based programming with stacked skills.** This project favors composable, spec-driven workflows on two levels:
  - **Methodology**: use Claude Code skills as stacked building blocks — [Superpowers](https://claude.com/plugins/superpowers) for engineering discipline (`/brainstorming`, `/execute-plan`, TDD, systematic debugging) composed with project skills (`/verify`, `/code-review`, `/init`). Each skill encodes a reviewed spec; chaining them produces predictable, auditable workflows. When a recurring task has no skill, author one (`/skill-authoring`) rather than re-improvising.
  - **Architecture**: prefer declarative specs (JSON Schemas, playbook YAML, JSON Logic rules) over imperative code paths. Extend existing schemas before adding ad-hoc Python logic.
- Prefer established, state-of-the-art libraries over starting from scratch.
- Prefer Python over ECMAScript languages when possible.
- Type hints required for all new functions and classes.

## Git workflow

- Feature/bug branches → PR → `main`. `main` is protected.
- For **notable user-facing features**, add the `whats-new` GitHub label on the PR. The `## Summary` section is harvested into the What's New page by `scripts/generate_whats_new.py` during CI.
- **Always rebase** feature branches on the latest `main` (never merge `main` back into them) — keeps history linear.
- Branch from the latest `main` immediately before committing (avoids the auto-rebase + squash no-op trap).

## Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) with the [Angular type list](https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#type).

- **Scopes are mandatory.** Full scope list in `docs/memory-bank/systemPatterns.md`.
- Description style: [Google Blockly commit guide](https://developers.google.com/blockly/guides/contribute/get-started/commits). Favor the functional aspect; reserve technical details for the body.

## Style guides

- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Google HTML/CSS Style Guide](https://google.github.io/styleguide/htmlcssguide.html)
- [Google developer documentation style guide](https://developers.google.com/style)
- Diagrams in **Mermaid**; architecture diagrams in **C4**.

## CI/CD

GitHub Actions + [Release Please](https://github.com/googleapis/release-please) + [Trunk](https://trunk.io). [Semantic Versioning](https://semver.org/). GitHub project config via the [Settings App](https://github.com/apps/settings).

Workflow gotchas (App token wiring, Dependabot secret access, Release Please labels, gh-pages, Trunk auto-fmt, mypy/tests, rebase + squash) → `docs/memory-bank/systemPatterns.md`.

Locally, Trunk's pre-commit hook auto-fixes on `git commit` — commit the produced changes.
