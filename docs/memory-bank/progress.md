# Progress

## Completed

- Core CLI functionality.
- Key analyzers (Skopeo, Trivy, Hadolint, etc.).
- Playbook evaluation with JSON logic.
- Jinja2-based HTML report generation.
- GitHub Actions workflows for release and Docker publishing.
- Docusaurus documentation structure initialized and migrated from Antora, including versioning setup.
- Relocated JSON schemas to `regis_cli/schemas/` for better packaging.
- Fixed Skopeo architecture mismatch handling for multi-arch image indexes.
- Automated Antora documentation publishing to GitHub Pages (Legacy).
- Automated `trunk fmt` in CI with auto-commit of style changes.
- Fixed Trunk Check `HEAD^2` error by optimizing git checkout and auto-commit configuration.
- Refactored `generate` command into a `bootstrap` command group (`bootstrap repository` and `bootstrap playbook`).
- Display post-install notes after bootstrap.
- Fixed Trunk Check `HEAD^2` error by optimizing git checkout and auto-commit configuration.
- Added post-install notes feature to `bootstrap` commands and updated documentation.

- Unified linting experience by migrating to Trunk.
- Migrated documentation to Docusaurus, established dynamic versioning strategy with tag names, and cleaned up redundant folders.

## Future Roadmap

- Additional analyzers (e.g., custom compliance checks).
- More HTML themes.
- Enhanced reporting features.
