# Registry Authentication

To analyze private images, `regis-cli` needs to authenticate with your container registry. It typically leverages the authentication mechanisms of its underlying [Analyzers](../concepts/analyzers.md), such as **Skopeo** and **Trivy**.

## Using Docker Credentials

The easiest way to authenticate is to run `docker login` before running an analysis. Most analyzers will automatically pick up the credentials from `~/.docker/config.json`.

```bash
docker login my-registry.com
regis analyze my-registry.com/private-repo:latest
```

## Provider-Specific Authentication

### GitHub Packages (GHCR)

Pass your `GITHUB_TOKEN` or a PAT via standard Docker login.

### Amazon ECR

Ensure your environment is configured with AWS credentials. You can use the AWS CLI helper:

```bash
aws ecr get-login-password --region region | docker login --username AWS --password-stdin 1234567890.dkr.ecr.region.amazonaws.com
```

### Google Artifact Registry (GAR)

Use the `gcloud` helper:

```bash
gcloud auth configure-docker region-docker.pkg.dev
```

## Troubleshooting

If you encounter `401 Unauthorized` or `403 Forbidden` errors:

1. **Verify Credentials**: Ensure the credentials used by `docker login` have pull permissions.
2. **Analyzer-Specific Flags**: Some analyzers might require explicit credential flags.
3. **Network/Proxy**: Check if your environment requires a proxy to reach the registry.

> [!IMPORTANT]
> Never hardcode credentials in your Playbooks or configuration files. Always use environment variables or CI/CD secrets.
