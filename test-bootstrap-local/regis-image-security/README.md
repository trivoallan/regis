# RegiS Image Security

Container image security analysis and reporting.

## Getting Started

To run the analysis locally using the `regis-cli` Docker image:

```bash
docker run --rm \
  -v $(pwd)/reports:/app/reports \
  -v $(pwd)/playbooks:/app/playbooks \
  ghcr.io/trivoallan/regis-cli:0.13.0 \
  analyze ghcr.io/trivoallan/regis-cli:0.13.0 \
  -p playbooks/default.yaml \
  --site
```

## GitHub Actions

The analysis is automatically performed on `workflow_dispatch`. Reports are published to GitHub Pages.
