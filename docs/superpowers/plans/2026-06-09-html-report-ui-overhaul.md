# HTML Report UI Overhaul — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flat single-file HTML report with a navigable, prioritized, Carbon-skinned dashboard (sticky TOC sidebar + triage panel + collapsible analyzer sections), staying strictly CSS-only and self-contained.

**Architecture:** Extract a pure `_build_context(report, sections) -> dict` in `regis/report/html.py` so the view-model (TOC entries, failing-analyzer set, CVE severity strip, triage data) is unit-testable without parsing HTML; rewrite the Jinja template `regis/templates/html/report.html.j2` to consume that context with CSS Grid, `<details>`, `:target`, `position: sticky`, and a `@media (max-width: 720px)` breakpoint. No CLI, signature, or format changes.

**Tech Stack:** Python 3.11, Jinja2, pytest. Spec: `docs/superpowers/specs/2026-06-09-html-report-ui-overhaul-design.md`.

---

## File Structure

- **Modify** `regis/report/html.py` — add `_source_rules()` and `_build_context()` helpers; `render_html_single()` delegates to `_build_context()` then renders.
- **Rewrite** `regis/templates/html/report.html.j2` — Carbon skin, grid layout, sidebar TOC, verdict hero, triage panel, severity strip, collapsible analyzer `<details>`, responsive media query. Existing value-rendering macros (`render_scalar`, `render_list_of_dicts`, `render_detail`) are preserved verbatim.
- **Add** `tests/report/test_html_context.py` — unit tests for `_build_context()`.
- **Add** `tests/report/test_html_layout.py` — HTML-output integration tests for the new structure.
- **Touch (only if assertions break)** `tests/report/test_html_single.py`, `tests/report/test_html_verdict.py` — these are designed to keep passing; adjust only if a rewrite detail breaks one.

Fast loop: `pipenv run pytest tests/report --no-cov -q`. Pre-PR gate: `pipenv run pytest` (coverage ≥ 90 % global and per-file).

---

## Task 1: Extract pure `_build_context()` (no behavior change)

**Files:**

- Modify: `regis/report/html.py`
- Test: `tests/report/test_html_single.py` (must stay green — no new test here)

- [ ] **Step 1: Read the current renderer**

Re-read `regis/report/html.py` lines 14-99 so you reproduce the existing logic exactly.

- [ ] **Step 2: Refactor — split context-building from rendering**

Replace the body of `render_html_single` so all context computation lives in a new private `_build_context`, and `render_html_single` only loads the template and renders. The returned dict must contain exactly the keys the current template already uses (`report`, `image_ref`, `show_details`, `filter_slugs`, `regis_version`, `generated_at`, `verdict`). Full new content of `regis/report/html.py`:

```python
"""Single-file HTML report renderer."""

from __future__ import annotations

import importlib.metadata
from datetime import datetime, timezone
from importlib import resources
from typing import Any

import click
from jinja2 import BaseLoader, Environment

_BADGE_CSS = {"error": "failed", "warning": "warning", "success": "passed"}


def _build_context(report: dict[str, Any], sections: str) -> dict[str, Any]:
    """Build the full template context for a report (pure: no template I/O)."""
    # Parse sections directive
    if sections == "all":
        show_details = True
        filter_slugs: set[str] | None = None
    elif sections == "summary":
        show_details = False
        filter_slugs = None
    else:
        show_details = True
        filter_slugs = {s.strip() for s in sections.split(",") if s.strip()}
        available = set(report.get("results", {}).keys())
        for slug in sorted(filter_slugs - available):
            click.echo(f"  Warning: unknown section '{slug}' (ignored)", err=True)

    # Build image_ref string
    req = report.get("request", {})
    image_ref = req.get("image_ref") or (
        f"{req.get('registry', '')}/{req.get('repository', '')}:{req.get('tag', '')}"
    )

    try:
        regis_version = importlib.metadata.version("regis")
    except importlib.metadata.PackageNotFoundError:
        regis_version = "dev"

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    from regis.playbook.verdict import (
        badge_emoji,
        build_verdict,
        format_counts,
        tier_label,
    )

    _v = build_verdict(report)
    verdict_view = None
    if _v.evaluated:
        verdict_view = {
            "headline": f"{tier_label(_v.tier, _v.tier_icon)} · {_v.score}/100",
            "score": _v.score,
            "counts": format_counts(_v),
            "badges": [
                {
                    "label": b.label,
                    "emoji": badge_emoji(b.klass),
                    "css": _BADGE_CSS.get(b.klass, "none"),
                }
                for b in _v.badges
            ],
            "failures": [
                {"slug": f.slug, "level": f.level, "message": f.message}
                for f in _v.failures
            ],
            "incompletes": [
                {"slug": i.slug, "level": i.level, "message": i.message}
                for i in _v.incompletes
            ],
        }

    return {
        "report": report,
        "image_ref": image_ref,
        "show_details": show_details,
        "filter_slugs": filter_slugs,
        "regis_version": regis_version,
        "generated_at": generated_at,
        "verdict": verdict_view,
    }


def render_html_single(report: dict[str, Any], sections: str = "all") -> str:
    """Render a self-contained single-file HTML report.

    Args:
        report: Full regis report dict.
        sections: "all" (default), "summary", or comma-separated analyzer slugs.

    Returns:
        Complete HTML string with inlined CSS, no external resources.
    """
    context = _build_context(report, sections)

    tmpl_path = resources.files("regis") / "templates" / "html" / "report.html.j2"
    tmpl_content = tmpl_path.read_text(encoding="utf-8")

    env = Environment(autoescape=True, loader=BaseLoader())
    template = env.from_string(tmpl_content)

    return template.render(**context)
```

