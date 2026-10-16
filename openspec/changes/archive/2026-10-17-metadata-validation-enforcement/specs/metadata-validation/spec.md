## Purpose

Defines how regis validates the metadata supplied with `--meta`, which schemas are in force, what
the report records, and how a malformed call is signalled — so that a playbook can declare a
required field and an omission has a consequence.

## ADDED Requirements

### Requirement: Effective metadata schema

Regis SHALL validate the supplied metadata against the union (JSON Schema `allOf`) of the
well-known schema, the `meta.schema.json` of each `--playbook` bundle, and each `--meta-schema`
path, in that order. A schema source SHALL only be able to add constraints, never relax those of
another source.

#### Scenario: Bundle schema is applied on the normal path

- **WHEN** `analyze` runs with a `--playbook` bundle whose `meta.schema.json` requires `PROJECT_ID`
  and `--meta` does not supply it
- **THEN** `results.metadata.valid` is false and `results.metadata.metadata_validation.PROJECT_ID.valid`
  is false

#### Scenario: Explicit schema path is applied

- **WHEN** `analyze` runs with `--meta-schema` pointing at a JSON Schema requiring `SAISINE_URL`
  and `--meta` does not supply it
- **THEN** `results.metadata.valid` is false

#### Scenario: Several sources stack

- **WHEN** a bundle schema requires `PROJECT_ID` and a `--meta-schema` requires `SAISINE_URL`
- **THEN** omitting either field makes `results.metadata.valid` false

#### Scenario: Supplied metadata reaches the analyzer

- **WHEN** `analyze` runs with `--meta PROJECT_ID=PROJ-42`
- **THEN** `results.metadata.metadata` contains `PROJECT_ID: PROJ-42`

### Requirement: Recorded schema provenance

Regis SHALL record in `results.metadata.schema_sources` the ordered list of schema files actually
loaded beyond the well-known schema, and SHALL record an empty list when none was loaded.

#### Scenario: No schema in force

- **WHEN** `analyze` runs with `--meta` and a `--playbook` that is a YAML file rather than a bundle
  directory
- **THEN** `results.metadata.schema_sources` is empty and a warning naming the playbook is written
  to stderr

#### Scenario: Sources are listed

- **WHEN** a bundle schema and a `--meta-schema` are both in force
- **THEN** `schema_sources` lists both paths in resolution order

### Requirement: Malformed-call exit code

When at least one schema source beyond the well-known schema is in force and the metadata
violates the effective schema, `analyze` SHALL write the report and then exit with code `3`,
independently of `--fail`. Exit code `3` SHALL NOT be used for a rule breach, which keeps exit
code `1`.

#### Scenario: Missing required field exits 3

- **WHEN** a bundle schema requires `SAISINE_URL` and it is not supplied
- **THEN** the process exits 3 and `report.json` has been written

#### Scenario: Exit 3 does not need `--fail`

- **WHEN** the same run omits `--fail`
- **THEN** the process still exits 3

#### Scenario: Rule breach keeps exit 1

- **WHEN** metadata is valid and a critical rule breaches with `--fail`
- **THEN** the process exits 1

#### Scenario: `--rerun metadata` enforces the same code

- **WHEN** `analyze --rerun metadata --report DIR --meta-schema S` is run without a required field
- **THEN** the report is updated and the process exits 3

### Requirement: Preserved behaviour without a schema source

When no schema source beyond the well-known schema is in force, `analyze` SHALL record the
validation outcome in the report and SHALL NOT change its exit code because of it.

#### Scenario: Well-known violation does not fail the run

- **WHEN** `analyze` runs with `--meta ci.platform=jenkins` and no bundle or `--meta-schema` schema
- **THEN** `results.metadata.valid` is false, a warning is written to stderr, and the exit code is
  unchanged from a run with valid metadata

#### Scenario: Valid metadata with no schema

- **WHEN** `analyze` runs with `--meta PROJECT_ID=PROJ-42` and no schema source
- **THEN** `results.metadata.valid` is true and the exit code is 0

### Requirement: Unreadable schema is a hard error

Regis SHALL abort with exit code `1` when a schema source is present but cannot be read or parsed,
rather than continuing without it.

#### Scenario: Malformed bundle schema

- **WHEN** a bundle's `meta.schema.json` is not valid JSON
- **THEN** `analyze` exits 1 with a message naming the file, and no report claims the metadata is
  valid

#### Scenario: Missing explicit schema path

- **WHEN** `--meta-schema` names a path that does not exist
- **THEN** the invocation is rejected as a usage error (exit 2)

### Requirement: Visible derogation

Regis SHALL provide a derogation (`--meta-advisory`, or `REGIS_META_ADVISORY`) that suspends the
exit-3 sanction without suspending the finding: validation still runs, the report still records
the violation, and `results.metadata.enforcement` SHALL be `"advisory"` so a downstream consumer
can see that a derogation was used and refuse it. Without the derogation, `enforcement` SHALL be
`"enforcing"`.

#### Scenario: Derogation returns zero but reports the violation

- **WHEN** `analyze --meta-schema S --meta-advisory` runs without a field `S` requires
- **THEN** the exit code is 0, `results.metadata.valid` is false,
  `results.metadata.metadata_validation` names the field, and
  `results.metadata.enforcement` is `"advisory"`

#### Scenario: Derogation stays legible

- **WHEN** the derogation applies, including under `--quiet`
- **THEN** the violation and the schemas it was checked against are written to stderr

#### Scenario: Derogation covers the metadata contract only

- **WHEN** the derogation applies and a critical rule breaches with `--fail`
- **THEN** the process exits 1 — the derogation never masks the verdict on the image

#### Scenario: Enforcing is the default

- **WHEN** no derogation is requested
- **THEN** `results.metadata.enforcement` is `"enforcing"` and a violation exits 3
