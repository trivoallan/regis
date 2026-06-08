# OCI platform whitelist/blacklist rules — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three platform-identity criteria (`platforms-required`, `platforms-whitelist`, `platforms-blacklist`) to the OCI analyzer, backed by a new flat `results.oci.platforms_supported` projection.

**Architecture:** A pure helper projects the list of platform objects into a deduplicated list of canonical `os/arch[/variant]` strings, emitted as a new optional field on the OCI analyzer output. Three new criteria in `default_criteria()` evaluate that field using the existing JSON Logic operators `contains_all`, `subset`, and `!`/`intersects` — no new operator, no engine change. Rule reference docs regenerate automatically from `default_criteria()`.

**Tech Stack:** Python 3.11, `pytest`, JSON Schema (draft-07), JSON Logic (`regis/rules/evaluator.py`), `regctl`.

**Reference spec:** `docs/superpowers/specs/2026-06-08-oci-platforms-whitelist-blacklist-design.md`

**Operator orientation (verified in `regis/rules/evaluator.py`):**
- `contains_all([a], [b])` → all elements of `b` are in `a`.
- `subset([a], [b])` → all elements of `a` are in `b`.
- `intersects([a], [b])` → any element of `a` is in `b`.

**Test commands:** `pipenv run pytest <path> -v --no-cov` for the fast loop; `pipenv run pytest` for the full coverage-gated run before the PR.

---

## File Structure

- `regis/analyzers/oci.py` — add module-level `_platforms_supported()` helper; emit `platforms_supported` in `analyze()`; append three criteria to `default_criteria()`.
- `regis/schemas/analyzer/oci.schema.json` — add the optional `platforms_supported` property (schema is `additionalProperties: false`, so this is mandatory for the field to validate).
- `tests/test_oci_analyzer.py` — projection unit tests, analyze-level wiring test, and functional evaluation tests for the three criteria.
- `docs/website/docs/reference/analyzers/oci.md` — document the new output field.
- `docs/website/docs/reference/rules/oci/*.md` — regenerated, not hand-written.

---

## Task 1: Platform projection helper

**Files:**
- Modify: `regis/analyzers/oci.py` (add a module-level helper near the other module helpers, e.g. just above `class OciAnalyzer`)
- Test: `tests/test_oci_analyzer.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_oci_analyzer.py`. Note the import update on line 12.

```python
# update the existing import line near the top of the file:
from regis.analyzers.oci import OciAnalyzer, _platforms_supported


def test_platforms_supported_dedup_and_order():
    platforms = [
        {"os": "linux", "architecture": "amd64"},
        {"os": "linux", "architecture": "arm64"},
        {"os": "linux", "architecture": "amd64"},  # duplicate
    ]
    assert _platforms_supported(platforms) == ["linux/amd64", "linux/arm64"]


def test_platforms_supported_includes_variant():
    platforms = [
        {"os": "linux", "architecture": "arm64", "variant": "v8"},
        {"os": "linux", "architecture": "arm", "variant": "v7"},
    ]
    assert _platforms_supported(platforms) == ["linux/arm64/v8", "linux/arm/v7"]


def test_platforms_supported_skips_unknown_and_missing():
    platforms = [
        {"os": "unknown", "architecture": "unknown"},
        {"os": "linux", "architecture": "unknown"},
        {"os": "linux"},  # missing architecture
        {"architecture": "amd64"},  # missing os
        {"os": "linux", "architecture": "amd64"},
    ]
    assert _platforms_supported(platforms) == ["linux/amd64"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pipenv run pytest tests/test_oci_analyzer.py -k platforms_supported -v --no-cov`
Expected: FAIL with `ImportError: cannot import name '_platforms_supported'`.

- [ ] **Step 3: Implement the helper**

Add to `regis/analyzers/oci.py`, as a module-level function above `class OciAnalyzer` (the file already imports `Any` from `typing`):