Note: `verdict_view` now also carries `"score"` (used later by the hero ring). The template change that consumes it lands in Task 6; adding the key now is harmless.

- [ ] **Step 3: Run the existing suite to verify no regression**

Run: `pipenv run pytest tests/report --no-cov -q`
Expected: PASS (all existing `test_html_single.py` and `test_html_verdict.py` tests green — output is byte-identical except the new unused `score` key in the context).

- [ ] **Step 4: Commit**

```bash
git add regis/report/html.py
git commit -m "refactor(templates): extract pure _build_context in html renderer"
```

---

## Task 2: Add `toc` to the context

The TOC lists the analyzer sections that will render, each with a pass/fail status, respecting the `--sections` slug filter.

**Files:**

- Modify: `regis/report/html.py`
- Test: `tests/report/test_html_context.py` (new)

- [ ] **Step 1: Write the failing test**

Create `tests/report/test_html_context.py`:

```python
"""Unit tests for the pure view-model builder _build_context."""

from regis.report.html import _build_context


def _report(results=None, rules=None, tier="Gold", score=92):
    rules = rules if rules is not None else []
    return {
        "schemaVersion": 4,
        "request": {"registry": "r", "repository": "library/nginx", "tag": "1.27"},
        "results": results if results is not None else {},
        "tier": tier,
        "rules": rules,
        "rules_summary": {
            "score": score,
            "total": [r["slug"] for r in rules],
            "passed": [r["slug"] for r in rules if r["passed"]],
        },
    }


_FAILING_CVE_RULE = {
    "slug": "no-critical-cve",
    "level": "critical",
    "passed": False,
    "status": "failed",
    "message": "1 critical CVE",
    "analyzers": ["cve"],
}


class TestToc:
    def test_one_entry_per_analyzer(self):
        ctx = _build_context(
            _report(results={"cve": {"analyzer": "cve"}, "oci": {"analyzer": "oci"}}),
            "all",
        )
        slugs = [e["slug"] for e in ctx["toc"]]
        assert slugs == ["cve", "oci"]

    def test_status_reflects_failing_analyzers(self):
        ctx = _build_context(
            _report(
                results={"cve": {"analyzer": "cve"}, "oci": {"analyzer": "oci"}},
                rules=[_FAILING_CVE_RULE],
            ),
            "all",
        )
        status = {e["slug"]: e["status"] for e in ctx["toc"]}
        assert status == {"cve": "fail", "oci": "pass"}

    def test_respects_slug_filter(self):
        ctx = _build_context(
            _report(results={"cve": {}, "oci": {}}),
            "cve",
        )
        assert [e["slug"] for e in ctx["toc"]] == ["cve"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pipenv run pytest tests/report/test_html_context.py -x --no-cov -q`
Expected: FAIL with `KeyError: 'toc'`.

- [ ] **Step 3: Implement — add `_source_rules` and `toc`**

In `regis/report/html.py`, add this helper above `_build_context`:

```python
def _source_rules(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the evaluated rules (playbooks[0] first, else top-level)."""
    playbooks = report.get("playbooks") or []
    if playbooks:
        src = playbooks[0]
    elif "tier" in report or "rules" in report:
        src = report
    else:
        return []
    return list(src.get("rules") or [])
```

