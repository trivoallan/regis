# Decision Log

## 2026-02-20: Handle Skopeo Architecture Mismatch

- **Decision**: Avoid high-level `skopeo inspect` on image indexes when the local architecture doesn't match the remote index.
- **Rationale**: Prevent "no image found" errors (exit status 1) when analyzing multi-arch images on local dev machines (e.g., Apple Silicon).

## 2026-02-20: Automated Docs Publishing

- **Decision**: Implement GitHub Actions workflow to build and publish Antora site to GitLab Pages.
- **Rationale**: Automate documentation deployment to ensure it stays up-to-date with the code.

## 2026-02-20: Cookiecutter Template for Consumer Repos

- **Decision**: Create a Cookiecutter template to bootstrap new repositories for `regis-cli` users.
- **Rationale**: Facilitate adoption and standardize the setup for image analysis projects, including CI/CD and security policies.

## 2026-02-20: Fix Missing Playbook Values

- **Decision**: Update `evaluate` in `engine.py` to add type checking and safety guards for playbook links.
- **Decision**: Integrate GitHub Actions metadata into the template workflow using `regis-cli --meta`.
- **Rationale**: Prevent `AttributeError` crashes when link URLs are null or missing in playbook definitions. Improved metadata integration ensures better traceability in CI/CD.
- 2026-03-05: Migrated CI linting from Super-Linter to Trunk to unify local and CI linting experience and improve performance.

## 2026-03-05: Adopt OCI Image Labels

- **Decision**: Add standard OCI labels (`org.opencontainers.image.*`) to the project's `Dockerfile`.
- **Rationale**: Improve discoverability and integration with GitHub Packages registry, ensuring the image description and source repository are automatically linked on the package page.
