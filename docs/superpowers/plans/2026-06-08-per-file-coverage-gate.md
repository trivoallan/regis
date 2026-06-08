# Per-file coverage gate (≥ 90 %) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `pipenv run pytest` fail when any single file under `regis/` is below 90 % coverage, after first raising the 8 currently-below-threshold files to ≥ 90 %.

**Architecture:** coverage.py only enforces a *global* `fail_under`. We add a small pytest plugin (`tests/_per_file_coverage.py`, wired via `tests/conftest.py`) that, after pytest-cov writes its data, loads the coverage data, computes per-file percentages, and fails the session if any file is below the same threshold read from `[tool.coverage.report].fail_under`. Tasks 1–8 raise the 8 legacy files first so the gate (Task 9) goes green immediately. Task 10 documents it.

**Tech Stack:** Python 3.10+, pytest, pytest-cov, coverage.py 7.x, `tomllib`. Tests mock at source module locations (project convention).

**Spec:** `docs/superpowers/specs/2026-06-08-per-file-coverage-gate-design.md`

---

## Conventions for every task

- Run a **single file's** coverage during the raise loop:
  `pipenv run pytest --cov=regis --cov-report=term-missing <testfile> -q`
  then read the line for the target file. (Coverage measures all imported `regis`
  modules, so a single test file is enough to report the target's percentage.)
- The example tests below are a **concrete starting point**. They use real symbol
  names and real patch targets (verified against the source), but the exact
  assertion strings / mock targets may need a one-line adjustment — the
  term-missing loop is the source of truth. **Iterate until the target file is
  ≥ 90 %, then commit.**
- Patch at the **source** module location (e.g. `regis.utils.process.subprocess`),
  never `regis.cli.*` (project convention, see `CLAUDE.md`).
- Trunk's pre-commit hook auto-formats; re-add and commit the produced changes.
- Commit scopes are mandatory (Conventional Commits).

**Order matters:** Tasks 1–8 (raise coverage) MUST land before Task 9 (arm the
gate), otherwise the suite goes red. Do them worst-file-first.

---

### Task 1: Raise `regis/tools/cosign.py` (73.3 % → ≥ 90 %)

**Files:**
- Test: `tests/tools/test_cosign.py` (extend)
- Under test: `regis/tools/cosign.py` (uncovered lines **29–46**)

**Uncovered behaviour:** `verify_blob()` builds the `cosign verify-blob` command
(29–41), runs it via `subprocess.run` (42–44), and raises
`CosignVerificationFailed` on non-zero return, using `stderr` or falling back to
`stdout` (45–46). Only the "cosign not found" path is currently tested.

- [ ] **Step 1: Write failing tests** — append to `tests/tools/test_cosign.py`:

```python
from unittest.mock import MagicMock, patch


def test_verify_blob_success(monkeypatch, tmp_path):
    monkeypatch.setattr("regis.tools.cosign.shutil.which", lambda _n: "/usr/bin/cosign")
    blob = tmp_path / "artifact.bin"
    blob.write_bytes(b"data")
    policy = CosignPolicy(
        issuer="https://token.actions.githubusercontent.com",
        identity_regex="^https://github\\.com/org/.*",
    )
    with patch("regis.tools.cosign.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stderr="", stdout="")
        verify_blob(blob, "https://r.example.com/bin.tar.gz", policy)
    cmd = run.call_args[0][0]
    assert cmd[1] == "verify-blob"
    assert "--signature" in cmd and "https://r.example.com/bin.tar.gz.sig" in cmd


def test_verify_blob_failure_uses_stderr(monkeypatch, tmp_path):
    monkeypatch.setattr("regis.tools.cosign.shutil.which", lambda _n: "/usr/bin/cosign")
    blob = tmp_path / "a.bin"
    blob.write_bytes(b"x")
    policy = CosignPolicy(issuer="i", identity_regex="r")
    with patch("regis.tools.cosign.subprocess.run") as run:
        run.return_value = MagicMock(returncode=1, stderr="bad signature", stdout="")
        with pytest.raises(CosignVerificationFailed) as exc:
            verify_blob(blob, "https://r.example.com/bin.tar.gz", policy)
    assert "bad signature" in str(exc.value)


def test_verify_blob_failure_falls_back_to_stdout(monkeypatch, tmp_path):
    monkeypatch.setattr("regis.tools.cosign.shutil.which", lambda _n: "/usr/bin/cosign")
    blob = tmp_path / "a.bin"
    blob.write_bytes(b"x")
    policy = CosignPolicy(issuer="i", identity_regex="r")
    with patch("regis.tools.cosign.subprocess.run") as run:
        run.return_value = MagicMock(returncode=1, stderr="", stdout="stdout error")
        with pytest.raises(CosignVerificationFailed) as exc:
            verify_blob(blob, "https://r.example.com/bin.tar.gz", policy)
    assert "stdout error" in str(exc.value)
```

> First read the top of `regis/tools/cosign.py` to confirm `CosignPolicy`'s field
> names and how `verify_blob` derives the `.sig`/`.pem` URLs and builds its error
> message; adjust the imports and assertions to match.

- [ ] **Step 2: Run, expect failures** — `pipenv run pytest tests/tools/test_cosign.py -q` → new tests fail (or error on a wrong symbol). Fix symbols until they run.
- [ ] **Step 3: Make them pass** — adjust assertions to the real command/message shape until green.
- [ ] **Step 4: Verify coverage** — `pipenv run pytest --cov=regis --cov-report=term-missing tests/tools/test_cosign.py -q` → `regis/tools/cosign.py` ≥ 90 %.
- [ ] **Step 5: Commit**

```bash
git add tests/tools/test_cosign.py
git commit -m "test(tools): cover cosign verify-blob success and failure paths"
```

---

### Task 2: Raise `regis/commands/doctor.py` (73.8 % → ≥ 90 %)

**Files:**
- Test: `tests/commands/test_doctor.py` (extend)
- Under test: `regis/commands/doctor.py` (uncovered **30–31, 33–35, 45–56**)

**Uncovered behaviour:** in `_print_tools_section()`, the cached+sha256-ok branch
(30–31) and the cached+sha256-mismatch branch (33–35, which sets `all_ok=False`);
and in `_get_version()`, the `except (FileNotFoundError, OSError, subprocess.TimeoutExpired): return None` path (45–56).

> First read `regis/commands/doctor.py` to confirm: the `ToolStatus` dataclass
> fields, the exact patch target for the status source (the agent suggested
> `regis.tools.fetcher.ToolFetcher.status`), how `doctor` is invoked (Click vs
> argparse), and `_get_version`'s real signature. Adjust below to match.

- [ ] **Step 1: Write failing tests** — add to `tests/commands/test_doctor.py`:

```python
def test_get_version_returns_none_on_filenotfound(monkeypatch):
    from regis.commands.doctor import _get_version
    def _raise(*a, **k):
        raise FileNotFoundError
    monkeypatch.setattr("regis.commands.doctor.subprocess.run", _raise)
    assert _get_version("/no/such/tool", "--version") is None


def test_get_version_returns_none_on_timeout(monkeypatch):
    import subprocess
    from regis.commands.doctor import _get_version
    def _raise(*a, **k):
        raise subprocess.TimeoutExpired(cmd="tool", timeout=5)
    monkeypatch.setattr("regis.commands.doctor.subprocess.run", _raise)
    assert _get_version("/usr/bin/tool", "--version") is None


def test_get_version_returns_none_on_oserror(monkeypatch):
    from regis.commands.doctor import _get_version
    def _raise(*a, **k):
        raise OSError("denied")
    monkeypatch.setattr("regis.commands.doctor.subprocess.run", _raise)
    assert _get_version("/usr/bin/tool", "--version") is None
```

For the cached/sha256 branches, add a test that patches the tool-status source to
return one cached+ok and one cached+mismatch `ToolStatus`, invokes `doctor`, and
asserts the `✓`/`MISMATCH` markers appear (and that a mismatch yields a non-zero
exit). Model the invocation on the existing tests already in this file.

- [ ] **Step 2: Run, expect failures** — `pipenv run pytest tests/commands/test_doctor.py -q`.
- [ ] **Step 3: Make them pass** — fix patch targets / invocation until green.
- [ ] **Step 4: Verify coverage** — `pipenv run pytest --cov=regis --cov-report=term-missing tests/commands/test_doctor.py -q` → `regis/commands/doctor.py` ≥ 90 %.
- [ ] **Step 5: Commit**

```bash
git add tests/commands/test_doctor.py
git commit -m "test(commands): cover doctor sha256 branches and version error paths"
```

---

### Task 3: Raise `regis/utils/process.py` (75.0 % → ≥ 90 %)

**Files:**
- Test: `tests/test_utils_process.py` (extend)
- Under test: `regis/utils/process.py` (uncovered **33–38, 60–62, 67–69, 73, 94–95, 98**)

**Uncovered behaviour:** `run_cmd()` non-zero-exit error raising (33–38) and the
`FileNotFoundError` "not found in PATH" path; the lazy helpers `_default_fetcher`
(60–62), `_manifest_names` (67–69), `_in_manifest` (73); and `ensure_tool()`'s
`ToolFetchError`→`ClickException` conversion (94–95) and install-hint message (98).

> First read `regis/utils/process.py` to confirm `run_cmd`'s signature (does it
> take `check=`, `step_label=`, `cwd=`?), the exact `ClickException` message
> strings, and where `load_manifest`/`ToolFetcher`/`ToolFetchError` are imported
> from. Adjust the tests accordingly.

