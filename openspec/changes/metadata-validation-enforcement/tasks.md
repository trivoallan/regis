## 1. Analyzer: several schema sources, no silent fallback

- [x] 1.1 Write failing tests: `MetadataAnalyzer` with two `meta_schema_paths` requires fields from
      both; `schema_sources` lists the loaded paths; an unparseable schema raises `AnalyzerError`
      instead of logging a warning
- [x] 1.2 Replace `meta_schema_path: Path | None` with `meta_schema_paths: Sequence[Path]`, stack
      every source into `allOf`, add `schema_sources` to the result, raise on an unreadable schema;
      update the existing call sites in `tests/test_analyzer_metadata.py`

## 2. Normal analyze path: the analyzer receives its inputs

- [x] 2.1 Write failing test: `analyze` with a bundle requiring `PROJECT_ID` and no `--meta`
      produces `results.metadata.valid == false` (today it is `true` — the false green)
- [x] 2.2 In `AnalyzeImage.run_and_evaluate`, rebind `selected["metadata"]` to a pre-bound factory
      carrying `metadata` and the resolved schema paths; widen `selected` to
      `Mapping[str, Callable[[], BaseAnalyzer]]`
- [x] 2.3 Resolve schema paths from `playbook_paths` via `bundle_meta_schema_path()` plus the
      explicit `--meta-schema` paths, in order

## 3. `--meta-schema` option

- [x] 3.1 Write failing tests: `--meta-schema` is honoured on the normal path and on
      `--rerun metadata`; a non-existent path is a usage error
- [x] 3.2 Add the repeatable `--meta-schema` option (`click.Path(exists=True, dir_okay=False,
path_type=Path)`) to `analyze`, thread it to both paths

## 4. Exit code 3 and the no-schema warning

- [x] 4.1 Write failing tests: exit 3 on a violation with a schema source, with and without
      `--fail`; report written before the exit; exit unchanged when no schema source is in force;
      exit 1 preserved for a rule breach; `--rerun metadata` exits 3
- [x] 4.2 Write failing test: `--meta` with a file (non-bundle) playbook warns on stderr and leaves
      `schema_sources` empty
- [x] 4.3 Implement the exit-3 check and the warning on both paths, after the report is emitted

## 5. Documentation

- [x] 5.1 Correct `docs/website/docs/concepts/playbooks.md` § Metadata: the "recorded as `null`"
      sentence (absent optional fields are `{"valid": true}`, not `null`), document `--meta-schema`,
      `schema_sources`, and the table comparing schema `required` (exit 3) with a playbook rule over
      `metadata.*` (exit 1 with `--fail`)
- [x] 5.2 Document exit codes 0/1/2/3 for `analyze` in `docs/website/docs/reference/cli.md`
- [x] 5.3 Add an `docs/website/docs/upgrade/` note: a bundle `meta.schema.json` that was inert now
      enforces, and a broken schema now aborts

## 6. Verification

- [x] 6.1 `uv run ruff check .`, `uv run ruff format .`, `trunk check`
- [x] 6.2 `uv run pytest` — full suite with both coverage gates
- [x] 6.3 End-to-end through the real CLI (offline, via `--rerun metadata`): a bundle requiring
      `SAISINE_URL`, run without it → exit 3, report written, field and schema path named; run with
      it → exit 0; the same schema via `--meta-schema` → exit 3; a file playbook → warning, exit 0

## 7. Visible derogation (`--meta-advisory`)

Added after the regulation analysis in design.md found that the bundle schema is not
necessarily the opt-in of the party that pays the exit code.

- [x] 7.1 Write failing tests: `enforcement` is `"enforcing"` by default and `"advisory"` under
      the derogation, with `valid`, `metadata_validation` and `schema_sources` untouched
- [x] 7.2 Add `advisory` to `MetadataAnalyzer`, emit `enforcement` in the result
- [x] 7.3 Thread `meta_advisory` through `run_and_evaluate` to the analyzer
- [x] 7.4 Write failing tests: `--meta-advisory` and `REGIS_META_ADVISORY` exit 0 while still
      naming the field; enforcing remains the default; the derogation does not mask a rule
      breach; `--rerun` records it too
- [x] 7.5 Add the `--meta-advisory` flag (with envvar) and read the derogation from
      `results.metadata.enforcement` in the sanction check, so both paths share one rule
- [x] 7.6 Document the derogation in `playbooks.md`, `reference/cli.md` (option, env-var table,
      exit codes) and the `upgrade/` note
- [x] 7.7 Verify end-to-end: derogation → exit 0 with the warning (even under `--quiet`) and
      `enforcement: "advisory"` in the report; without it → exit 3
