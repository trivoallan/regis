# Business Logic

## Domain Rules

- Container analysis results must be evaluated consistently across analyzers and playbooks.
- Policy decisions should be reproducible from the stored analyzer outputs and rule definitions.

## Business Workflows

- Analyze an image or registry artifact.
- Run multiple analyzers concurrently.
- Evaluate playbook rules against the collected evidence.
- Produce human-readable and machine-readable outputs.

## Validation Rules

- Analyzer outputs should conform to their schemas.
- Playbook results should remain valid JSON structures.
- Security-related checks should fail clearly when severity thresholds are exceeded.

## Edge Cases & Exceptions

- Some analyzers depend on external tools being available in `PATH`.
- Registry access may require authentication.
- Release workflows may behave differently for bot-authored (Renovate) or protected branches.

## Domain Glossary

| Term     | Definition                                                   |
| -------- | ------------------------------------------------------------ |
| Analyzer | A plugin that extracts evidence or computes a specific check |
| Playbook | A policy definition that evaluates analyzer output           |
| Report   | The generated output for humans or automation                |
| Registry | OCI-compliant source for container images                    |