- [ ] **Step 1: Write failing tests** — add to `tests/test_utils_process.py`:

```python
from unittest.mock import MagicMock, patch
import subprocess
import click
import pytest
from regis.utils.process import run_cmd, ensure_tool


def test_run_cmd_raises_on_nonzero_with_stderr():
    result = subprocess.CompletedProcess(["x"], 1, stdout="", stderr="boom")
    with patch("regis.utils.process.subprocess.run", return_value=result):
        with pytest.raises(click.ClickException) as exc:
            run_cmd(["x"], check=True)
    assert "boom" in exc.value.message


def test_run_cmd_raises_on_missing_binary():
    with patch("regis.utils.process.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(click.ClickException) as exc:
            run_cmd(["nope"], check=True)
    assert "not found in PATH" in exc.value.message


def test_ensure_tool_fetches_from_manifest():
    with patch("regis.utils.process.shutil.which", return_value=None), \
         patch("regis.utils.process._manifest_names", return_value=frozenset({"grype"})), \
         patch("regis.utils.process._default_fetcher") as fetcher:
        fetcher.return_value = MagicMock(ensure=MagicMock(return_value="/cache/grype"))
        assert str(ensure_tool("grype")) == "/cache/grype"


def test_ensure_tool_wraps_fetch_error():
    from regis.tools.fetcher import ToolFetchError
    with patch("regis.utils.process.shutil.which", return_value=None), \
         patch("regis.utils.process._manifest_names", return_value=frozenset({"grype"})), \
         patch("regis.utils.process._default_fetcher") as fetcher:
        fetcher.return_value = MagicMock(ensure=MagicMock(side_effect=ToolFetchError("dl failed")))
        with pytest.raises(click.ClickException) as exc:
            ensure_tool("grype")
    assert "dl failed" in exc.value.message


def test_ensure_tool_missing_with_install_hint():
    with patch("regis.utils.process.shutil.which", return_value=None), \
         patch("regis.utils.process._manifest_names", return_value=frozenset()):
        with pytest.raises(click.ClickException) as exc:
            ensure_tool("ghost", install_hint="brew install ghost")
    assert "brew install ghost" in exc.value.message
```