Inside `_build_context`, after `verdict_view` is built and before the `return`, add:

```python
    failing_analyzers: set[str] = {
        a
        for r in _source_rules(report)
        if not r.get("passed") and r.get("status") != "incomplete"
        for a in (r.get("analyzers") or [])
    }

    toc = [
        {
            "slug": name,
            "label": name,
            "status": "fail" if name in failing_analyzers else "pass",
        }
        for name in report.get("results", {})
        if filter_slugs is None or name in filter_slugs
    ]
```

Add `"toc": toc,` and `"failing_analyzers": failing_analyzers,` to the returned dict (you will assert on `failing_analyzers` in Task 3).

- [ ] **Step 4: Run test to verify it passes**

Run: `pipenv run pytest tests/report/test_html_context.py -x --no-cov -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add regis/report/html.py tests/report/test_html_context.py
git commit -m "feat(templates): compute TOC entries in html context"
```

---

## Task 3: Assert `failing_analyzers` in the context

`failing_analyzers` was added in Task 2; lock it with a dedicated test.

**Files:**

- Test: `tests/report/test_html_context.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/report/test_html_context.py`:

```python
class TestFailingAnalyzers:
    def test_collects_analyzers_of_failed_rules(self):
        ctx = _build_context(
            _report(
                results={"cve": {}, "oci": {}},
                rules=[
                    _FAILING_CVE_RULE,
                    {
                        "slug": "ok-rule",
                        "level": "info",
                        "passed": True,
                        "status": "passed",
                        "message": "",
                        "analyzers": ["oci"],
                    },
                ],
            ),
            "all",
        )
        assert ctx["failing_analyzers"] == {"cve"}

    def test_empty_when_all_pass(self):
        ctx = _build_context(_report(results={"cve": {}}), "all")
        assert ctx["failing_analyzers"] == set()
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pipenv run pytest tests/report/test_html_context.py::TestFailingAnalyzers -x --no-cov -q`
Expected: PASS (implementation already present from Task 2).

- [ ] **Step 3: Commit**

```bash
git add tests/report/test_html_context.py
git commit -m "test(templates): lock failing_analyzers computation"
```

---

## Task 4: Add CVE `severity` strip to the context

**Files:**

- Modify: `regis/report/html.py`
- Test: `tests/report/test_html_context.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/report/test_html_context.py`:

```python
class TestSeverity:
    def test_present_when_cve_analyzer(self):
        ctx = _build_context(
            _report(
                results={
                    "cve": {
                        "critical_count": 0,
                        "high_count": 1,
                        "medium_count": 4,
                        "low_count": 12,
                    }
                }
            ),
            "all",
        )
        sev = {c["css"]: c["count"] for c in ctx["severity"]}
        assert sev == {"critical": 0, "high": 1, "medium": 4, "low": 12}
        assert [c["label"] for c in ctx["severity"]] == [
            "critical",
            "high",
            "medium",
            "low",
        ]

    def test_absent_without_cve_analyzer(self):
        ctx = _build_context(_report(results={"oci": {}}), "all")
        assert ctx["severity"] is None

    def test_missing_counts_default_to_zero(self):
        ctx = _build_context(_report(results={"cve": {}}), "all")
        assert all(c["count"] == 0 for c in ctx["severity"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pipenv run pytest tests/report/test_html_context.py::TestSeverity -x --no-cov -q`
Expected: FAIL with `KeyError: 'severity'`.

- [ ] **Step 3: Implement — add `severity`**

In `regis/report/html.py`, add this module-level constant near `_BADGE_CSS`:

```python
# CVE severity strip: (display label / css class, source count key)
_SEVERITY_SPEC = [
    ("critical", "critical_count"),
    ("high", "high_count"),
    ("medium", "medium_count"),
    ("low", "low_count"),
]
```

Inside `_build_context`, before the `return`, add:

```python
    cve_result = report.get("results", {}).get("cve")
    severity = None
    if cve_result is not None:
        severity = [
            {"label": label, "css": label, "count": cve_result.get(key, 0)}
            for label, key in _SEVERITY_SPEC
        ]
```

Add `"severity": severity,` to the returned dict.

- [ ] **Step 4: Run test to verify it passes**

Run: `pipenv run pytest tests/report/test_html_context.py::TestSeverity -x --no-cov -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add regis/report/html.py tests/report/test_html_context.py
git commit -m "feat(templates): compute CVE severity strip in html context"
```

---

## Task 5: Add `triage` to the context

