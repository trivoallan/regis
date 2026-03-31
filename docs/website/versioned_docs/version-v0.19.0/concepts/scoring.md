---
tags:
  - scoring
---

# Scoring & Metrics

`regis` doesn't just provide raw data; it translates analysis results into actionable **Scores** and **Metrics** based on your security and operational policies.

## How Scores are Calculated

Scores are determined by the [Playbooks](./playbooks.md) you apply. A playbook defines rules, and each rule can contribute to a specific score category.

### Major Score Categories

- **Security Posture**: Derived from Trivy (CVEs), Hadolint (Dockerfile security), and Provenance checks.
- **Freshness**: Measures how recently the image was built and how far it has drifted from its base image.
- **Compliance**: Tracks adherence to internal standards (e.g., mandatory labels, allowed registries).
- **Efficiency**: Analyzes image size, layer count, and potential optimizations.

## Rule Weights

In a playbook, rules can be assigned different severities (e.g., `CRITICAL`, `HIGH`, `LOW`). These severities directly impact the final score:

- **Critical violations** often result in a "Fail" state for CI/CD pipelines.
- **Informational rules** provide insights without affecting the main status code.

## Interpreting Results

The final report provides a visual summary of these scores, allowing engineers to quickly identify if an image is "Production Ready."

:::note
Scores are subjective to the playbook used. An image might "Pass" a development playbook but "Fail" a strict production-hardening playbook.
:::