- [ ] **Step 2: Run, expect failures** — `pipenv run pytest tests/test_utils_process.py -q`.
- [ ] **Step 3: Make them pass** — align messages/targets until green.
- [ ] **Step 4: Verify coverage** — term-missing for `regis/utils/process.py` ≥ 90 %.
- [ ] **Step 5: Commit**

```bash
git add tests/test_utils_process.py
git commit -m "test(utils): cover run_cmd errors and ensure_tool fetch paths"
```

---

### Task 4: Raise `regis/playbook/sections.py` (78.6 % → ≥ 90 %)

**Files:**
- Test: `tests/test_playbook_sections.py` (**create** — no dedicated test today)
- Under test: `regis/playbook/sections.py` (uncovered **33–47, 159–160, 180, 187, 217, 237–265, 290, 292, 328–332, 338–342, 365, 377**)

**Highest-value blocks:** `_evaluate_scorecards` pre-evaluated branch (33–47);
`_evaluate_section` rule-reference processing (237–265); `resolve_widgets_final`
section/widget condition filtering (328–342) and subvalue/URL re-resolution
(365, 377). Functions are all module-level: `_evaluate_scorecards`,
`_evaluate_widgets`, `_build_render_order`, `_evaluate_section`,
`resolve_widgets_final`.

> First read `regis/playbook/sections.py` around each uncovered block to confirm
> the exact dict keys these functions read (e.g. `_pre_evaluated`/`_rule_result`,
> `rules`, `hint`, `condition`, `options.subvalue`, `url`) and the call
> signatures. Build minimal raw-context/section dicts that drive each branch.

- [ ] **Step 1: Write failing tests** — create `tests/test_playbook_sections.py`. Start with the largest blocks; representative cases:

