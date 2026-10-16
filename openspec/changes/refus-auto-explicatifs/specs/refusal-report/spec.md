# Spec Delta

## Purpose

Lets a platform operator explain a refused or incomplete admission verdict from the HTML report alone, without asking the regis maintainer which rule, fact, threshold or playbook produced it.

## ADDED Requirements

### Requirement: A failed rule cites its cause in the HTML report
For every rule whose status is `failed`, the HTML report SHALL show the rule's slug and description, the observed value of the image fact the rule tested, the threshold or parameters the rule applied, the name and version of the playbook that holds the rule, and the playbook's `ruleset_hash`.

#### Scenario: Failed rule with a numeric threshold
- **WHEN** an image is analyzed with a playbook whose rule `max-critical-cves` has `params.max: 0` and the image has 3 critical CVEs
- **THEN** the HTML report row for `max-critical-cves` shows the rule description, the observed value `3`, the threshold `max: 0`, the playbook name and version, and the `ruleset_hash`

#### Scenario: Observed value carried by the rule message
- **WHEN** the observed value is not available as a structured field and the playbook rule's `message` template interpolates the fact and the threshold
- **THEN** the HTML report shows that rendered message for the rule, and the playbook name and version and the `ruleset_hash` still appear

### Requirement: An incomplete rule names what was missing
For every rule whose status is `incomplete`, the HTML report SHALL label it distinctly from a failure and SHALL name the analyzers and data keys the condition needed but could not read. It SHALL NOT reuse the failure message as the only explanation.

#### Scenario: Missing analyzer output
- **WHEN** a rule's condition reads `results.sbom.packages` and the `sbom` analyzer produced no output
- **THEN** the HTML report shows the rule as incomplete, with a label different from the failure label, and names `results.sbom.packages` as missing

#### Scenario: Several missing keys
- **WHEN** a rule's condition reads two keys that are both absent
- **THEN** the HTML report lists both keys for that rule

### Requirement: The playbook result records missing keys per rule
Each rule entry in the playbook result SHALL carry a `missing_keys` list of the data keys its condition accessed but could not resolve. The list SHALL be empty for rules that are `passed` or `failed`. Adding this field SHALL NOT change the existing `slug`, `status`, `level` or `passed` fields.

#### Scenario: Incomplete rule entry
- **WHEN** a rule evaluates to `incomplete` because `results.provenance` is absent
- **THEN** the rule entry in `report.json` has `status: incomplete` and `missing_keys` containing `results.provenance`

#### Scenario: Existing consumers unaffected
- **WHEN** a consumer reads only `playbooks[0].rules[].status`, `level` and `slug`
- **THEN** it gets the same values as before the change

### Requirement: The playbook results table shows the real playbook
The HTML report's playbook results table SHALL show each playbook's name and its result tier. It SHALL NOT render a placeholder dash when the playbook has a name.

#### Scenario: Named playbook
- **WHEN** an image is analyzed with a playbook named `pilot-sncf` that yields tier `quarantine`
- **THEN** the playbook results table shows `pilot-sncf` and `quarantine`, and no cell for that playbook shows "—"
