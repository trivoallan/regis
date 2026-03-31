# GitHub Actions

Integrating `regis` into your GitHub Actions workflows allows you to automate security and compliance checks for every container image you build. This ensures that only images meeting your predefined standards are promoted through your pipeline.

## Prerequisites

To follow this guide, you should have a GitHub repository with a `Dockerfile` and a basic understanding of GitHub Actions.

:::tip
To quickly bootstrap a new GitHub repository pre-configured with `regis` and GitHub Actions, you can use our [Project Bootstrapping](../../reference/cli.md#bootstrap) command.

**Note**: For repositories with branch protection, please ensure the **"Allow auto-merge"** option is enabled in the repository's general settings to support automated documentation updates.
:::

## Quick Start with the Reusable Action

The fastest way to integrate `regis` is to use the official reusable GitHub
Action. It wraps the full analysis workflow—running the scanner, uploading the
report artifact, and posting a PR comment—into a single step.

### Permissions

```yaml
permissions:
  contents: read
  packages: write # Required only if pushing to GHCR
  pull-requests: write # Required only for PR comments
```

### Minimal example

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

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

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
        uses: trivoallan/regis@v0.25.0
        with:
          image-url: ghcr.io/${{ github.repository }}:latest
          auth: ghcr.io=${{ github.actor }}:${{ secrets.GITHUB_TOKEN }}
```

### Action inputs

| Input             | Required | Default                 | Description                                                                     |
| ----------------- | -------- | ----------------------- | ------------------------------------------------------------------------------- |
| `image-url`       | Yes      | —                       | Container image URL to analyze.                                                 |
| `auth`            | No       | —                       | Registry credentials as `registry=user:pass`.                                   |
| `playbook`        | No       | —                       | URL or path to a custom playbook YAML file.                                     |
| `report-url`      | No       | —                       | URL to a hosted report (used as a link in the PR comment).                      |
| `github-token`    | No       | `${{ github.token }}`   | Token used to post PR comments (`pull-requests: write` required).               |
| `pr-url`          | No       | —                       | PR URL to post results on. Defaults to the current PR on `pull_request` events. |
| `upload-artifact` | No       | `true`                  | Upload the report directory as a workflow artifact.                             |
| `artifact-name`   | No       | `regis-security-report` | Name for the uploaded artifact.                                                 |
| `version`         | No       | `latest`                | `regis` Docker image version to use.                                            |

### Action outputs

| Output        | Description                                          |
| ------------- | ---------------------------------------------------- |
| `report-path` | Absolute path to the report directory on the runner. |

:::note
PR comments require `regis` **v0.25.0 or later**. When running on a
`pull_request` event, the action posts automatically. For other events, pass
`pr-url` explicitly.
:::

## Workflow Setup

A robust integration typically involves building your image, pushing it to a registry (like GitHub Container Registry), and then running `regis` to analyze the results.

### Required Permissions

Ensure your workflow has the necessary permissions to read content and write to the package registry:

```yaml
permissions:
  contents: read
  packages: write
```

### Complete Example

The following example demonstrates a complete workflow that builds an image, pushes it to GHCR, and performs a security analysis.

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

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:latest

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install regis
        run: |
          pip install pipenv
          pipenv install --deploy

      - name: Run Analysis
        run: |
          pipenv run regis analyze ghcr.io/${{ github.repository }}:latest \
            --auth ghcr.io=${{ github.actor }}:${{ secrets.GITHUB_TOKEN }} \
            --site \
            --meta "trigger.user=${{ github.actor }}" \
            --meta "trigger.url=${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"

      - name: Upload Report
        uses: actions/upload-artifact@v4
        with:
          name: regis-security-report
          path: reports/
```

## Publishing to GitHub Pages

You can host your security reports directly on GitHub Pages by adding a deployment job to your workflow.

### Configure Repository

1. Go to **Settings > Pages**.
2. Under **Build and deployment > Source**, select **GitHub Actions**.

### Deployment Job

Add the following job to your workflow to deploy the generated site:

```yaml
deploy:
  environment:
    name: github-pages
    url: ${{ steps.deployment.outputs.page_url }}
  runs-on: ubuntu-latest
  needs: build-and-analyze
  permissions:
    pages: write
    id-token: write
  steps:
    - name: Deploy to GitHub Pages
      id: deployment
      uses: actions/deploy-pages@v4
      with:
        artifact_name: github-pages # Matches the artifact uploaded by build-and-analyze
```

:::important
To use this job, update your `Run Analysis` step to use `--site` and ensure you use `actions/upload-pages-artifact` instead of `upload-artifact` in the `build-and-analyze` job.
:::

```yaml
- name: Upload Pages Artifact
  uses: actions/upload-pages-artifact@v3
  with:
    path: reports/
```

## Advanced Configuration

You can further customize the integration to meet specific security requirements.

### Authenticating with Private Registries

To analyze images in private registries, use the `--auth` flag. For GitHub Container Registry, you can use the automatically provided `GITHUB_TOKEN`.

```bash
regis analyze <image-url> --auth ghcr.io=<username>:<token>
```

### Using Security Playbooks

By default, `regis` uses its built-in evaluation logic. For standardized security enforcement, you can point to the project's recommended security playbook.

```bash
regis analyze <image-url> --playbook https://raw.githubusercontent.com/trivoallan/regis/main/regis/playbooks/default.yaml
```

:::tip
You can also define local playbooks in your repository to enforce custom organization-wide policies. Check the [Playbooks](../../concepts/playbooks.md) guide for more details.
:::

### Adding CI Metadata

Use the `--meta` flag to attach arbitrary metadata to your reports. `regis` recognizes certain "well-known" keys that are used by the default playbook to enhance the report:

- `trigger.user`: The user who initiated the analysis (e.g., `${{ github.actor }}`).
- `trigger.url`: A link to the CI job or environment (e.g., the URL to the GitHub Actions run).

```bash
regis analyze <image-url> \
  --meta "trigger.user=${{ github.actor }}" \
  --meta "trigger.url=${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
```

## Posting Results to Pull Requests

After running the analysis, you can post the results directly to a Pull Request
as a comment using the `github update-pr` command:

```yaml
- name: Post analysis results to PR
  if: github.event_name == 'pull_request'
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: |
    regis github update-pr \
      --report reports/report.json \
      --report-url "${{ steps.pages.outputs.page_url }}" \
      --pr-url "${{ github.event.pull_request.html_url }}"
```

The command will:

- Post a summary comment with the playbook score, tier, and vulnerability counts.
- Include a link to the full HTML report.
- Apply any labels defined in the playbook.
- **Update** the existing comment on re-runs instead of creating duplicates.

### CLI reference

```bash
regis github update-pr \
  --report <path-to-report.json> \
  --report-url <url-to-html-report> \
  --pr-url <github-pr-url> \
  --token <github-token>  # or set GITHUB_TOKEN env var
```

| Option         | Description                                                   |
| -------------- | ------------------------------------------------------------- |
| `--report`     | Path to the `report.json` file produced by `regis analyze`    |
| `--report-url` | URL where the HTML report is hosted (artifact, Pages, etc.)   |
| `--pr-url`     | Full GitHub PR URL (`https://github.com/owner/repo/pull/42`)  |
| `--token`      | GitHub token — also reads `GITHUB_TOKEN` environment variable |

## Viewing Reports

When using the `--site` flag, `regis` generates a full HTML site in the `reports/` directory. By uploading this directory as a workflow artifact (as shown in the example), you can download and view the interactive reports directly from the GitHub Actions run page.
