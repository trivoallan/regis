# Regis Security Analysis — GitHub Action

[![CI](https://github.com/trivoallan/regis-action/actions/workflows/ci.yml/badge.svg)](https://github.com/trivoallan/regis-action/actions/workflows/ci.yml)

The **[regis-security-analysis](https://github.com/marketplace/actions/regis-security-analysis)**
GitHub Action runs a full [Regis](https://github.com/trivoallan/regis) security
analysis on any OCI image, uploads the report as a workflow artifact, and
optionally posts a summary comment on pull requests.

The action wraps the `regis` CLI (shipped as the
`ghcr.io/trivoallan/regis` Docker image) into a single composite step.

> **Migrating from `trivoallan/regis@vX`?** The action used to live in the core
> repository and was referenced as `uses: trivoallan/regis@vX`. It now lives
> here. Replace `trivoallan/regis@vX` with `trivoallan/regis-action@v1`. The
> `version:` input (the `regis` Docker image tag) is unchanged.

## Quick start

```yaml
- uses: trivoallan/regis-action@v1
  with:
    image-url: ghcr.io/your-org/your-image:latest
```

## Inputs

| Input             | Required | Default                 | Description                                                          |
| ----------------- | -------- | ----------------------- | -------------------------------------------------------------------- |
| `image-url`       | Yes      | —                       | Container image URL to analyze                                       |
| `auth`            | No       | `""`                    | Registry credentials as `registry=user:pass`                         |
| `playbook`        | No       | `""`                    | URL or path to a custom playbook YAML                                |
| `report-url`      | No       | `""`                    | URL to the hosted report (used in the PR comment link)               |
| `github-token`    | No       | `${{ github.token }}`   | Token for posting PR comments; requires `pull-requests: write`       |
| `pr-url`          | No       | `""`                    | PR URL to comment on; auto-detected in `pull_request` context        |
| `upload-artifact` | No       | `true`                  | Whether to upload the report as a workflow artifact                  |
| `artifact-name`   | No       | `regis-security-report` | Name for the uploaded artifact                                       |
| `version`         | No       | `latest`                | `regis` Docker image tag to run (pin to a release tag in production) |

## Outputs

| Output        | Description                                         |
| ------------- | --------------------------------------------------- |
| `report-path` | Absolute path to the report directory on the runner |

## PR comment usage

To post a comment with the analysis summary on a pull request, add
`pull-requests: write` to your job permissions and supply `pr-url`:

```yaml
jobs:
  security-scan:
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: trivoallan/regis-action@v1
        with:
          image-url: ghcr.io/your-org/your-image:latest
          pr-url: ${{ github.event.pull_request.html_url }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

The PR comment fires only when `pr-url` is set (auto-detected on
`pull_request` events). The `github-token` always defaults to `GITHUB_TOKEN`;
supplying it explicitly is optional.

## Complete example

```yaml
name: Build and Analyze

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-and-analyze:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      pull-requests: write
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:latest

      - name: Analyze with regis
        uses: trivoallan/regis-action@v1
        with:
          image-url: ghcr.io/${{ github.repository }}:latest
          auth: ghcr.io=${{ github.actor }}:${{ secrets.GITHUB_TOKEN }}
          pr-url: ${{ github.event.pull_request.html_url }}
```

## Version pinning

The `uses:` ref (action code) and the `version:` input (Docker image tag) are
**independent** — pin both for a fully reproducible run:

```yaml
- uses: trivoallan/regis-action@v1.0.0
  with:
    image-url: ghcr.io/your-org/your-image:latest
    version: "v0.34.0" # regis Docker image tag
```

`@v1` tracks the latest stable v1.x of the action; `@v1.0.0` pins an exact
release.

## License

[MIT](LICENSE)
