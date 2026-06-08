---
trigger: always_on
---

# Commit messages

- Must follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. Allowed types : https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#type
- Scopes are **mandatory** and must be extrapolated from the architectural component modified.
- Styleguide : https://developers.google.com/blockly/guides/contribute/get-started/commits
- La description du commit doit être pensée pour être facilement compréhensible dans le changelog et renvoyer vers la documentation quand c'est possible. Privilégier l'aspect fonctionnel. Réserver les aspects techniques au body du message.

## Defined Scopes

To ensure clean and readable changelogs, please use the following allowed scopes depending on the architectural component modified:

### Core & Logic

- `cli` : Command-line interface, argument parsing, main console output.
- `playbook` : Rule evaluation engine, section parsing, `jsonLogic`, context management.
- `schema` : Data interfaces, structure definitions, JSON validation files (`*.schema.json`).
- `registry` : Registry communication layer (HTTP, authentication, manifest fetching).

### Analyzers

- `analyzer` : Base analyzer class or shared analyzer interfaces.
- `analyzer/cve` : Vulnerability (CVE) scanning via grype.
- `analyzer/secrets` : Embedded secret detection via trufflehog.
- `analyzer/sbom` : SBOM analysis and CycloneDX/SPDX generation via syft.
- `analyzer/hadolint` : Dockerfile linting.
- `analyzer/dockle` : Container image linting / best practices.
- `analyzer/skopeo` : Base metadata extraction.
- `analyzer/freshness` : Image age and freshness score.
- `analyzer/size` : Size and layer calculations.
- `analyzer/popularity` : Registry popularity metrics.
- `analyzer/endoflife` : Version support status.
- `analyzer/scorecarddev` : OpenSSF Scorecard checks.
- `analyzer/provenance` : Provenance and supply-chain evidence.

### Rendering & Reporting

- `report` : High-level report generation (folder creation, file writing).
- `templates` (or `theme`) : Visual aspects, HTML, CSS, React/Docusaurus SPA.

### Tooling & CI

- `ci` : GitHub Actions workflows.
- `deps` (or `build`) : Environment management (Pipenv, pyproject.toml, Dockerfiles).
- `docs` : Docusaurus documentation, READMEs, and Memory Bank updates.