```python
def _platforms_supported(platforms: list[dict[str, Any]]) -> list[str]:
    """Project platform objects into canonical ``os/arch[/variant]`` strings.

    Skips entries whose ``os`` or ``architecture`` is missing or ``"unknown"``.
    Deduplicates while preserving first-seen order.
    """
    seen: list[str] = []
    for platform in platforms:
        os_name = platform.get("os")
        arch = platform.get("architecture")
        if not os_name or not arch or os_name == "unknown" or arch == "unknown":
            continue
        name = f"{os_name}/{arch}"
        variant = platform.get("variant")
        if variant:
            name = f"{name}/{variant}"
        if name not in seen:
            seen.append(name)
    return seen
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pipenv run pytest tests/test_oci_analyzer.py -k platforms_supported -v --no-cov`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add regis/analyzers/oci.py tests/test_oci_analyzer.py
git commit -m "feat(analyzer): add platforms_supported projection helper"
```

---

## Task 2: Emit `platforms_supported` in the analyzer output + schema

**Files:**
- Modify: `regis/analyzers/oci.py` (the `analyze()` return dict, currently `regis/analyzers/oci.py:253-258`)
- Modify: `regis/schemas/analyzer/oci.schema.json`
- Test: `tests/test_oci_analyzer.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_oci_analyzer.py`. It reuses the existing `_multiarch_dispatcher` and `_client` helpers already defined in the file.

```python
def test_oci_report_includes_platforms_supported():
    with patch("regis.analyzers.oci.run_regctl", side_effect=_multiarch_dispatcher):
        analyzer = OciAnalyzer()
        report = analyzer.analyze(_client(), "library/alpine", "3.20.10")

    # New field is present and schema-valid.
    analyzer.validate(report)
    assert "platforms_supported" in report
    supported = report["platforms_supported"]
    assert isinstance(supported, list)
    assert all(isinstance(name, str) for name in supported)
    # Multi-arch index resolves at least amd64 and arm64 linux platforms.
    assert "linux/amd64" in supported
    assert "linux/arm64" in supported
    # No "unknown" platforms leak into the projection.
    assert all("unknown" not in name for name in supported)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pipenv run pytest tests/test_oci_analyzer.py::test_oci_report_includes_platforms_supported -v --no-cov`
Expected: FAIL — `assert "platforms_supported" in report` (field not yet emitted). If the field were emitted without the schema change, `analyzer.validate(report)` would instead raise a `ValidationError` due to `additionalProperties: false`; either way the test is red until both edits below land.

- [ ] **Step 3: Add the field to the analyzer output**

In `regis/analyzers/oci.py`, update the `analyze()` return statement (currently `regis/analyzers/oci.py:253-258`):

```python
        return {
            "analyzer": self.name,
            "repository": repository,
            "tag": tag,
            "platforms": platforms,
            "platforms_supported": _platforms_supported(platforms),
            "tags": tags,
        }
```

- [ ] **Step 4: Add the property to the schema**

In `regis/schemas/analyzer/oci.schema.json`, add a `platforms_supported` property to the top-level `properties` object (alongside `platforms` and `tags`; do **not** add it to the top-level `required` array):

```json
    "platforms_supported": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Deduplicated canonical platform identifiers (os/arch[/variant]) supported by the image."
    },
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `pipenv run pytest tests/test_oci_analyzer.py -v --no-cov`
Expected: PASS (all OCI analyzer tests, including the new one).

- [ ] **Step 6: Commit**

```bash
git add regis/analyzers/oci.py regis/schemas/analyzer/oci.schema.json tests/test_oci_analyzer.py
git commit -m "feat(analyzer): emit platforms_supported on OCI report"
```

---

## Task 3: Three platform-identity criteria

**Files:**
- Modify: `regis/analyzers/oci.py` (`OciAnalyzer.default_criteria()`, insert after the `platforms-count` entry which ends at `regis/analyzers/oci.py:121`)
- Test: `tests/test_oci_analyzer.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_oci_analyzer.py`. Add this import near the top of the file:

```python
from regis.rules.evaluator import evaluate_rules
```

Then add the tests:

```python
def _oci_report(supported: list[str]) -> dict:
    return {
        "request": {"registry": "docker.io", "analyzers": ["oci"]},
        "results": {"oci": {"platforms_supported": supported}},
    }


def _eval_oci_criterion(supported: list[str], criterion: str, platforms: list[str]):
    rules_def = {
        "rules": [
            {
                "provider": "oci",
                "criterion": criterion,
                "slug": "under-test",
                "options": {"platforms": platforms},
            }
        ]
    }
    res = evaluate_rules(_oci_report(supported), rules_def)
    return next(r for r in res["rules"] if r["slug"] == "under-test")


def test_platforms_required_pass_and_fail():
    # All required platforms are supported (extras allowed) -> pass.
    passed = _eval_oci_criterion(
        ["linux/amd64", "linux/arm64", "windows/amd64"],
        "platforms-required",
        ["linux/amd64", "linux/arm64"],
    )
    assert passed["passed"] is True

    # A required platform is missing -> fail.
    failed = _eval_oci_criterion(
        ["linux/amd64"],
        "platforms-required",
        ["linux/amd64", "linux/arm64"],
    )
    assert failed["passed"] is False


def test_platforms_whitelist_pass_and_fail():
    # Every supported platform is allowed -> pass.
    passed = _eval_oci_criterion(
        ["linux/amd64", "linux/arm64"],
        "platforms-whitelist",
        ["linux/amd64", "linux/arm64", "windows/amd64"],
    )
    assert passed["passed"] is True

    # A supported platform is not in the allowed set -> fail.
    failed = _eval_oci_criterion(
        ["linux/amd64", "linux/arm64"],
        "platforms-whitelist",
        ["linux/amd64"],
    )
    assert failed["passed"] is False


def test_platforms_blacklist_pass_and_fail():
    # No forbidden platform is supported -> pass.
    passed = _eval_oci_criterion(
        ["linux/amd64", "linux/arm64"],
        "platforms-blacklist",
        ["windows/amd64"],
    )
    assert passed["passed"] is True

    # A forbidden platform is supported -> fail.
    failed = _eval_oci_criterion(
        ["linux/amd64", "linux/arm64"],
        "platforms-blacklist",
        ["linux/arm64"],
    )
    assert failed["passed"] is False


def test_platforms_required_fails_when_none_supported():
    # Empty projection cannot satisfy a required platform -> fail.
    failed = _eval_oci_criterion([], "platforms-required", ["linux/amd64"])
    assert failed["passed"] is False
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pipenv run pytest tests/test_oci_analyzer.py -k "platforms_required or platforms_whitelist or platforms_blacklist" -v --no-cov`
Expected: FAIL — the criteria slugs don't exist yet, so `evaluate_rules` produces no rule with slug `under-test` and `next(...)` raises `StopIteration`.

- [ ] **Step 3: Add the three criteria**

In `regis/analyzers/oci.py`, inside `OciAnalyzer.default_criteria()`, insert these three dict entries immediately **after** the `platforms-count` entry (which ends with `},` at `regis/analyzers/oci.py:121`):

```python
            {
                "slug": "platforms-required",
                "description": "Image must support a required set of platforms.",
                "level": "warning",
                "tags": ["compatibility"],
                "params": {"platforms": ["linux/amd64", "linux/arm64"]},
                "condition": {
                    "contains_all": [
                        {"var": "results.oci.platforms_supported"},
                        {"var": "criterion.params.platforms"},
                    ]
                },
                "messages": {
                    "pass": "Image supports all required platforms.",  # nosec B105
                    "fail": "Image is missing required platforms (supported: ${results.oci.platforms_supported}; required: ${criterion.params.platforms}).",
                },
            },
            {
                "slug": "platforms-whitelist",
                "description": "Image must only support allowed platforms.",
                "level": "warning",
                "tags": ["compatibility"],
                "params": {"platforms": ["linux/amd64", "linux/arm64"]},
                "condition": {
                    "subset": [
                        {"var": "results.oci.platforms_supported"},
                        {"var": "criterion.params.platforms"},
                    ]
                },
                "messages": {
                    "pass": "All supported platforms are allowed.",  # nosec B105
                    "fail": "Image supports disallowed platforms: ${results.oci.platforms_supported} (allowed: ${criterion.params.platforms}).",
                },
            },
            {
                "slug": "platforms-blacklist",
                "description": "Image must not support forbidden platforms.",
                "level": "warning",
                "tags": ["compatibility"],
                "params": {"platforms": ["windows/amd64"]},
                "condition": {
                    "!": {
                        "intersects": [
                            {"var": "results.oci.platforms_supported"},
                            {"var": "criterion.params.platforms"},
                        ]
                    }
                },
                "messages": {
                    "pass": "Image supports no forbidden platforms.",  # nosec B105
                    "fail": "Image supports forbidden platforms: ${results.oci.platforms_supported} (forbidden: ${criterion.params.platforms}).",
                },
            },
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pipenv run pytest tests/test_oci_analyzer.py -v --no-cov`
Expected: PASS (all OCI analyzer tests, including the four new criteria tests). The existing `test_oci_default_criteria_use_oci_paths` still passes because the new conditions use `results.oci.` and `criterion.params.`.

