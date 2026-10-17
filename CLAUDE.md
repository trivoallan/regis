# CLAUDE.md

## Memory Bank (required)

This project uses a Memory Bank in `docs/memory-bank/`. At every session start:

1. Read `docs/memory-bank/RULES.md` — protocol rules (immutable).
2. Read `docs/memory-bank/activeContext.md` and `docs/memory-bank/progress.md`.
3. Read others as needed (`systemPatterns.md`, `techContext.md`, `productContext.md`, `projectbrief.md`).

Les **specs** vivent dans `docs/superpowers/specs/`, les **plans** d'exécution dans `docs/superpowers/plans/` — jamais à la racine. Les plans sont **supprimés au merge** (squash) ; seuls specs et notes de recherche promues survivent. Taxonomie : `docs/memory-bank/systemPatterns.md`.
Never modify `RULES.md` or write secrets into any memory bank file.

## Commands

```bash
uv sync                              # Install all dependencies (incl. dev group)
make lint                            # ruff, mypy, import-linter, docs/reference up to date
make test                            # Full run with coverage (fails if total < 90% OR any file < 90%)
make security                        # pip-audit, blocking from HIGH
make image                           # Build and smoke-test both image variants (slim, full)
make reference                       # Regenerate docs/reference (rules and schemas); commit the result
uv run python -m pytest --no-cov     # Fast loop — disables both the global and per-file coverage gates
uv run ruff format .                 # Format
uv run regis --help                  # Run CLI locally
```

CI's build steps only call these `make` targets. Documentation is plain Markdown in `docs/` (entry point `docs/README.md`), read on GitHub.

Required external binaries (must be on `PATH`): `grype`, `syft`, `trufflehog`, `regctl`, `hadolint`, `dockle`, `cosign`.

Coverage is enforced at two levels by `tests/_per_file_coverage.py` (loaded via `tests/conftest.py`): a global
`--cov-fail-under=90` gate and a per-file gate that fails if any single source file under `regis/` is below 90%.
The threshold for both is `[tool.coverage.report].fail_under` in `pyproject.toml`. `tests/` is excluded from
measurement; zero-statement files are skipped. `--no-cov` disables both gates.

Use `--no-cov` for fast iteration; run the full suite before opening a PR.

## Architecture

Hexagonal (ports & adapters). The dependency rule — `adapters > core.application > core.domain > core.ports > core.model` — is enforced in CI by **import-linter** (`make lint`). The core is Click-free; driven adapters own all I/O. Full layer table + diagram: `docs/memory-bank/systemPatterns.md` § Architecture.

```
regis/
  core/                 # Click-free hexagonal core
    model/              #   value objects: ImageReference, Report, REPORT_SCHEMA_VERSION
    ports/              #   ImageInspector, ToolRunner, ReportSink, PresentationRenderer, AnalyzerProvider
    domain/
      analyzers/        #     BaseAnalyzer + discovery.py (entry-point loader) + 14 analyzers
      playbook/         #     playbook engine (loader, evaluator, conditions, context, verdict)
      rules/            #     JSON Logic criterion evaluation and merging
      manifest.py · context.py (AnalysisContext) · errors.py
    application/        #   use-cases: AnalyzeImage, Evaluate, playbook_runner
  adapters/
    driven/
      registry/         #     RegistryClient, auth, URL parser; Registry/Regctl ImageInspectors
      tools/            #     SubprocessToolRunner + tool-fetch infra (manifest/fetcher/cosign + manifest.yaml)
      report/           #     FileReportSink, CookiecutterPresentationRenderer, html report
      analyzers/        #     EntryPointAnalyzerProvider
    driving/
      cli/              #     cli.py (`regis` console script), commands/, composition.py (wiring root)
  utils/                # unlayered: process (run_cmd/require_tool), report shim, predicates, scanner wrappers
  schemas/              # JSON Schema files for analyzer outputs and playbooks
  playbooks/            # Built-in default playbook (default/playbook.yaml)
  templates/ · cookiecutters/ · data/   # report template, scaffolds, static data
```

## Agent patterns (Regis-specific)

- **Analyzer plugins**: subclass `BaseAnalyzer` (in `regis/core/domain/analyzers/`), implement `analyze(self, ctx: AnalysisContext)` (external access via `ctx.tools` / `ctx.inspector`), `validate()`, `default_criteria()`. Register via `[project.entry-points."regis.analyzers"]` in `pyproject.toml` pointing at `regis.core.domain.analyzers.<mod>:<Cls>` — re-run `uv sync` after changing entry points (the group key `"regis.analyzers"` is the discovery contract, not a module path).
- **Rule templates**: `default_criteria()` can return both concrete criteria and slug-identified templates; playbooks instantiate them via `criterion: <slug>` + `options:`.
- **JSON Logic operators**: custom ops (`intersects`, `contains_all`, `subset`, `keys`, `get`, `env_contains`) registered in `core/domain/rules/evaluator.py`.
- **Parallel analysis**: `ThreadPoolExecutor`, default 4 workers (`--max-workers` overrides). Each thread gets its own `RegistryClient`.
- **Test patch targets**: patch at the _new_ module location after the CLI split — `regis.adapters.driving.cli.commands.analyze.{RegistryClient,_discover_analyzers}`, `regis.adapters.driving.cli.commands.check.{RegistryClient,version}`, `regis.utils.process.{shutil,subprocess}`, `regis.utils.report.jsonschema`. **Not** `regis.adapters.driving.cli.cli.*`.
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
- **Always rebase** feature branches on the latest `main` (never merge `main` back into them) — keeps history linear.
- Branch from the latest `main` immediately before committing.

## Commit messages

> Conventions transverses (scopes, branches, skills, style) : source unique dans `.agent/rules/` (auto-chargé) ; contrat + glossaire dans `docs/memory-bank/constellation/`. Ce `CLAUDE.md` ne garde que le détail propre au cœur.

Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) with the [Angular type list](https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#type).

- **Scopes are mandatory.** Full scope list in `docs/memory-bank/systemPatterns.md`.
- Description style: [Google Blockly commit guide](https://developers.google.com/blockly/guides/contribute/get-started/commits). Favor the functional aspect; reserve technical details for the body.

## Style guides

- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Google HTML/CSS Style Guide](https://google.github.io/styleguide/htmlcssguide.html)
- [Google developer documentation style guide](https://developers.google.com/style)
- Diagrams in **Mermaid**; architecture diagrams in **C4**.

## CI/CD

GitHub Actions with the CI socle shared by `regis`, `knock` and `uske` (`ci`, `pr-title`, `release`, `renovate`, `settings`, `socle-drift`), plus `regis`-only workflows named `extra-*.yml`. [Release Please](https://github.com/googleapis/release-please), [Semantic Versioning](https://semver.org/). Repository settings are versioned in `.github/settings.json` and applied by `.github/apply-settings.sh` (`make settings`). Renovate is self-hosted (`renovate.yml`). Workflows that write use the `oci-ci-ttc` GitHub App (`CI_APP_CLIENT_ID`, `CI_APP_PRIVATE_KEY`).

Workflow details (the `make` contract, App tokens, settings, Release Please labels, mypy/tests) → `docs/memory-bank/systemPatterns.md` § CI/CD.