Triage reuses the already-computed verdict failures/incompletes and flags the all-clear state.

**Files:**

- Modify: `regis/report/html.py`
- Test: `tests/report/test_html_context.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/report/test_html_context.py`:

```python
class TestTriage:
    def test_lists_failures_and_flags_not_clear(self):
        ctx = _build_context(
            _report(results={"cve": {}}, rules=[_FAILING_CVE_RULE], score=80),
            "all",
        )
        triage = ctx["triage"]
        assert triage["clear"] is False
        assert [f["slug"] for f in triage["failures"]] == ["no-critical-cve"]

    def test_clear_when_all_pass(self):
        ctx = _build_context(
            _report(
                results={"cve": {}},
                rules=[
                    {
                        "slug": "ok",
                        "level": "info",
                        "passed": True,
                        "status": "passed",
                        "message": "",
                        "analyzers": ["cve"],
                    }
                ],
                score=100,
            ),
            "all",
        )
        assert ctx["triage"]["clear"] is True
        assert ctx["triage"]["failures"] == []

    def test_none_when_not_evaluated(self):
        ctx = _build_context(
            {"request": {"registry": "r", "repository": "x", "tag": "t"}, "results": {}},
            "all",
        )
        assert ctx["triage"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pipenv run pytest tests/report/test_html_context.py::TestTriage -x --no-cov -q`
Expected: FAIL with `KeyError: 'triage'`.

- [ ] **Step 3: Implement — add `triage`**

In `regis/report/html.py`, inside `_build_context`, after `verdict_view` is built, add:

```python
    triage = None
    if verdict_view is not None:
        triage = {
            "failures": verdict_view["failures"],
            "incompletes": verdict_view["incompletes"],
            "clear": not verdict_view["failures"] and not verdict_view["incompletes"],
        }
```

Add `"triage": triage,` to the returned dict.

- [ ] **Step 4: Run test to verify it passes**

Run: `pipenv run pytest tests/report/test_html_context.py::TestTriage -x --no-cov -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add regis/report/html.py tests/report/test_html_context.py
git commit -m "feat(templates): compute triage data in html context"
```

---

## Task 6: Rewrite the Jinja template (Carbon dashboard)

This wires the new context into the redesigned layout. The existing value-rendering macros are kept verbatim. Existing tests are designed to keep passing (textual hooks preserved: `class="verdict"`, `verdict.headline`, `Playbook results`, `Snapshot date`, `all pass ✓`, image ref in `<title>`, no `<script>`, no `http`).

**Files:**

- Rewrite: `regis/templates/html/report.html.j2`
- Test: `tests/report/test_html_layout.py` (new)

- [ ] **Step 1: Write the failing integration tests**

Create `tests/report/test_html_layout.py`:

```python
"""Integration tests for the redesigned single-file HTML layout."""

from regis.report.html import render_html_single


def _report(results=None, rules=None, tier="Gold", score=92):
    rules = rules if rules is not None else []
    return {
        "schemaVersion": 4,
        "request": {"registry": "r", "repository": "library/nginx", "tag": "1.27"},
        "results": results if results is not None else {},
        "tier": tier,
        "rules": rules,
        "rules_summary": {
            "score": score,
            "total": [r["slug"] for r in rules],
            "passed": [r["slug"] for r in rules if r["passed"]],
        },
    }


_FAILING_CVE_RULE = {
    "slug": "no-critical-cve",
    "level": "critical",
    "passed": False,
    "status": "failed",
    "message": "1 critical CVE",
    "analyzers": ["cve"],
}


def test_sidebar_toc_links_each_analyzer():
    html = render_html_single(_report(results={"cve": {}, "oci": {}}))
    assert 'class="toc"' in html
    assert 'href="#cve"' in html
    assert 'href="#oci"' in html


def test_failing_analyzer_details_open_passing_closed():
    html = render_html_single(
        _report(results={"cve": {"x": 1}, "oci": {"y": 2}}, rules=[_FAILING_CVE_RULE])
    )
    assert 'id="cve" open>' in html
    assert 'id="oci">' in html


def test_severity_strip_present_with_cve():
    html = render_html_single(
        _report(results={"cve": {"critical_count": 0, "high_count": 1}})
    )
    assert 'class="sev"' in html


def test_severity_strip_absent_without_cve():
    html = render_html_single(_report(results={"oci": {}}))
    assert 'class="sev"' not in html


def test_triage_attention_when_failing():
    html = render_html_single(
        _report(results={"cve": {}}, rules=[_FAILING_CVE_RULE], score=80)
    )
    assert "Attention required" in html
    assert "Severity" in html  # severity column, not "Level" (level vs tier, PR #703)
    assert "no-critical-cve" in html


def test_triage_all_clear_when_passing():
    html = render_html_single(
        _report(
            results={"cve": {}},
            rules=[
                {
                    "slug": "ok",
                    "level": "info",
                    "passed": True,
                    "status": "passed",
                    "message": "",
                    "analyzers": ["cve"],
                }
            ],
            score=100,
        )
    )
    assert "All checks passed" in html


def test_responsive_breakpoint_present():
    html = render_html_single(_report(results={"cve": {}}))
    assert "max-width:720px" in html or "max-width: 720px" in html


def test_still_self_contained():
    html = render_html_single(_report(results={"cve": {}}))
    assert "<script" not in html
    assert 'href="http' not in html
    assert 'src="http' not in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pipenv run pytest tests/report/test_html_layout.py -x --no-cov -q`
