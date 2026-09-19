## 1. Analyzer and schema

- [x] 1.1 Flag pre-1980 `created` as `reproducible_build` with null `age_days` in `freshness.py`; verify `tests/test_analyzer_freshness.py` epoch and real-date cases pass
- [x] 1.2 Add required `reproducible_build` boolean to `freshness.schema.json`; verify schema tests and `uv run pytest --no-cov -k schema` pass

## 2. Default criterion

- [x] 2.1 Change the `age` condition to `reproducible_build OR age_days < max_days` and reword the pass message; verify the rule test covers reproducible, fresh, stale and unknown-date cases

## 3. Verification

- [x] 3.1 Run `uv run pytest` and verify the coverage gates still pass
- [ ] 3.2 Re-run `regis analyze` on `gcr.io/distroless/static-debian12:nonroot` with the oci-supply-chain-spec playbook and verify `rules.age.passed` is true
