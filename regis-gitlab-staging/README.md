# regis-gitlab

Reusable GitLab CI template that runs [Regis](https://github.com/trivoallan/regis)
container-image security analysis on a merge request and posts the results back
to the MR — comment, labels, and a checklist in the description.

Versioned independently from the Regis core; consume it with `include: remote`.

## Usage

Add to your project's `.gitlab-ci.yml`:

```yaml
include:
  - remote: "https://raw.githubusercontent.com/trivoallan/regis-gitlab/v1/templates/regis-mr.yml"

variables:
  REGIS_IMAGE: "ghcr.io/trivoallan/regis:latest" # pin a tag in production
  REGIS_PLAYBOOK: "playbook.yaml"
```

Commit a `playbook.yaml` to your repo (scaffold one with `regis bootstrap playbook`).

## Required CI/CD variables

| Variable         | Required | Description                                                                 |
| ---------------- | -------- | --------------------------------------------------------------------------- |
| `GITLAB_TOKEN`   | Yes      | Project/group access token with `api` scope (posts comments, labels, push). |
| `IMAGE_URL`      | Web run  | Image to analyze when triggering the pipeline manually (web UI).            |
| `REGIS_IMAGE`    | No       | Regis image (default `ghcr.io/trivoallan/regis:latest`).                    |
| `REGIS_PLAYBOOK` | No       | Playbook path (default `playbook.yaml`).                                    |

Mark `GITLAB_TOKEN` as **Masked** in **Settings → CI/CD → Variables** so it is not
exposed in job logs (it is embedded in the authenticated `git push` URL).

## How it works

1. **request** (web trigger): creates a `regis/analyze/<ts>` branch + MR carrying the image URL.
2. **analyze** (MR event): runs `regis analyze --html` into `reports/`.
3. **report** (MR event): commits the report to the branch and posts to the MR
   (comment with the HTML report link, coloured labels from the playbook, and a
   checklist appended to the MR description).

## Versioning

`@v1` is a floating major tag. Pin `@vX.Y.Z` for reproducibility. The template's
`@vN` ref and the `REGIS_IMAGE` tag are independent.
