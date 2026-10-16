# System Patterns

## Architecture — hexagonal (ports & adapters)

`regis` follows a strict **ports & adapters** layout. The dependency rule is
enforced in CI by **import-linter** (`[tool.importlinter]` in `pyproject.toml`,
contract _"Hexagonal layering"_, run by `make lint`): a layer may import only
the layers below it. The migration that landed this (P0→P5, 2026-06) is recorded
in `decisionLog.md`.

```mermaid
flowchart TB
    CLI["Driving adapter — adapters/driving/cli<br/>cli.py · commands/ · composition.py"]
    APP["core.application<br/>AnalyzeImage · Evaluate · playbook_runner"]
    DOM["core.domain<br/>analyzers/ · playbook/ · rules/ · manifest · context · errors"]
    PORTS["core.ports<br/>ImageInspector · ToolRunner · ReportSink · PresentationRenderer · AnalyzerProvider"]
    MODEL["core.model<br/>ImageReference · Report"]
    DRIVEN["Driven adapters — adapters/driven<br/>registry/ · tools/ · report/ · analyzers/"]

    CLI -->|may import| APP
    APP -->|may import| DOM
    DOM -->|may import| PORTS
    PORTS -->|may import| MODEL
    DRIVEN -->|implement| PORTS
    CLI -->|composition root wires| DRIVEN
```

### Layers (top → bottom; each imports only those below)

| Layer               | Package                       | Holds                                                                                                                                                                                                             |
| ------------------- | ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Driving adapter** | `regis/adapters/driving/cli/` | `cli.py`, `commands/`, the composition root (`composition.py`) that wires use-cases to driven adapters                                                                                                            |
| **Application**     | `regis/core/application/`     | use-cases `AnalyzeImage` / `Evaluate` (own the loop, playbooks, emission), `playbook_runner`                                                                                                                      |
| **Domain**          | `regis/core/domain/`          | `analyzers/` (base + discovery + 14 analyzers), `playbook/` engine, `rules/` (JSON Logic), `manifest`, `context` (`AnalysisContext`), `errors`                                                                    |
| **Ports**           | `regis/core/ports/`           | `ImageInspector`, `ToolRunner`, `ReportSink`, `PresentationRenderer` (driven-side interfaces) + `AnalyzerProvider` (analyzer discovery)                                                                           |
| **Model**           | `regis/core/model/`           | value objects `ImageReference`, `Report`, `REPORT_SCHEMA_VERSION`                                                                                                                                                 |
| **Driven adapters** | `regis/adapters/driven/`      | `registry/` (HTTP + regctl inspectors, auth, URL parser), `tools/` (subprocess runner + tool-fetch infra), `report/` (`FileReportSink`, cookiecutter renderer, html), `analyzers/` (`EntryPointAnalyzerProvider`) |

The core is **Click-free** — Click lives only in the driving CLI adapter; driven
adapters own all I/O (subprocesses, registry HTTP, file writes, credentials).
Unlayered support packages (`utils/`, `schemas/`, `templates/`, `playbooks/`,
`cookiecutters/`, `data/`) sit outside the contract.

## Report Output Format Extension Pattern

New report output formats in `regis/utils/report.py` follow the `elif fmt == '<ext>':` pattern in `render_and_save_reports()`, delegating to a dedicated `_render_<fmt>()` helper.

Adding a format requires:

1. New `_render_<fmt>()` helper function in `report.py`
2. `elif fmt == '<ext>':` branch in `render_and_save_reports()`
3. CLI flag in `analyze.py` wired into both the main analysis path and the `--rerun` path

**Gotcha**: The `-m` shorthand is already taken by `--meta` in `regis analyze`. When adding new short flags to `analyze.py`, check existing shorthands first. `--markdown` has no short flag for this reason.

## Vocabulary: the four-layer policy model

