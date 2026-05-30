# alpine:latest

## Command

```bash
pipenv run regis analyze alpine:latest --evaluate --site --output-dir docs/website/static/examples/playbooks/default/alpine
```

## Playbook used

This example uses the [default Regis playbook](../index.md), which evaluates security, compliance, and image metadata against a comprehensive set of checks.

## What to expect

Alpine is a minimal base image, typically just 5-10 MB. This results in excellent performance across several scoring dimensions: small image size, minimal attack surface, and few (if any) known CVEs. However, Alpine images tend to have sparse metadata labels, which may impact compliance scores.

## Key findings

Alpine examples typically exhibit:

- **Size**: Very compact footprint (excellent score)
- **CVEs**: Minimal or zero known vulnerabilities
- **Labels**: Few or no metadata labels
- **Freshness**: High score due to regular updates and active maintenance

## Interpreting the report

For guidance on how scores are calculated and what each metric means, see [Scoring](../../../../concepts/scoring.md) and [Reports](../../../../concepts/reports.md).

## View the report

Browse the generated report at [/examples/playbooks/default/alpine/index.html](pathname:///regis/examples/playbooks/default/alpine/index.html)
