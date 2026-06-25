---
sidebar_position: 8
tags:
  - troubleshooting
---

# Troubleshooting

## Missing External Tools

When you run `regis`, it requires certain external binaries depending on which analyzers you use.

**Error symptoms:**

- `Command 'regctl' not found`
- `Command 'grype' not found`
- `Command 'syft' not found`
- `Command 'trufflehog' not found`
- `Command 'hadolint' not found`
- `Command 'dockle' not found`

**Solution:**

1. Run `regis check` to diagnose which tools are missing:

   ```bash
   regis check
   ```

2. Follow the installation instructions in [Getting Started](./getting-started.md) to install the missing tools.

3. **Using Docker** is the easiest path—the official image comes pre-packaged with all dependencies:
   ```bash
   docker run --rm ghcr.io/trivoallan/regis analyze nginx:latest
   ```

## Registry Authentication Errors

When analyzing private container images, you may encounter authentication failures.

**Error symptoms:**

- `401 Unauthorized`
- `403 Forbidden`
- `authentication required` when pulling from a private registry

**Solution:**

`regis` uses the same authentication mechanisms as regctl and Docker:

1. **Docker login** (most common):

   ```bash
   docker login registry.example.com
   regis analyze registry.example.com/myapp:v1.0
   ```

2. **Podman login**:

   ```bash
   podman login registry.example.com
   regis analyze registry.example.com/myapp:v1.0
   ```

3. **Environment variables** (for CI/CD):
   - Configure Docker credentials (`docker login`) before running `regis`; `regctl` reads the same credential store.

If you're using a custom authentication mechanism, consult [Registries](./registries.md) for advanced configuration options.

## Timeout or Network Errors

When analyzing very large images or connecting to slow registries, you may encounter timeouts.

**Error symptoms:**

- `connection timed out`
- `i/o timeout`
- Analysis hangs on large images

**Solutions:**

1. **Run in serial mode** to reduce concurrent load:

   ```bash
   regis analyze myimage:latest --max-workers 1
   ```

2. **Check your network connection** to the registry. Large images can take minutes to pull metadata.

3. **For very large images**, consider analyzing during off-peak hours or splitting the analysis across multiple runs.

## Report Generation Issues

Problems with the `--html` report or an empty/blank report file.

**Error symptoms:**

- `--html` produces an empty or partial `report.html`
- The JSON report is missing expected analyzer data

**Solutions:**

1. **Generate a self-contained HTML report** with `--html`. It writes a single portable `report.html` that needs no base URL or web server:

   ```bash
   regis analyze nginx:latest --html
   ```

2. **Review the JSON report** to ensure the analysis succeeded:

   ```bash
   regis analyze nginx:latest -o report.json
   cat report.json | jq .
   ```

For detailed information on how reports work, see [Reports](../concepts/reports.md).

## Playbook Evaluation Issues

Rules marked as "incomplete" or unexpected scores.

**Error symptoms:**

- Rules status shows `incomplete` instead of `pass` or `fail`
- Scores don't match expected values
- Rule conditions reference missing analyzer data

**Solutions:**

1. **Verify the analyzer ran**. Incomplete rules indicate that the data they depend on was not generated. Check which analyzers participated in the run:

   ```bash
   regis analyze myimage:latest -o report.json
   cat report.json | jq '.analyzers | keys'
   ```

2. **Ensure your playbook doesn't reference non-existent analyzers**. For example, if you include a `cve` rule but didn't run the cve analyzer, the rule will be incomplete.

3. **Check your rule conditions** in your playbook. If a rule accesses a field that an analyzer didn't populate, it will be marked incomplete rather than failed.

For detailed information on rule evaluation, see [Rules](../concepts/rules.md) and [Scoring](../concepts/scoring.md).

## FAQ

### What registries does Regis support?

Regis supports any OCI-compliant container registry (Docker Hub, Quay.io, ECR, GCR, Azure Container Registry, your private registry, etc.). As long as the image reference is valid and you have authentication, Regis can analyze it.

### What image formats are supported?

Regis supports standard OCI container images. It does not support:

- Image archives in Docker `.tar` format
- Helm charts or other packaging formats
- Non-container artifacts

For local images, use the full reference: `docker.io/library/nginx:latest` or `localhost:5000/myimage:v1`.

### How do I run only specific analyzers?

Use the `-a` or `--analyzer` flag to limit which analyzers run:

```bash
# Run only CVE scanning and OCI metadata
regis analyze myimage:latest -a cve -a oci
```

This is useful when you only care about specific security checks or want to speed up analysis.

### How do I get verbose output?

Use the `--verbose` flag or set the `REGIS_LOG_LEVEL` environment variable:

```bash
# Verbose mode
regis analyze myimage:latest --verbose

# Debug logging
REGIS_LOG_LEVEL=DEBUG regis analyze myimage:latest
```

This will output detailed information about each analyzer's execution, registry calls, and rule evaluation.

### Can I run Regis in a CI/CD pipeline?

Yes. Regis is designed for CI/CD. Use Docker for simplicity:

```bash
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  trivoallan/regis analyze myimage:latest --html
```

Then collect the generated `report.html` (and `report.json`) as a CI artifact. See the [GitHub](./integrations/github.md) and [GitLab](./integrations/gitlab.md) integration guides for more details.
