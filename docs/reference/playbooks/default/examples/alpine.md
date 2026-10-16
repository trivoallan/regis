# alpine:latest

## Command

```bash
uv run regis analyze alpine:latest --evaluate --html --output-dir reports/alpine
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

The report is not published with the documentation. Run the command above, then open `reports/alpine/report.html` in a browser. The playbook used is [`regis/playbooks/default/playbook.yaml`](../../../../../regis/playbooks/default/playbook.yaml).