```python
"""Coverage for regis/playbook/sections.py branches."""
from regis.playbook.sections import (
    _evaluate_scorecards,
    _evaluate_section,
    resolve_widgets_final,
)


def test_pre_evaluated_scorecard_is_passed_through():
    defs = [{
        "_pre_evaluated": True,
        "_rule_result": {
            "slug": "r1", "description": "Rule 1", "level": "bronze",
            "tags": ["sec"], "analyzers": ["cve"], "passed": True,
            "status": "passed", "message": "ok",
        },
    }]
    out = _evaluate_scorecards(defs, {})
    assert out[0]["name"] == "r1" and out[0]["passed"] is True


def test_section_rule_reference_by_slug():
    section = {"name": "S", "rules": ["my-rule"]}
    ctx = {"rules": {"my-rule": {
        "slug": "my-rule", "description": "My Rule", "level": "bronze",
        "tags": [], "analyzers": [], "passed": True, "status": "passed", "message": "",
    }}}
    out = _evaluate_section(section, ctx)
    assert any(c["name"] == "my-rule" for c in out["scorecards"])


def test_section_hint_and_condition_preserved():
    out = _evaluate_section(
        {"name": "S", "hint": "h", "condition": {"==": [1, 1]}, "scorecards": []}, {}
    )
    assert out["hint"] == "h" and out["condition"] == {"==": [1, 1]}


def test_resolve_widgets_final_filters_false_section_condition():
    pages = [{"sections": [
        {"name": "keep", "condition": {"==": [1, 1]}, "widgets": []},
        {"name": "drop", "condition": {"==": [1, 0]}, "widgets": []},
    ]}]
    resolve_widgets_final(pages, {})
    assert [s["name"] for s in pages[0]["sections"]] == ["keep"]


def test_resolve_widgets_final_filters_false_widget_condition():
    pages = [{"sections": [{"widgets": [
        {"label": "keep", "condition": {"==": [1, 1]}},
        {"label": "drop", "condition": {"==": [1, 0]}},
    ]}]}]
    resolve_widgets_final(pages, {})
    assert [w["label"] for w in pages[0]["sections"][0]["widgets"]] == ["keep"]
```

Add cases for: a widget whose condition raises (invalid operator) with no missing
data (skipped); a widget with `options.subvalue` resolving to `None` (line 180)
and with a `url` template (185–189); the tags-in-render-order branch (217); and
the subvalue/URL re-resolution in the final pass (365, 377). Drive each from the
term-missing output.

- [ ] **Step 2: Run, expect failures** — `pipenv run pytest tests/test_playbook_sections.py -q`.
- [ ] **Step 3: Make them pass / add cases** — iterate against term-missing.
- [ ] **Step 4: Verify coverage** — `regis/playbook/sections.py` ≥ 90 %.
- [ ] **Step 5: Commit**

```bash
git add tests/test_playbook_sections.py
git commit -m "test(playbook): cover sections scorecards, rule refs and final resolution"
```

---

### Task 5: Raise `regis/analyzers/endoflife.py` (79.4 % → ≥ 90 %)

**Files:**
- Test: `tests/test_endoflife.py` (extend)
- Under test: `regis/analyzers/endoflife.py` (uncovered **76, 99–108, 125, 173, 177**)

**Uncovered behaviour:** `_image_to_product` short-name fallback (76);
`_fetch_cycles` HTTP non-200 / error handling (99–108); `_match_cycle` major-
version fallback (125); and in `EndOfLifeAnalyzer.analyze`, `is_eol` derivation
for `eol=False` (173) and boolean `eol=True` (177).

> CRITICAL: confirm which HTTP client `_fetch_cycles` uses — read the imports at
> the top of `regis/analyzers/endoflife.py`. `pyproject.toml` ships `httpx`; the
> recipe assumed `requests`. Patch whatever it actually imports
> (e.g. `regis.analyzers.endoflife.httpx.get` or `...requests.get`). Also confirm
> how existing tests in `tests/test_endoflife.py` mock HTTP (look for `responses`
> or an `httpx` mock) and follow that pattern.

- [ ] **Step 1: Write failing tests** — add to `tests/test_endoflife.py` (pure-function cases are client-agnostic):

```python
from regis.analyzers.endoflife import _image_to_product, _match_cycle


def test_image_to_product_short_name_fallback():
    assert _image_to_product("myorg/nodejs") == "nodejs"


def test_match_cycle_major_version_fallback():
    cycles = [{"cycle": "1", "eol": False, "latest": "1.5.0"}]
    assert _match_cycle("1.5", cycles)["cycle"] == "1"
```

For `_fetch_cycles` (99–108): add tests mocking the real client to return a 404
(→ `None`) and to raise a transport/timeout error (→ `None`). For `analyze`
(173, 177): patch `regis.analyzers.endoflife._fetch_cycles` to return a cycle
list with `eol=False` (assert `report["is_eol"] is False`) and one with
`eol=True` (assert `report["is_eol"] is True`); reuse the existing
`MockRegistryClient` in the file.

- [ ] **Step 2: Run, expect failures** — `pipenv run pytest tests/test_endoflife.py -q`.
- [ ] **Step 3: Make them pass** — fix the HTTP patch target to the real client.
- [ ] **Step 4: Verify coverage** — `regis/analyzers/endoflife.py` ≥ 90 %.
- [ ] **Step 5: Commit**

```bash
git add tests/test_endoflife.py
git commit -m "test(analyzers): cover endoflife fetch errors and eol derivation"
```

---

### Task 6: Raise `regis/playbook/evaluator.py` (83.2 % → ≥ 90 %)

**Files:**
- Test: `tests/test_playbook_evaluator.py` (**create**)
- Under test: `regis/playbook/evaluator.py` (uncovered **40, 68–82, 150, 154–155, 237–238, 255–257, 267–269, 286**)