Policy concepts are layered so "rule" is no longer overloaded (rename landed 2026-06-05, PR #646):

```text
finding → metric → criterion → rule
```

- **finding** — a raw detection from an analyzer (a CVE on a package, a leaked secret). Evidence; security analyzers only. SBOM **components** are inventory, _not_ findings.
- **metric** — an aggregate measurement an analyzer exposes (`critical_count`, `has_sbom`, `score`). What criteria evaluate; namespace `results.<analyzer>.<metric>` in conditions.
- **criterion** — a reusable, parameterized condition shipped by an analyzer via `default_criteria()` (e.g. `cve-count`). Policy-neutral: a JSON Logic `condition` + open `params`. Referenced in a playbook entry via the `criterion:` key; namespace `criterion.params.*`.
- **rule** — the policy decision: a criterion bound to concrete options + a severity level + a tier, in a playbook. "rule" now means only this layer (and `spec.rules`, the list of rules).

Backward compatibility: the legacy `rule:` entry key and `rule.*` condition namespace still resolve (the engine dual-binds both to the same object) but emit a `DeprecationWarning`; `BaseAnalyzer.default_rules()` is a deprecated shim. `regis playbook migrate` rewrites playbooks (idempotent, evaluation-preserving). The legacy path is removed at the next major.

## Rules and Standards

- **Python**: Use `uv` for dependency management.
- **CI/CD**: GitHub Actions, the common socle and its `make` contract, Release Please (see "CI/CD — the common socle" below).
- **Documentation**: plain Markdown in `docs/`, read on GitHub (documentation as code).
- **Aesthetics**: High priority on visual excellence for HTML reports.

### Couverture de tests — double gate (global + par fichier)

La suite `uv run pytest` applique deux niveaux de garde :

1. **Global** : `--cov-fail-under=90` (paramètre pytest standard, lu depuis `pyproject.toml`).
2. **Par fichier** : `tests/_per_file_coverage.py` — plugin pytest maison enregistré via un
   hookwrapper `pytest_sessionfinish` dans `tests/conftest.py`. Il parcourt le rapport de
   couverture et fait échouer la session si un fichier sous `regis/` est en-dessous du seuil.

Les deux gates lisent le même seuil : `[tool.coverage.report].fail_under` dans `pyproject.toml`.
`tests/` est exclu de la mesure (pas de récursion). Les fichiers sans aucune instruction sont
ignorés. `--no-cov` désactive les deux gates.

## Dev Environment Gotchas

- **Stale editable-install entry points**: the analyzer registry (`discover_analyzers()`) is resolved from `importlib.metadata` entry points, which are **frozen into `entry_points.txt` at `pip install -e` time** and do **not** update when `pyproject.toml`'s `[project.entry-points."regis.analyzers"]` changes. After any pull/branch switch that adds, removes, or renames an analyzer entry point, **re-run `uv sync`** (or `uv run pip install -e . --no-deps`) to regenerate the metadata. Symptom: `ModuleNotFoundError` warnings for removed/renamed analyzers (`skopeo`, `trivy`) **and**, more insidiously, **silent absence** of newly added analyzers (`oci`, `cve`) — `analyze` runs without them and emits no error. Verify with `uv run python -c "from importlib.metadata import entry_points; [print(ep.name) for ep in entry_points(group='regis.analyzers')]"` and compare against `pyproject.toml`.

## CI/CD — the common socle

`regis`, `knock` and `uske` share one CI ("socle"), copied verbatim between the three repos.
`socle-drift.yml` compares it weekly with the other two repos' `main`.

- **Socle workflows** (identical in the three repos): `ci.yml`, `pr-title.yml`, `release.yml`,
  `renovate.yml`, `settings.yml`, `socle-drift.yml`, plus `.github/renovate.json5`,
  `.github/apply-settings.sh` and `.github/pip-audit-gate.py`. A workflow that belongs to one
  repo only must be named `extra-*.yml` (here: `extra-image-size`, `extra-tools-fetch-smoke`,
  `extra-tools-manifest`, `extra-cleanup-ghcr`), or `socle-drift` reports it.
- **The `make` contract**: CI only calls `make ci-tools lint test security image`. What is
  specific to `regis` lives in the `Makefile`: `lint` runs ruff, mypy, import-linter, then
  `make reference` and fails if `docs/reference` is stale (commit the regenerated output);
  `security` runs `pip-audit` with a HIGH gate via `.github/pip-audit-gate.py`; `image` builds
  and smoke-tests both variants listed in `.github/images.json`.
- **`ci.yml`** also checks that actions are pinned by full SHA, that no nanopm data is
  tracked, and internal Markdown links (lychee, offline).
- **`release.yml`**: release-please on `main`; when a release is cut, builds each variant from
  `.github/images.json`, pushes to GHCR with buildx provenance (`mode=max`) and SBOM, signs
  keyless with cosign, and smoke-tests the published image.
- **GitHub App**: workflows that write use the `oci-ci-ttc` app through
  `actions/create-github-app-token` (`client-id: ${{ secrets.CI_APP_CLIENT_ID }}` and
  `CI_APP_PRIVATE_KEY`), each with a token scoped to what it needs. Never use `GITHUB_TOKEN`
  for a push that must trigger downstream CI — it won't.
- **Repository settings** are versioned in `.github/settings.json` and applied by
  `.github/apply-settings.sh` (`make settings`, and `settings.yml`, which reverts manual
  changes; it runs on push to `main` when either file changes, and weekly). Only `description` and `topics` differ between repos.
- **Renovate** is self-hosted (`renovate.yml`, daily cron) with `.github/renovate.json5`.
- **PR titles** follow Conventional Commits, checked by `pr-title.yml` (required check
  `pr-title`). Release Please PRs carry the `autorelease: pending` label; don't edit them by
  hand unless necessary.
- **Documentation** is plain Markdown under `docs/`, read on GitHub: no site, no Pages, no
  Docusaurus. `docs/reference/` is generated by `make reference`.
- **mypy** is excluded for `tests/**` (crashes on Linux CI with stale cache on `http.server`).

## Mémoire & artefacts de planification — taxonomie

Tout artefact de mémoire se range selon deux axes : **portée** (local à un repo /
constellation transverse) et **durée de vie** (durable / éphémère).

|                   | Durable                                                           | Éphémère                                 |
| ----------------- | ----------------------------------------------------------------- | ---------------------------------------- |
| **Local**         | memory-bank du repo + specs (`docs/superpowers/specs/`)           | plans d'exécution → supprimés au merge   |
| **Constellation** | conventions (`.agent/rules/`) + `docs/memory-bank/constellation/` | état programme → mémoire auto de l'agent |

Règle mentale : _« Est-ce vrai pour toute la constellation ? → cœur. Est-ce que ça
survit à la PR ? → memory-bank/spec, sinon plan jetable. »_

- Une **note de recherche** (probe, benchmark, « pourquoi on a écarté X ») est durable :
  la promouvoir vers `decisionLog.md` avant de supprimer le plan qui l'hébergeait.
- Les sous-projets ne dupliquent pas la zone constellation : ils y renvoient par lien.

## Commit Scopes (mandatory)

> Source de vérité unique : `.agent/rules/commitmessages.md` (auto-chargé par les
> agents). Extrapoler le scope du composant architectural modifié. Ne pas redupliquer
> la liste ici.
