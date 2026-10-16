# regis:0.18.0

## Command

```bash
uv run regis analyze ghcr.io/trivoallan/regis:0.18.0 --evaluate --html --output-dir reports/regis
```

## Playbook used

This example uses the [default Regis playbook](../index.md), which evaluates security, compliance, and image metadata against a comprehensive set of checks.

## What to expect

The Regis CLI image is a multi-tool container bundling regctl, grype, syft, trufflehog, Hadolint, and Dockle. Unlike minimal base images, this is a feature-rich image with comprehensive tooling. It is larger in size but comes with well-defined metadata labels and built-in supply chain provenance evidence.

## Key findings

Regis CLI examples typically exhibit:

- **Size**: Larger footprint due to included tooling (moderate score)
- **Labels**: Comprehensive metadata and documentation labels
- **Provenance**: Supply chain evidence and build provenance data
- **SBOM**: Complete Software Bill of Materials with detailed component tracking
- **Security**: Regular updates and vulnerability scanning

## Interpreting the report

For guidance on how scores are calculated and what each metric means, see [Scoring](../../../../concepts/scoring.md) and [Reports](../../../../concepts/reports.md).

## View the report

The report is not published with the documentation. Run the command above, then open `reports/regis/report.html` in a browser. The playbook used is [`regis/playbooks/default/playbook.yaml`](../../../../../regis/playbooks/default/playbook.yaml).