**Uncovered behaviour:** `_normalize_pages` pages-provided branch (40);
`_evaluate_pages` section-condition handling incl. missing-data tracking and
exception path (68–82); `_resolve_links` `.format(**report)` (150) and its
exception handling (154–155); and inside `evaluate`, tier-condition exception
(237–238), badge value interpolation (255–257), badge condition exception
(267–269), and label-without-value (286). Module functions: `_normalize_pages`,
`_evaluate_pages`, `_resolve_links`, `evaluate`.

> First read `regis/playbook/evaluator.py` around these lines to confirm the
> signatures of `_evaluate_pages` and `_resolve_links` (argument order/keys) and
> the shape of `evaluate(playbook, report)` output (`tier`, `badges`, `links`).
> The drafts below match the agent's reading but verify before trusting.

- [ ] **Step 1: Write failing tests** — create `tests/test_playbook_evaluator.py`:

```python
"""Coverage for regis/playbook/evaluator.py branches."""
from regis.playbook.evaluator import _normalize_pages, evaluate


def test_normalize_pages_returns_explicit_pages():
    pb = {"pages": [{"name": "P1", "sections": []}]}
    assert _normalize_pages(pb) == pb["pages"]


def test_badge_without_value_uses_scope_label():
    out = evaluate({"name": "x", "badges": [{"slug": "s", "scope": "Status"}]}, {})
    badge = out["badges"][0]
    assert badge["label"] == "Status" and badge["value"] is None


def test_badge_value_interpolation():
    pb = {"name": "x", "badges": [{"slug": "v", "scope": "Version", "value": "${version}"}]}
    out = evaluate(pb, {"version": "1.2.3"})
    assert out["badges"][0]["value"] == "1.2.3"


def test_badge_condition_exception_is_skipped():
    pb = {"name": "x", "badges": [
        {"slug": "bad", "scope": "T", "value": "X", "condition": {"invalid_op": [1, 2]}},
    ]}
    out = evaluate(pb, {})
    assert all(b["slug"] != "bad" for b in out.get("badges", []))
```

Add cases driving `_evaluate_pages` (a section whose condition is False with no
missing data → skipped; a condition referencing missing data → kept as
incomplete; an invalid-operator condition → exception path) and `_resolve_links`
(a `{repo}`-style URL formatted from `report`; a URL referencing a missing key →
link skipped via the exception handler), plus a tier whose condition uses an
invalid operator (237–238). Iterate against term-missing.

- [ ] **Step 2: Run, expect failures** — `pipenv run pytest tests/test_playbook_evaluator.py -q`.
- [ ] **Step 3: Make them pass / add cases** — iterate against term-missing.
- [ ] **Step 4: Verify coverage** — `regis/playbook/evaluator.py` ≥ 90 %.
- [ ] **Step 5: Commit**

```bash
git add tests/test_playbook_evaluator.py
git commit -m "test(playbook): cover evaluator pages, links, tiers and badges"
```

---

### Task 7: Raise `regis/rules/evaluator.py` (84.7 % → ≥ 90 %)

**Files:**
- Test: `tests/test_rules_evaluator.py` (extend)
- Under test: `regis/rules/evaluator.py` (uncovered **43, 56–63, 165–166, 195, 212–221, 234, 261, 266–279, 398–402**)

**Highest-value blocks:** `_interpolate_string` list `.length`/index access and
its error handling (56–63) and empty-template early return (43); custom-operator
edge branches registered in `_add_custom_operations` (non-list/non-dict inputs);
`resolve_rules` merge-when-already-present logic (266–279); and `evaluate_rules`
exception path (398–402).

> First read `regis/rules/evaluator.py` around 40–65, 200–280 and 359–402 to
> confirm `_interpolate_string`/`resolve_rules`/`evaluate_rules` signatures and
> the custom operator names. The custom ops (`intersects`, `contains_all`,
> `subset`, `keys`, `get`, `env_contains`) are registered globally via
> `_add_custom_operations()`; verify it has been called (import side effect) or
> call it in the test setup.

- [ ] **Step 1: Write failing tests** — add to `tests/test_rules_evaluator.py`. High-confidence cases:

```python
from regis.rules.evaluator import _interpolate_string, evaluate_rules


def test_interpolate_empty_template_returns_input():
    assert _interpolate_string("", {}) == ""


def test_interpolate_list_length_and_index():
    ctx = {"items": ["a", "b", "c"]}
    assert _interpolate_string("n=${items.length}", ctx) == "n=3"
    assert _interpolate_string("first=${items.0}", ctx) == "first=a"


def test_interpolate_list_index_out_of_range_keeps_placeholder():
    assert _interpolate_string("x=${items.9}", {"items": ["a"]}) == "x=${items.9}"


def test_evaluate_rules_condition_exception_marks_failed():
    report = {"request": {"registry": "docker.io", "analyzers": []}, "results": {}}
    rules_def = {"rules": [{
        "slug": "bad", "condition": {"invalid_op": [1, 2]},
        "messages": {"pass": "ok", "fail": "err"},
    }]}
    res = evaluate_rules(report, rules_def)
    bad = next(r for r in res["rules"] if r["slug"] == "bad")
    assert bad["passed"] is False
```