Expected: FAIL (current template has no `class="toc"`, `class="sev"`, `<details id=...>`, etc.).

- [ ] **Step 3: Rewrite the template**

Replace the entire content of `regis/templates/html/report.html.j2` with:

```jinja
{%- macro render_scalar(val) -%}
  {%- if val is none -%}<em>—</em>
  {%- elif val is sameas true -%}<span class="badge badge-pass">yes</span>
  {%- elif val is sameas false -%}<span class="badge badge-fail">no</span>
  {%- else -%}{{ val }}{%- endif -%}
{%- endmacro -%}

{%- macro render_list_of_dicts(items) -%}
  {%- set cols = items[0].keys() | list -%}
  <table>
    <thead><tr>{% for c in cols %}<th>{{ c }}</th>{% endfor %}</tr></thead>
    <tbody>
      {% for row in items %}
      <tr>{% for c in cols %}<td>{{ render_scalar(row[c] if c in row else none) }}</td>{% endfor %}</tr>
      {% endfor %}
    </tbody>
  </table>
{%- endmacro -%}

{%- macro render_detail(val) -%}
  {%- if val is none -%}
    <em>—</em>
  {%- elif val is mapping -%}
    <table>
      <tbody>
        {% for k, v in val.items() %}
        <tr><th>{{ k }}</th><td>{{ render_detail(v) }}</td></tr>
        {% endfor %}
      </tbody>
    </table>
  {%- elif val is iterable and val is not string -%}
    {%- set items = val | list -%}
    {%- if items | length == 0 -%}
      <em>none</em>
    {%- elif items[0] is mapping -%}
      {{ render_list_of_dicts(items) }}
    {%- else -%}
      <ul>{% for item in items %}<li>{{ item }}</li>{% endfor %}</ul>
    {%- endif -%}
  {%- elif val is sameas true -%}
    <span class="badge badge-pass">yes</span>
  {%- elif val is sameas false -%}
    <span class="badge badge-fail">no</span>
  {%- else -%}
    {{ val }}
  {%- endif -%}
{%- endmacro -%}

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ image_ref }} — regis report</title>
  <style>
    :root {
      --bg:#fff; --fg:#18181b; --muted:#71717a; --line:#e4e4e7; --panel:#fafafa;
      --crit:#991b1b; --crit-bg:#fef2f2; --high:#c2410c; --high-bg:#fff7ed;
      --med:#a16207; --low:#166534; --low-bg:#f0fdf4; --accent:#18181b;
    }
    *, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
    body { font-family:system-ui,-apple-system,sans-serif; font-size:14px; line-height:1.5; color:var(--fg); background:var(--bg); }
    .mono { font-family:ui-monospace,"SF Mono",Menlo,monospace; }
    a { color:inherit; }
    .layout { display:grid; grid-template-columns:200px 1fr; max-width:1200px; margin:0 auto; min-height:100vh; }
    .sidebar { position:sticky; top:0; align-self:start; max-height:100vh; overflow:auto; background:var(--panel); border-right:1px solid var(--line); padding:1.25rem 1rem; }
    .brand { font-weight:800; letter-spacing:.05em; margin-bottom:1rem; }
    .toc a { display:flex; justify-content:space-between; gap:.5rem; text-decoration:none; color:var(--muted); padding:.2rem 0; font-size:13px; }
    .toc a:hover { color:var(--fg); }
    .st-fail { color:var(--crit); font-weight:700; }
    .st-pass { color:var(--low); }
    main { padding:1.5rem 2rem; min-width:0; }
    header.rep { border-bottom:1px solid var(--line); padding-bottom:1rem; margin-bottom:1.25rem; }
    header.rep h1 { font-size:1.3rem; word-break:break-all; }
    header.rep .meta { display:grid; grid-template-columns:max-content 1fr; gap:.1rem .75rem; font-size:13px; margin-top:.5rem; }
    header.rep .meta dt { font-weight:600; color:var(--muted); }
    header.rep .meta dd { color:var(--fg); word-break:break-all; }
    .verdict { margin:1rem 0 1.25rem; }
    .hero { display:flex; align-items:center; gap:1rem; }
    .ring { width:64px; height:64px; border-radius:50%; border:5px solid var(--accent); display:flex; align-items:center; justify-content:center; font-weight:800; font-size:1.3rem; flex:0 0 auto; }
    .verdict-headline { font-size:1.2rem; margin:0; }
    .counts { color:var(--muted); font-size:13px; margin-top:.15rem; }
    .verdict-badges { margin-top:.5rem; }
    .pill, .badge { display:inline-block; padding:.12rem .5rem; border-radius:999px; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.02em; }
    .badge { border-radius:3px; }
    .badge-critical { background:var(--crit-bg); color:var(--crit); }
    .badge-high { background:var(--high-bg); color:var(--high); }
    .badge-medium { background:#fefce8; color:var(--med); }
    .badge-low { background:var(--low-bg); color:var(--low); }
    .badge-pass, .badge-passed { background:var(--low-bg); color:var(--low); }
    .badge-fail, .badge-failed { background:var(--crit-bg); color:var(--crit); }
    .badge-warn, .badge-warning, .badge-incomplete { background:var(--high-bg); color:var(--high); }
    .badge-none { background:var(--panel); color:var(--muted); }
    .triage { border:1px solid var(--line); border-left:3px solid var(--high); border-radius:6px; background:var(--panel); padding:.75rem 1rem; margin:1rem 0; }
    .triage.clear { border-left-color:var(--low); }
    .triage h2 { font-size:.95rem; margin-bottom:.4rem; }
    .triage table { width:100%; border-collapse:collapse; font-size:13px; margin:0; }
    .triage td { padding:.25rem .4rem; border:none; border-top:1px solid var(--line); vertical-align:top; background:transparent; }
    .triage th { padding:.25rem .4rem; border:none; border-bottom:1px solid var(--line); text-align:left; font-size:11px; text-transform:uppercase; color:var(--muted); background:transparent; }
    .sev { display:grid; grid-template-columns:repeat(4,1fr); gap:.5rem; margin:1rem 0; }
    .sev .cell { border:1px solid var(--line); border-radius:6px; text-align:center; padding:.5rem; }
    .sev .n { display:block; font-size:1.4rem; font-weight:800; line-height:1; }
    .sev .l { font-size:11px; text-transform:uppercase; color:var(--muted); }
    .sev .critical .n { color:var(--crit); } .sev .high .n { color:var(--high); }
    .sev .medium .n { color:var(--med); } .sev .low .n { color:var(--low); }
    h2.section-title { font-size:1rem; margin:1.5rem 0 .5rem; }
    details.an { border:1px solid var(--line); border-radius:6px; margin:.75rem 0; }
    details.an > summary { cursor:pointer; padding:.5rem .75rem; font-weight:700; list-style:none; display:flex; justify-content:space-between; align-items:center; }
    details.an > summary::-webkit-details-marker { display:none; }
    details.an > summary::before { content:"▸"; margin-right:.5rem; color:var(--muted); }
    details.an[open] > summary::before { content:"▾"; }
    details.an .an-body { padding:.25rem .75rem .75rem; }
    details.an:target { border-color:var(--accent); }
    table { border-collapse:collapse; width:100%; margin:.5rem 0; font-size:13px; }
    th { background:var(--panel); text-align:left; padding:.4rem .75rem; border:1px solid var(--line); font-weight:600; color:#52525b; }
    td { padding:.35rem .75rem; border:1px solid var(--line); vertical-align:top; }
    ul { padding-left:1.2rem; } li { margin:.1rem 0; }
    dl.scalars { display:grid; grid-template-columns:max-content 1fr; gap:.15rem .75rem; font-size:13px; }
    dl.scalars dt { font-weight:600; color:var(--muted); }
    em { color:var(--muted); font-style:normal; }
    footer { margin-top:2rem; padding-top:1rem; border-top:1px solid var(--line); color:var(--muted); font-size:12px; }
    @media (max-width:720px) {
      .layout { grid-template-columns:1fr; }
      .sidebar { position:sticky; top:0; max-height:none; height:auto; border-right:none; border-bottom:1px solid var(--line); padding:.6rem .75rem; z-index:5; }
      .brand { display:inline-block; margin:0 .5rem 0 0; }
      .toc { display:flex; gap:.4rem; overflow-x:auto; white-space:nowrap; }
      .toc a { flex:0 0 auto; border:1px solid var(--line); border-radius:999px; padding:.2rem .6rem; }
      .sev { grid-template-columns:repeat(2,1fr); }
      main { padding:1rem; }
    }
  </style>
</head>
<body>
<div class="layout">
  <aside class="sidebar">
    <div class="brand">regis</div>
    <nav class="toc">
      {% if verdict %}<a href="#verdict"><span>Verdict</span></a>{% endif %}
      {% if triage %}<a href="#triage"><span>Triage</span></a>{% endif %}
      {% for t in toc %}
      <a href="#{{ t.slug }}"><span>{{ t.label }}</span><span class="st-{{ t.status }}">{{ '✗' if t.status == 'fail' else '✓' }}</span></a>
      {% endfor %}
    </nav>
  </aside>

  <main>
    <header class="rep" id="top">
      <h1>{{ image_ref }}</h1>
      <dl class="meta">
        <dt>Registry</dt><dd>{{ report.request.registry }}</dd>
        <dt>Repository</dt><dd>{{ report.request.repository }}</dd>
        <dt>Tag</dt><dd class="mono">{{ report.request.tag }}</dd>
        {% if report.request.digest %}
        <dt>Digest</dt><dd class="mono">{{ report.request.digest }}</dd>
        {% endif %}
        {% if report.request.timestamp %}
        <dt>Analysis date</dt><dd>{{ report.request.timestamp }}</dd>
        {% endif %}
        {% if report.snapshot_date %}
        <dt>Snapshot date</dt><dd>{{ report.snapshot_date }}</dd>
        {% endif %}
      </dl>
    </header>

    {% if verdict %}
    <section id="verdict" class="verdict">
      <div class="hero">
        <div class="ring">{{ verdict.score }}</div>
        <div>
          <h2 class="verdict-headline">{{ verdict.headline }}</h2>
          <p class="counts">{{ verdict.counts }}</p>
        </div>
      </div>
      {% if verdict.badges %}
      <p class="verdict-badges">
        {% for b in verdict.badges %}
        <span class="badge badge-{{ b.css }}">{{ b.emoji }} {{ b.label }}</span>
        {% endfor %}
      </p>
      {% endif %}
    </section>
    {% endif %}

    {% if triage %}
    <section id="triage" class="triage {{ 'clear' if triage.clear else '' }}">
      <h2>{{ '✓ All checks passed' if triage.clear else '⚠ Attention required' }}</h2>
      {% if not triage.clear %}
      <table>
        <thead><tr><th></th><th>Rule</th><th>Severity</th><th>Detail</th></tr></thead>
        <tbody>
          {% for f in triage.failures %}
          <tr><td>✗</td><td class="mono">{{ f.slug }}</td><td>{{ f.level }}</td><td>{{ f.message }}</td></tr>
          {% endfor %}
          {% for i in triage.incompletes %}
          <tr><td>⚠</td><td class="mono">{{ i.slug }}</td><td>{{ i.level }}</td><td>{{ i.message }}</td></tr>
          {% endfor %}
        </tbody>
      </table>
      {% endif %}
    </section>
    {% endif %}

    {% if severity %}
    <section class="sev">
      {% for s in severity %}
      <div class="cell {{ s.css }}"><span class="n">{{ s.count }}</span><span class="l">{{ s.label }}</span></div>
      {% endfor %}
    </section>
    {% endif %}

    {% if report.playbooks %}
    <section id="playbooks">
      <h2 class="section-title">Playbook results</h2>
      <table>
        <thead>
          <tr><th>Playbook</th><th>Verdict</th><th>Score</th><th>Failing rules</th></tr>
        </thead>
        <tbody>
          {% for pb in report.playbooks %}
          <tr>
            <td>{{ pb.name | default('—') }}</td>
            <td>
              {% set pbv = pb.verdict | default('') | lower %}
              <span class="badge badge-{{ pbv }}">{{ pb.verdict | default('—') }}</span>
            </td>
            <td>{{ pb.score | default('—') }}{% if pb.score is not none %}%{% endif %}</td>
            <td>{{ pb.rules | default([]) | selectattr('passed', 'equalto', false) | list | length }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
    {% endif %}

    {% for analyzer_name, result in report.results.items() %}
    {% if filter_slugs is none or analyzer_name in filter_slugs %}
    <details class="an" id="{{ analyzer_name }}"{% if not show_details or analyzer_name in failing_analyzers %} open{% endif %}>
      <summary>
        <span>{{ analyzer_name }}</span>
        <span class="st-{{ 'fail' if analyzer_name in failing_analyzers else 'pass' }}">{{ '✗' if analyzer_name in failing_analyzers else '✓' }}</span>
      </summary>
      <div class="an-body">
        {% if not show_details %}
          <dl class="scalars">
            {% for k, v in result.items() %}
            {% if v is not mapping and (v is not iterable or v is string) %}
            <dt>{{ k }}</dt><dd>{{ render_scalar(v) }}</dd>
            {% endif %}
            {% endfor %}
          </dl>
        {% else %}
          {{ render_detail(result) }}
        {% endif %}
      </div>
    </details>
    {% endif %}
    {% endfor %}

    <footer>Generated by regis {{ regis_version }} on {{ generated_at }}</footer>
  </main>
</div>
</body>
</html>
```

