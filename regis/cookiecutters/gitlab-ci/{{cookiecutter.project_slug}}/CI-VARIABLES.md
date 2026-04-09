# CI/CD Variables — {{ cookiecutter.project_name }}

Configure these variables in **Settings > CI/CD > Variables** in your GitLab project.

## Required

| Variable       | Description                                                                                                                                                                  |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GITLAB_TOKEN` | Project Access Token with `api` and `write_repository` scopes. Role: Developer (minimum). **Do not protect** this variable, or protect the `regis/analyze/*` branch pattern. |

## Pipeline Input

| Variable    | Description                                                                                                                                          |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IMAGE_URL` | Container image to analyze (e.g., `docker.io/library/alpine:3.18`). Set when running the pipeline manually via **Build > Pipelines > Run pipeline**. |

## Optional

| Variable                  | Description                                                                    |
| ------------------------- | ------------------------------------------------------------------------------ |
| `REGIS_REGISTRY_USER`     | Username for private registry authentication.                                  |
| `REGIS_REGISTRY_PASSWORD` | Password or token for private registry authentication.                         |
| `DOCKER_AUTH_CONFIG`      | Docker config JSON for registry authentication (alternative to user/password). |