For the custom-operator edge branches, add a test exercising each operator with
non-list/non-dict inputs (the project registers them via `json_logic`; call them
through `evaluate_rules` with crafted conditions, or directly via the registered
`jsonLogic` if exposed). For the `resolve_rules` merge path (266–279), declare
the same provider+slug twice with different `messages`/`params` and assert they
merge. Iterate against term-missing.

- [ ] **Step 2: Run, expect failures** — `pipenv run pytest tests/test_rules_evaluator.py -q`.
- [ ] **Step 3: Make them pass / add cases** — iterate against term-missing.
- [ ] **Step 4: Verify coverage** — `regis/rules/evaluator.py` ≥ 90 %.
- [ ] **Step 5: Commit**

```bash
git add tests/test_rules_evaluator.py
git commit -m "test(rules): cover interpolation, custom operators and merge paths"
```

---

### Task 8: Raise `regis/playbook/conditions.py` (87.8 % → ≥ 90 %)

**Files:**
- Test: `tests/test_playbook_conditions.py` (**create**)
- Under test: `regis/playbook/conditions.py` (uncovered **47, 52–54, 89, 93**)

**Uncovered behaviour:** `evaluate_condition` falsy-condition early return (47)
and its exception handler returning an incomplete `ConditionResult` (52–54); and
`_stringify_condition`'s `in` (89) and `and` (93) operator branches.

> First read `regis/playbook/conditions.py` to confirm `evaluate_condition`'s
> signature (does it take a `label=`/tracker arg?), `ConditionResult`'s fields
> (`passed`, `incomplete`), and `_stringify_condition`'s output format.

- [ ] **Step 1: Write failing tests** — create `tests/test_playbook_conditions.py`:

```python
"""Coverage for regis/playbook/conditions.py branches."""
from regis.playbook.conditions import (
    ConditionResult,
    evaluate_condition,
    _stringify_condition,
)


def test_falsy_condition_returns_none():
    assert evaluate_condition(None, {}) is None
    assert evaluate_condition({}, {}) is None


def test_condition_exception_returns_incomplete():
    res = evaluate_condition({"/": [1, 0]}, {})  # division by zero
    assert isinstance(res, ConditionResult)
    assert res.passed is False and res.incomplete is True


def test_stringify_in_operator():
    out = _stringify_condition({"in": [{"var": "x"}, {"var": "xs"}]}, {"x": "a", "xs": ["a"]})
    assert " in " in out


def test_stringify_and_operator():
    out = _stringify_condition({"and": [{"==": [1, 1]}, {"==": [2, 2]}]}, {})
    assert " and " in out
```

- [ ] **Step 2: Run, expect failures** — `pipenv run pytest tests/test_playbook_conditions.py -q`.
- [ ] **Step 3: Make them pass** — adjust to the real signatures/format.
- [ ] **Step 4: Verify coverage** — `regis/playbook/conditions.py` ≥ 90 %.
- [ ] **Step 5: Commit**

```bash
git add tests/test_playbook_conditions.py
git commit -m "test(playbook): cover condition falsy/exception and stringify branches"
```

---

### Task 9: Add the per-file coverage gate plugin

**Files:**
- Create: `tests/_per_file_coverage.py`
- Modify: `tests/conftest.py` (register the `pytest_sessionfinish` hookwrapper)
- Test: `tests/test_per_file_coverage.py` (create)

**Design notes (validated during brainstorming):** a hookwrapper
`pytest_sessionfinish` runs *after* pytest-cov has written `.coverage`; loading a
fresh `coverage.Coverage()` then yields the same per-file percentages as the CLI
report. The `--no-cov` no-op is detected via `option.no_cov` / `option.cov_source`.
The gate lives under `tests/` (not measured by coverage), so it is exempt from
itself; its logic is unit-tested instead.

- [ ] **Step 1: Write the gate's unit tests (failing)** — create `tests/test_per_file_coverage.py`:

```python
"""Unit tests for the per-file coverage gate logic."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests import _per_file_coverage


def test_evaluate_coverage_flags_files_below_threshold():
    stats = {"regis/a.py": (10, 0), "regis/b.py": (10, 2), "regis/c.py": (100, 11)}
    assert _per_file_coverage.evaluate_coverage(stats, 90.0) == [
        ("regis/b.py", 80.0),
        ("regis/c.py", 89.0),
    ]


def test_evaluate_coverage_passes_at_exact_threshold():
    assert _per_file_coverage.evaluate_coverage({"ok.py": (10, 1)}, 90.0) == []


def test_evaluate_coverage_skips_zero_statement_files():
    assert _per_file_coverage.evaluate_coverage({"x/__init__.py": (0, 0)}, 90.0) == []


def test_read_threshold_reads_fail_under(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[tool.coverage.report]\nfail_under = 90\n", encoding="utf-8"
    )
    assert _per_file_coverage.read_threshold(tmp_path) == 90.0


def _session(no_cov, cov_source):
    return SimpleNamespace(
        config=SimpleNamespace(
            option=SimpleNamespace(no_cov=no_cov, cov_source=cov_source),
            rootpath=Path("."),
        ),
        exitstatus=0,
    )


def test_enforce_is_noop_when_coverage_disabled(monkeypatch):
    monkeypatch.setattr(
        _per_file_coverage, "_collect_stats",
        lambda _r: (_ for _ in ()).throw(AssertionError("should not run")),
    )
    session = _session(no_cov=True, cov_source=[])
    _per_file_coverage.enforce(session)
    assert session.exitstatus == 0


def test_enforce_fails_session_for_low_file(monkeypatch, capsys):
    monkeypatch.setattr(_per_file_coverage, "read_threshold", lambda _r: 90.0)
    monkeypatch.setattr(_per_file_coverage, "_collect_stats", lambda _r: {"regis/bad.py": (10, 5)})
    session = _session(no_cov=False, cov_source=["regis"])
    _per_file_coverage.enforce(session)
    assert session.exitstatus == pytest.ExitCode.TESTS_FAILED
    err = capsys.readouterr().err
    assert "regis/bad.py" in err and "below 90.0%" in err


def test_enforce_passes_when_all_meet_threshold(monkeypatch):
    monkeypatch.setattr(_per_file_coverage, "read_threshold", lambda _r: 90.0)
    monkeypatch.setattr(_per_file_coverage, "_collect_stats", lambda _r: {"regis/good.py": (10, 0)})
    session = _session(no_cov=False, cov_source=["regis"])
    _per_file_coverage.enforce(session)
    assert session.exitstatus == 0
```

- [ ] **Step 2: Run, expect failure** — `pipenv run pytest tests/test_per_file_coverage.py -q` → fails with `ModuleNotFoundError`/`AttributeError` (module not written yet).

- [ ] **Step 3: Write the plugin** — create `tests/_per_file_coverage.py`:

```python
"""Per-file coverage gate.

coverage.py only enforces a *global* ``fail_under`` threshold, so a poorly
tested file can hide behind well-covered ones. After pytest-cov writes its data,
this gate loads it and fails the session if any measured file is below the same
threshold (read from ``[tool.coverage.report].fail_under``). Wired in via
``tests/conftest.py``. Spec:
docs/superpowers/specs/2026-06-08-per-file-coverage-gate-design.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - 3.10 fallback
    import tomli as tomllib

import coverage
import pytest


def read_threshold(rootpath: Path) -> float:
    """Read the shared coverage threshold from ``[tool.coverage.report]``."""
    data = tomllib.loads((rootpath / "pyproject.toml").read_text(encoding="utf-8"))
    return float(data["tool"]["coverage"]["report"]["fail_under"])


def evaluate_coverage(
    stats: dict[str, tuple[int, int]], threshold: float
) -> list[tuple[str, float]]:
    """Return ``[(path, percent)]`` for files below ``threshold``, worst first.

    ``stats`` maps a display path to ``(n_statements, n_missing)``. Files with
    zero statements are skipped. The percentage is rounded to two decimals before
    comparison, mirroring coverage.py's reporting precision.
    """
    offenders: list[tuple[str, float]] = []
    for path, (n_statements, n_missing) in stats.items():
        if n_statements == 0:
            continue
        percent = 100.0 * (n_statements - n_missing) / n_statements
        if round(percent, 2) < threshold:
            offenders.append((path, percent))
    offenders.sort(key=lambda item: (item[1], item[0]))
    return offenders


def _collect_stats(rootpath: Path) -> dict[str, tuple[int, int]]:
    """Load on-disk coverage data into ``{display_path: (n_statements, n_missing)}``."""
    cov = coverage.Coverage()  # reads [tool.coverage] config (omit, etc.)
    cov.load()
    data = cov.get_data()
    stats: dict[str, tuple[int, int]] = {}
    for filename in data.measured_files():
        _, statements, _excluded, missing, _fmt = cov.analysis2(filename)
        try:
            display = str(Path(filename).relative_to(rootpath))
        except ValueError:
            display = filename
        stats[display] = (len(statements), len(missing))
    return stats


def enforce(session: pytest.Session) -> None:
    """Fail the pytest session if any measured file is below the threshold."""
    option = session.config.option
    if getattr(option, "no_cov", False) or not getattr(option, "cov_source", None):
        return  # coverage disabled (e.g. --no-cov): nothing to check
    rootpath = Path(session.config.rootpath)
    threshold = read_threshold(rootpath)
    offenders = evaluate_coverage(_collect_stats(rootpath), threshold)
    if not offenders:
        return
    lines = [f"Per-file coverage gate: {len(offenders)} file(s) below {threshold:.1f}%"]
    lines += [f"  {percent:5.1f}%  {path}" for path, percent in offenders]
    print("\n" + "\n".join(lines), file=sys.stderr)
    session.exitstatus = pytest.ExitCode.TESTS_FAILED
```

