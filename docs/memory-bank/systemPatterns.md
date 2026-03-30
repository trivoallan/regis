# System Patterns

## Architecture

`regis-cli` follows a modular, pluggable architecture.

### Key Components

- **CLI (Click)**: Entry point for user interaction.
- **Engine**: Orchestrates analysis and playbook evaluation.
- **Analyzers**: Pluggable modules that extract specific data (e.g., Skopeo, Trivy, Hadolint).
- **Playbook Engine**: Evaluates JSON logic rules against analyzer results.
- **Report Generators**: Produces interactive SPA dashboards and machine-readable JSON.

## Rules and Standards

- **Python**: Use `pipenv` for dependency management.
- **CI/CD**: GitHub Actions with Release Please and Trunk.
  - **Authentication**: All workflows use GitHub App token (`actions/create-github-app-token@v1`) with `REGIS_CI_APP_ID` + `REGIS_CI_APP_PRIVATE_KEY` secrets. This ensures bot-created PRs and auto-commits trigger downstream workflows (unlike GITHUB_TOKEN which prevents run triggers).
  - **Key Actions**: `peaceiris/actions-gh-pages` uses `personal_token:` (not `github_token:`) when passed a non-GITHUB_TOKEN.
- **Documentation**: Docusaurus for documentation as code.
- **Aesthetics**: High priority on visual excellence for HTML reports.