- [ ] **Step 4: Run the new + existing report tests**

Run: `pipenv run pytest tests/report --no-cov -q`
Expected: PASS. If a `test_html_single.py` / `test_html_verdict.py` assertion broke, inspect the rendered HTML and either restore the textual hook in the template or update that single assertion to the new structure (do NOT weaken a self-contained/no-JS assertion).

- [ ] **Step 5: Commit**

```bash
git add regis/templates/html/report.html.j2 tests/report/test_html_layout.py
git commit -m "feat(templates): Carbon dashboard layout for single-file HTML report"
```

---

## Task 7: Visual verification + full gate

**Files:**

- None (verification only); fix template/CSS if rendering reveals issues.

- [ ] **Step 1: Render the real fixture**

Run:

```bash
pipenv run python -c "import json; from regis.report.html import render_html_single; open('/tmp/regis-report.html','w').write(render_html_single(json.load(open('tests/fixtures/report.v3.json')),'all'))"
```

Expected: file written, no traceback.

- [ ] **Step 2: Open in the preview and inspect**

Use the preview tools to open `file:///tmp/regis-report.html`. Verify visually:

- sidebar TOC sticky on the left with `Verdict`, `Triage`, `cve ✓`, `oci ✓`;
- verdict hero shows the score ring + `🥇 Gold · 100/100` + counts;
- triage shows the all-clear state (fixture has 1 passing rule);
- severity strip shows 0 / 1 / 4 / 12 (crit/high/med/low);
- analyzer `<details>` collapse/expand on click;
- resize narrow (<720px): sidebar collapses to a sticky horizontal pill bar, severity strip becomes 2×2.