- [ ] **Step 5: Commit**

```bash
git add regis/analyzers/oci.py tests/test_oci_analyzer.py
git commit -m "feat(analyzer): add platform required/whitelist/blacklist criteria"
```

---

## Task 4: Documentation

**Files:**
- Modify: `docs/website/docs/reference/analyzers/oci.md`
- Regenerate: `docs/website/docs/reference/rules/oci/*.md`

- [ ] **Step 1: Document the new output field**

Open `docs/website/docs/reference/analyzers/oci.md` and locate the section/table describing the analyzer output fields (where `platforms`, `tags`, etc. are listed). Add an entry for the new field, matching the surrounding prose/table style. Use exactly this description:

> `platforms_supported` — Deduplicated canonical platform identifiers (`os/arch[/variant]`) supported by the image, e.g. `["linux/amd64", "linux/arm64"]`. Consumed by the `platforms-required`, `platforms-whitelist`, and `platforms-blacklist` rules.

If the page renders output as a JSON example, also add `"platforms_supported": ["linux/amd64", "linux/arm64"]` to that example object.

- [ ] **Step 2: Regenerate the rule reference pages**

Run: `pipenv run regis rules list -f markdown -D docs/website/docs/reference/rules`
Expected: three new files created — `docs/website/docs/reference/rules/oci/platforms-required.md`, `platforms-whitelist.md`, `platforms-blacklist.md` — plus an updated `oci/index.md` (this matches the CI command in `.github/workflows/cd-docs.yml`).

- [ ] **Step 3: Verify the generated pages**

Run: `git status --porcelain docs/website/docs/reference/rules/oci/`
Expected: the three new `platforms-*.md` files (and possibly an updated index) appear. Spot-check `platforms-required.md` shows the `platforms` parameter with default `["linux/amd64", "linux/arm64"]`.

- [ ] **Step 4: Commit**

```bash
git add docs/website/docs/reference/analyzers/oci.md docs/website/docs/reference/rules/oci/
git commit -m "docs(analyzer): document platform identity rules"
```

---

## Task 5: Full verification before PR

**Files:** none (verification only)

- [ ] **Step 1: Run the full test suite with coverage**

Run: `pipenv run pytest`
Expected: PASS, coverage ≥ 90% (the project gate).

- [ ] **Step 2: Lint and format**

Run: `pipenv run ruff check . && pipenv run ruff format --check .`
Expected: no errors. If `ruff format --check` reports diffs, run `pipenv run ruff format .` and amend the relevant commit.

- [ ] **Step 3: Confirm the working tree is clean**

Run: `git status`
Expected: clean (all changes committed).

---

## Self-Review Notes

- **Spec coverage:** projection field (Task 1+2), `oci.schema.json` update (Task 2), three criteria with exact conditions/params/messages (Task 3), exact-match + variant identity (covered by the helper in Task 1 and the variant test), edge cases (empty-projection required-fail test in Task 3), generated reference docs + analyzer field doc (Task 4). `platforms-count` left untouched; default playbook unchanged; no new operator — all consistent with the spec's "Out of scope".
- **Param name** is `platforms` uniformly across all three criteria and all tests.
- **Operator orientation** verified against `regis/rules/evaluator.py`: `contains_all(supported, required)`, `subset(supported, allowed)`, `!(intersects(supported, forbidden))`.
