## Purpose

Defines how regis reports the age of an image tag and how the default `age` criterion judges it, so that reproducible builds are not penalised for a deliberately pinned build date.

## ADDED Requirements

### Requirement: Reproducible build detection

The freshness analyzer SHALL report `reproducible_build: true` and `age_days: null` when the image config `created` date is before 1980-01-01, and `reproducible_build: false` otherwise.

#### Scenario: Epoch-pinned image

- **WHEN** the config `created` is `1970-01-01T00:00:00Z`
- **THEN** `reproducible_build` is true and `age_days` is null

#### Scenario: Ordinary image

- **WHEN** the config `created` is a real past date
- **THEN** `reproducible_build` is false and `age_days` is the number of days since that date

### Requirement: Default age criterion

The default `age` criterion SHALL pass when `reproducible_build` is true or `age_days` is below `max_days`, and SHALL fail when the age is unknown for any other reason.

#### Scenario: Reproducible image passes

- **WHEN** `reproducible_build` is true and `age_days` is null
- **THEN** the criterion passes

#### Scenario: Stale image fails

- **WHEN** `reproducible_build` is false and `age_days` exceeds `max_days`
- **THEN** the criterion fails

#### Scenario: Unparseable date fails

- **WHEN** `created` is missing or not a valid timestamp
- **THEN** `age_days` is null, `reproducible_build` is false and the criterion fails