Take a screenshot to share as proof. Fix any layout/CSS issue in `report.html.j2` and re-render.

- [ ] **Step 3: Run the full gate (coverage)**

Run: `pipenv run pytest`
Expected: PASS with coverage ≥ 90 % globally and on `regis/report/html.py`. If `html.py` dips below 90 %, add a `_build_context` unit test covering the uncovered branch (e.g. `image_ref` from `request.image_ref`, or `regis_version` fallback).

- [ ] **Step 4: Lint/format**

Run: `pipenv run ruff format . && pipenv run ruff check . && trunk check --fix`
Expected: clean (commit any autofixes).

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "test(templates): verify redesigned HTML report renders end-to-end"
```

---

## Self-Review (completed by plan author)

- **Spec coverage:** Layout/sidebar (Task 2 + 6), Carbon skin + responsive (Task 6), light-only/no-print (no dark/print code — satisfied by omission), triage-first collapse (Task 5 `failing_analyzers`-driven `open` in Task 6), view-model additions toc/failing_analyzers/severity/triage (Tasks 2-5), `--sections` modes preserved (Task 1 logic unchanged + Task 6 template branches), tests adapted + new (Tasks 1-7). No gaps.
- **Placeholder scan:** none — every code/template/test step contains full content.
- **Type consistency:** context keys (`toc`, `failing_analyzers`, `severity`, `triage`, `verdict.score`) are defined in Tasks 1-5 and consumed by the exact same names in the Task 6 template; severity `css`/`label` keys match between Task 4 builder and Task 6 `.sev .{css}` CSS and `.l` label.
