---
sidebar_position: 3
---

# Archive Repository

The `bootstrap archive --repo` command scaffolds a standalone archive viewer site and publishes it to a new remote repository in a single step — no manual git or platform configuration required.

:::info
This command automates what you would otherwise do manually after running [`bootstrap archive`](../../reference/cli.md#bootstrap-archive): creating the remote repository, pushing the initial commit, and enabling Pages.
:::

## Prerequisites

Before running the command, make sure the following tools are installed and authenticated:

| Tool   | Purpose                                   | Install                                                        |
| :----- | :---------------------------------------- | :------------------------------------------------------------- |
| `pnpm` | Install Node.js dependencies              | [pnpm.io](https://pnpm.io/installation)                        |
| `git`  | Initialize the local repository           | System package or [git-scm.com](https://git-scm.com)           |
| `gh`   | Create GitHub repository and enable Pages | [cli.github.com](https://cli.github.com)                       |
| `glab` | Create GitLab repository                  | [gitlab.com/gitlab-org/cli](https://gitlab.com/gitlab-org/cli) |

Only `gh` **or** `glab` is required depending on your target platform.

Authenticate before running:

```bash
# GitHub
gh auth login

# GitLab
glab auth login
```

## Usage

```bash
regis bootstrap archive [OUTPUT_DIR] --repo [OPTIONS]
```

| Option                        | Default                                    | Description                                                          |
| :---------------------------- | :----------------------------------------- | :------------------------------------------------------------------- |
| `--repo`                      | —                                          | **Required.** Create a remote repository and enable Pages.           |
| `--platform [github\|gitlab]` | _(interactive prompt)_                     | Target platform. Skips the cookiecutter platform prompt.             |
| `--no-input`                  | `False`                                    | Accept all cookiecutter defaults without prompting.                  |
| `--repo-name TEXT`            | Project slug                               | Name of the remote repository to create.                             |
| `--public / --private`        | `--public` (GitHub) / `--private` (GitLab) | Repository visibility.                                               |
| `--org TEXT`                  | Current authenticated user                 | Organisation (GitHub) or group (GitLab) to create the repository in. |

## What the command does

The command runs the following steps in sequence:

1. **Pre-flight** — verifies that `pnpm`, `git`, and the platform CLI are available and authenticated.
2. **Scaffold** — runs the archive cookiecutter template to generate a local Docusaurus site.
3. **`pnpm install`** — installs Node.js dependencies.
4. **Initial commit** — runs `git init -b main`, stages all files, and commits with the message `chore(report): initial archive site scaffold`.
5. **Create remote repository** — runs `gh repo create` or `glab repo create`.
6. **Enable Pages** — activates GitHub Pages in workflow mode via the GitHub API. On GitLab, Pages is activated automatically by the `pages` CI job on first push.
7. **Summary** — prints the expected Pages URL and the command to add your first report.

## GitHub example

```bash
regis bootstrap archive ./my-archives \
  --repo \
  --platform github \
  --repo-name regis-archive \
  --org my-org \
  --no-input
```

After the command completes, the GitHub Actions workflow (`.github/workflows/deploy.yml`) runs on every push to `main` that touches `static/archive/**`. It builds the Docusaurus site and deploys it to GitHub Pages.

The Pages URL follows the pattern:

```
https://<owner>.github.io/<repo-name>/
```

### Custom domain or org page

If you are using a custom domain or a GitHub organisation page (where the site is served at the root `/`), set the `ARCHIVE_BASE_URL` repository variable in **Settings > Secrets and variables > Actions > Variables**:

```
ARCHIVE_BASE_URL = /
```

The workflow reads this variable and passes it to the Docusaurus build.

## GitLab example

```bash
regis bootstrap archive ./my-archives \
  --repo \
  --platform gitlab \
  --repo-name regis-archive \
  --org my-group \
  --no-input
```

The GitLab CI pipeline (`.gitlab-ci.yml`) derives `ARCHIVE_BASE_URL` automatically from `CI_PAGES_URL`, which handles subgroups and custom domains correctly.

The Pages URL follows the pattern:

```
https://<namespace>.gitlab.io/<repo-name>/
```

### Custom domain or subgroup

If you use a custom Pages domain or a deeply nested subgroup, the base URL is derived from `CI_PAGES_URL` at build time — no manual configuration needed. To override, add `ARCHIVE_BASE_URL` as a CI/CD variable in **Settings > CI/CD > Variables**.

## Adding reports

Once the archive site is live, append reports to it from any project:

```bash
regis analyze <image> \
  --archive /path/to/regis-archive/static/archive
```

Then commit and push in the archive repository:

```bash
cd /path/to/regis-archive
git add static/archive/
git commit -m "chore: add report for <image>"
git push
```

The CI pipeline triggers automatically and rebuilds the site.

## Troubleshooting

### Repository already exists

If the remote repository was created by a previous interrupted run, the creation step is skipped automatically and the push continues to the existing repository. You will see:

```
  ⚠ Repository 'regis-archive' already exists, skipping creation.
```

### Authentication error

If `gh auth status` or `glab auth status` fails, the command stops immediately. Re-run `gh auth login` or `glab auth login` and retry.

### `pnpm` not found

Install `pnpm` globally and ensure it is in your `PATH`:

```bash
npm install -g pnpm
```

### Docusaurus baseUrl error after deployment

If the deployed site shows a **"wrong baseUrl"** error, the built-in auto-detection may not match your Pages setup. Set the `ARCHIVE_BASE_URL` CI/CD variable explicitly to the correct path (for example `/` for a root custom domain, or `/subgroup/repo-name/` for a GitLab subgroup).