- [ ] **Step 4: Run the gate's unit tests** — `pipenv run pytest tests/test_per_file_coverage.py -q` → PASS.

- [ ] **Step 5: Register the hook in `tests/conftest.py`** — add at the top (after the module docstring/imports) and append the hook:

```python
import pytest

from tests import _per_file_coverage


@pytest.hookimpl(hookwrapper=True)
def pytest_sessionfinish(session: pytest.Session):
    """Run the per-file coverage gate after pytest-cov writes its data."""
    yield
    _per_file_coverage.enforce(session)
```

> `import pytest` may already be present in `tests/conftest.py` — don't duplicate it.

- [ ] **Step 6: Run the FULL suite — expect green** — Tasks 1–8 brought every file ≥ 90 %, so the gate passes:

```bash
pipenv run pytest
```

Expected: `Required test coverage of 90% reached`, all tests pass, no
"Per-file coverage gate" message, exit 0.

- [ ] **Step 7: Sanity-check the gate actually bites** — temporarily append a throwaway uncovered branch to a small module to confirm the gate fails, then revert:

```bash
printf '\n\ndef _gate_probe(x):\n    if x:\n        return 1\n    return 2\n' >> regis/tools/cosign.py
pipenv run pytest -q; echo "exit=$?"   # expect a 'Per-file coverage gate' message + non-zero exit
git checkout -- regis/tools/cosign.py  # revert the probe
```

- [ ] **Step 8: Commit**

```bash
git add tests/_per_file_coverage.py tests/test_per_file_coverage.py tests/conftest.py
git commit -m "test(coverage): fail the suite on any file below the per-file threshold"
```

---

### Task 10: Document the gate

**Files:**
- Modify: `CLAUDE.md` (Commands section)
- Modify: `docs/memory-bank/systemPatterns.md` and/or `docs/memory-bank/techContext.md`

- [ ] **Step 1: Update `CLAUDE.md`** — in the Commands block, annotate the test
  commands to note the per-file gate. Add a line near the pytest commands, e.g.:

```markdown
pipenv run pytest             # Full run with coverage — fails if total < 90% OR any file < 90%
```

  And add a short note under the commands: "Coverage is enforced both globally
  and **per file** (no file < 90 %) by `tests/_per_file_coverage.py`. Use
  `--no-cov` for fast iteration (disables both gates)."

- [ ] **Step 2: Update the memory bank** — add an entry to
  `docs/memory-bank/systemPatterns.md` (and/or `techContext.md`) recording the
  rule and mechanism: a hookwrapper `pytest_sessionfinish` in `tests/conftest.py`
  delegating to `tests/_per_file_coverage.py`, threshold sourced from
  `[tool.coverage.report].fail_under`, exempting `tests/` and zero-statement
  files. Follow the existing taxonomy/format of that file.

- [ ] **Step 3: Verify docs render / lint** — `trunk check --fix` on the changed
  markdown; commit any auto-formatting.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md docs/memory-bank/
git commit -m "docs(tests): document the per-file coverage gate"
```

---

## Self-Review

**Spec coverage:**
- Behaviour (single command fails on any file < 90 %, `--no-cov` no-op, new files auto-blocked) → Task 9 (`enforce`, `option.no_cov` guard, `_collect_stats` scans all measured files).
- Plugin location/hook/data-source/threshold-source → Task 9 Steps 3 & 5 exactly as specified.
- Edge cases (`--no-cov`, `omit`, zero-statement, failure output + exitstatus) → covered by `enforce`/`evaluate_coverage` and their unit tests in Task 9.
- "Raise the 8 files first" → Tasks 1–8, worst-first, each ≥ 90 % before Task 9.
- Plugin itself tested → `tests/test_per_file_coverage.py` (Task 9).
- Integration & docs (no new CI step; CLAUDE.md + memory-bank) → Task 10.

**Placeholder scan:** none — every code step contains real code; the coverage-
raise tasks intentionally end in a measured term-missing gate (the iterative loop
is the spec, not a placeholder).

**Type/name consistency:** gate API names are consistent across the plugin and
its tests: `read_threshold`, `evaluate_coverage(stats, threshold)`,
`_collect_stats(rootpath)`, `enforce(session)`. Target symbol names in Tasks 1–8
were verified against the source. The only deliberately-flagged uncertainties
(HTTP client in `endoflife`, exact message strings, some `_resolve_links`/
`_evaluate_pages` signatures) carry an explicit "read the source first" note and
self-correct via the per-file coverage loop.
