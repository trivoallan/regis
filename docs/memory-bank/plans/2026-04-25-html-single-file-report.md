# HTML Single-File Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `--html` flag to `regis analyze` and `regis evaluate` that generates a single self-contained `report.html` file (HTML + CSS, no JS, no external dependencies), with a `--sections` option to control which analyzer sections are included.

**Architecture:** Jinja2 template in `regis/templates/html/report.html.j2` rendered by a new `render_html_single()` in `regis/report/html.py`. The existing `--site` flag (Docusaurus multi-file) is renamed internally to `"html-site"` format. The function follows the same pattern as `_render_markdown()`: takes a `dict`, returns a `str`, delegating file I/O to `write_report()`.

**Tech Stack:** Python 3.11+, Jinja2 (already in Pipfile), Click, importlib.resources, importlib.metadata.

---

## File Map

| Action | Path                                  | Responsibility                                                                                                     |
| ------ | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Create | `regis/report/html.py`                | `render_html_single(report, sections)` function                                                                    |
| Create | `regis/templates/html/report.html.j2` | Full HTML+CSS template with Jinja2 macros                                                                          |
| Modify | `regis/utils/report.py`               | Add `sections` param to `render_and_save_reports`; add `html` branch; rename `html` → `html-site` branch           |
| Modify | `regis/commands/analyze.py`           | Rename `"html"` → `"html-site"` (×2); add `--html` flag + `--sections` option to both `analyze` and `evaluate_cmd` |
| Create | `tests/report/test_html_single.py`    | Unit tests for `render_html_single`                                                                                |
| Create | `tests/commands/test_analyze_html.py` | CLI integration tests                                                                                              |

---

## Task 1: Rename internal `"html"` → `"html-site"` format

This is a purely internal rename — no user-visible change yet. It clears the way for `"html"` to mean "single file".

**Files:**

- Modify: `regis/commands/analyze.py:351` and `:624`
- Modify: `regis/utils/report.py` — the `if fmt == "html":` branch

- [ ] **Step 1: Edit `regis/commands/analyze.py` — rename both occurrences**

  Line 350–351 (inside `analyze`):

  ```python
  if site:
      formats.append("html-site")
  ```

  Line 623–624 (inside `evaluate_cmd`):

  ```python
  if site:
      formats.append("html-site")
  ```

- [ ] **Step 2: Edit `regis/utils/report.py` — rename the `html` branch in `render_and_save_reports`**

  Change the `if fmt == "html":` block (currently around line 305) to `elif fmt == "html-site":`:

  ```python
  for fmt in formats:
      if fmt == "html-site":
          from regis.report.docusaurus import build_report_site
          # ... rest of block unchanged ...
  ```

- [ ] **Step 3: Run the full test suite to verify nothing is broken**

  ```bash
  pipenv run pytest --no-cov -x -q
  ```

  Expected: all tests pass (Docusaurus tests should still pass since `--site` still maps to the same code path, now called `"html-site"`).

- [ ] **Step 4: Commit**

  ```bash
  git add regis/commands/analyze.py regis/utils/report.py
  git commit -m "refactor(cli): rename internal html format to html-site"
  ```

---

## Task 2: Write failing tests for `render_html_single`

- [ ] **Step 1: Create `tests/report/__init__.py`**

  ```bash
  mkdir -p tests/report
  touch tests/report/__init__.py
  ```

- [ ] **Step 2: Create `tests/report/test_html_single.py` with failing tests**

  ```python
  """Tests for render_html_single in regis.report.html."""
  import pytest

  from regis.report.html import render_html_single


  def _minimal_report(**extra) -> dict:
      base = {
          "request": {
              "registry": "registry-1.docker.io",
              "repository": "library/nginx",
              "tag": "latest",
              "timestamp": "2026-04-25T10:00:00+00:00",
          },
          "results": {},
          "playbooks": [],
      }
      base.update(extra)
      return base


  class TestRenderHtmlSingle:
      def test_returns_string(self):
          html = render_html_single(_minimal_report())
          assert isinstance(html, str)

      def test_contains_doctype(self):
          html = render_html_single(_minimal_report())
          assert "<!DOCTYPE html>" in html

      def test_contains_image_ref_in_title(self):
          html = render_html_single(_minimal_report())
          assert "registry-1.docker.io/library/nginx:latest" in html

      def test_no_external_resources(self):
          html = render_html_single(_minimal_report())
          # Must not reference external URLs in link/script/img tags
          assert 'href="http' not in html
          assert 'src="http' not in html

      def test_no_javascript(self):
          html = render_html_single(_minimal_report())
          assert "<script" not in html

      def test_playbook_table_present_when_playbooks(self):
          report = _minimal_report(
              playbooks=[
                  {
                      "name": "default",
                      "verdict": "PASS",
                      "score": 95,
                      "rules": [{"passed": True}, {"passed": True}],
                  }
              ]
          )
          html = render_html_single(report)
          assert "default" in html
          assert "PASS" in html

      def test_playbook_table_absent_when_no_playbooks(self):
          html = render_html_single(_minimal_report())
          assert "Playbook results" not in html

      def test_snapshot_date_shown_when_present(self):
          html = render_html_single(_minimal_report(snapshot_date="2026-04-09"))
          assert "2026-04-09" in html

      def test_snapshot_date_absent_when_missing(self):
          html = render_html_single(_minimal_report())
          assert "Snapshot date" not in html

      def test_sections_all_includes_analyzer(self):
          report = _minimal_report(results={"trivy": {"score": 80, "cves": []}})
          html = render_html_single(report, sections="all")
          assert "trivy" in html

      def test_sections_summary_excludes_detail_tables(self):
          report = _minimal_report(
              results={
                  "trivy": {
                      "score": 80,
                      "vulnerabilities": [
                          {"id": "CVE-2023-1234", "severity": "CRITICAL"}
                      ],
                  }
              }
          )
          html = render_html_single(report, sections="summary")
          # score scalar shown, but CVE table detail not shown
          assert "trivy" in html
          assert "CVE-2023-1234" not in html

      def test_sections_filter_by_slug(self):
          report = _minimal_report(
              results={"trivy": {"score": 80}, "hadolint": {"warnings": 3}}
          )
          html = render_html_single(report, sections="trivy")
          assert "trivy" in html
          assert "hadolint" not in html

      def test_unknown_slug_warns_and_continues(self, capsys):
          report = _minimal_report(results={"trivy": {"score": 80}})
          # Should not raise even with unknown slug
          html = render_html_single(report, sections="unknown_analyzer")
          assert isinstance(html, str)

      def test_footer_contains_generated_by(self):
          html = render_html_single(_minimal_report())
          assert "Generated by regis" in html
  ```

- [ ] **Step 3: Run to confirm all tests fail with ImportError**

  ```bash
  pipenv run pytest tests/report/test_html_single.py -v --no-cov 2>&1 | head -20
  ```

  Expected: `ImportError: cannot import name 'render_html_single' from 'regis.report.html'`

---

## Task 3: Create `regis/report/html.py`

- [ ] **Step 1: Create the file**

  ```python
  """Single-file HTML report renderer."""

  from __future__ import annotations

  import importlib.metadata
  from datetime import datetime, timezone
  from importlib import resources
  from typing import Any

  import click
  from jinja2 import BaseLoader, Environment


  def render_html_single(report: dict[str, Any], sections: str = "all") -> str:
      """Render a self-contained single-file HTML report.

      Args:
          report: Full regis report dict.
          sections: "all" (default), "summary", or comma-separated analyzer slugs.

      Returns:
          Complete HTML string with inlined CSS, no external resources.
      """
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
              click.echo(
                  f"  Warning: unknown section '{slug}' (ignored)", err=True
              )

      # Load template from package resources
      tmpl_path = resources.files("regis") / "templates" / "html" / "report.html.j2"
      tmpl_content = tmpl_path.read_text(encoding="utf-8")

      import json

      env = Environment(autoescape=True, loader=BaseLoader())
      env.filters["to_json"] = lambda v: json.dumps(v, ensure_ascii=False)

      template = env.from_string(tmpl_content)

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

      return template.render(
          report=report,
          image_ref=image_ref,
          show_details=show_details,
          filter_slugs=filter_slugs,
          regis_version=regis_version,
          generated_at=generated_at,
      )
  ```

- [ ] **Step 2: Create the template directory and an empty placeholder**

  ```bash
  mkdir -p regis/templates/html
  touch regis/templates/html/report.html.j2
  ```

- [ ] **Step 3: Run tests — expect failures due to empty template**

  ```bash
  pipenv run pytest tests/report/test_html_single.py -v --no-cov 2>&1 | tail -20
  ```

  Expected: some tests fail (empty string returned), `test_returns_string` passes.

- [ ] **Step 4: Commit skeleton**

  ```bash
  git add regis/report/html.py regis/templates/html/ tests/report/
  git commit -m "feat(report): add render_html_single skeleton and failing tests"
  ```

---

## Task 4: Build the Jinja2 template

- [ ] **Step 1: Write `regis/templates/html/report.html.j2`**

  ```html
  {%- macro render_scalar(val) -%} {%- if val is none -%}<em>—</em> {%- elif val
  is sameas true -%}<span class="badge badge-pass">yes</span> {%- elif val is
  sameas false -%}<span class="badge badge-fail">no</span>
  {%- else -%}{{ val }}{%- endif -%} {%- endmacro -%} {%- macro
  render_list_of_dicts(items) -%} {%- set cols = items[0].keys() | list -%}
  <table>
    <thead>
      <tr>
        {% for c in cols %}
        <th>{{ c }}</th>
        {% endfor %}
      </tr>
    </thead>
    <tbody>
      {% for row in items %}
      <tr>
        {% for c in cols %}
        <td>{{ render_scalar(row[c] if c in row else none) }}</td>
        {% endfor %}
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {%- endmacro -%} {%- macro render_detail(val) -%} {%- if val is none -%}
  <em>—</em>
  {%- elif val is mapping -%}
  <table>
    <tbody>
      {% for k, v in val.items() %}
      <tr>
        <th>{{ k }}</th>
        <td>{{ render_detail(v) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {%- elif val is iterable and val is not string -%} {%- set items = val | list
  -%} {%- if items | length == 0 -%}
  <em>none</em>
  {%- elif items[0] is mapping -%} {{ render_list_of_dicts(items) }} {%- else
  -%}
  <ul>
    {% for item in items %}
    <li>{{ item }}</li>
    {% endfor %}
  </ul>
  {%- endif -%} {%- elif val is sameas true -%}
  <span class="badge badge-pass">yes</span>
  {%- elif val is sameas false -%}
  <span class="badge badge-fail">no</span>
  {%- else -%} {{ val }} {%- endif -%} {%- endmacro -%}

  <!DOCTYPE html>
  <html lang="en">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>{{ image_ref }} — regis report</title>
      <style>
        *,
        *::before,
        *::after {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }
        body {
          font-family:
            system-ui,
            -apple-system,
            sans-serif;
          font-size: 14px;
          line-height: 1.5;
          color: #1a1a1a;
          max-width: 1200px;
          margin: 0 auto;
          padding: 1rem 2rem;
        }
        header {
          border-bottom: 2px solid #2563eb;
          padding-bottom: 1rem;
          margin-bottom: 2rem;
        }
        h1 {
          font-size: 1.3rem;
          color: #1d4ed8;
          word-break: break-all;
          margin-bottom: 0.5rem;
        }
        h2 {
          font-size: 1rem;
          margin: 2rem 0 0.5rem;
          background: #f1f5f9;
          padding: 0.4rem 0.75rem;
          border-left: 3px solid #2563eb;
        }
        section {
          margin-bottom: 1.5rem;
        }
        dl.meta {
          display: grid;
          grid-template-columns: max-content 1fr;
          gap: 0.15rem 0.75rem;
          font-size: 13px;
        }
        dt {
          font-weight: 600;
          color: #64748b;
        }
        dd {
          color: #334155;
          word-break: break-all;
        }
        table {
          border-collapse: collapse;
          width: 100%;
          margin: 0.5rem 0 1rem;
          font-size: 13px;
        }
        th {
          background: #f8fafc;
          text-align: left;
          padding: 0.4rem 0.75rem;
          border: 1px solid #e2e8f0;
          font-weight: 600;
          color: #475569;
        }
        td {
          padding: 0.35rem 0.75rem;
          border: 1px solid #e2e8f0;
          vertical-align: top;
        }
        tr:nth-child(even) td {
          background: #f8fafc;
        }
        ul {
          padding-left: 1.2rem;
        }
        li {
          margin: 0.1rem 0;
        }
        .badge {
          display: inline-block;
          padding: 0.1rem 0.4rem;
          border-radius: 3px;
          font-size: 11px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.02em;
        }
        .badge-critical {
          background: #fee2e2;
          color: #991b1b;
        }
        .badge-high {
          background: #fef3c7;
          color: #92400e;
        }
        .badge-medium {
          background: #fef9c3;
          color: #854d0e;
        }
        .badge-low {
          background: #dcfce7;
          color: #166534;
        }
        .badge-pass,
        .badge-passed {
          background: #dcfce7;
          color: #166534;
        }
        .badge-fail,
        .badge-failed {
          background: #fee2e2;
          color: #991b1b;
        }
        .badge-warn,
        .badge-warning,
        .badge-incomplete {
          background: #fef3c7;
          color: #92400e;
        }
        .badge-none {
          background: #f1f5f9;
          color: #64748b;
        }
        em {
          color: #94a3b8;
          font-style: normal;
        }
        footer {
          margin-top: 3rem;
          padding-top: 1rem;
          border-top: 1px solid #e2e8f0;
          color: #94a3b8;
          font-size: 12px;
        }
      </style>
    </head>
    <body>
      <header>
        <h1>{{ image_ref }}</h1>
        <dl class="meta">
          <dt>Registry</dt>
          <dd>{{ report.request.registry }}</dd>
          <dt>Repository</dt>
          <dd>{{ report.request.repository }}</dd>
          <dt>Tag</dt>
          <dd>{{ report.request.tag }}</dd>
          {% if report.request.digest %}
          <dt>Digest</dt>
          <dd>{{ report.request.digest }}</dd>
          {% endif %} {% if report.request.timestamp %}
          <dt>Analysis date</dt>
          <dd>{{ report.request.timestamp }}</dd>
          {% endif %} {% if report.snapshot_date %}
          <dt>Snapshot date</dt>
          <dd>{{ report.snapshot_date }}</dd>
          {% endif %}
        </dl>
      </header>

      {% if report.playbooks %}
      <section id="playbooks">
        <h2>Playbook results</h2>
        <table>
          <thead>
            <tr>
              <th>Playbook</th>
              <th>Verdict</th>
              <th>Score</th>
              <th>Failing rules</th>
            </tr>
          </thead>
          <tbody>
            {% for pb in report.playbooks %}
            <tr>
              <td>{{ pb.name | default('—') }}</td>
              <td>
                {% set verdict = pb.verdict | default('') | lower %}
                <span class="badge badge-{{ verdict }}"
                  >{{ pb.verdict | default('—') }}</span
                >
              </td>
              <td>
                {{ pb.score | default('—') }}{% if pb.score is not none %}%{%
                endif %}
              </td>
              <td>
                {{ pb.rules | default([]) | selectattr('passed', 'equalto',
                false) | list | length }}
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </section>
      {% endif %} {% for analyzer_name, result in report.results.items() %} {%
      if filter_slugs is none or analyzer_name in filter_slugs %}
      <section id="{{ analyzer_name }}">
        <h2>{{ analyzer_name }}</h2>
        {% if not show_details %} {# Summary mode: render only top-level scalar
        fields #}
        <dl class="meta">
          {% for k, v in result.items() %} {% if v is not mapping and (v is not
          iterable or v is string) %}
          <dt>{{ k }}</dt>
          <dd>{{ render_scalar(v) }}</dd>
          {% endif %} {% endfor %}
        </dl>
        {% else %} {# Detail mode: render all fields #} {{ render_detail(result)
        }} {% endif %}
      </section>
      {% endif %} {% endfor %}

      <footer>
        Generated by regis {{ regis_version }} on {{ generated_at }}
      </footer>
    </body>
  </html>
  ```

- [ ] **Step 2: Run the tests**

  ```bash
  pipenv run pytest tests/report/test_html_single.py -v --no-cov
  ```

  Expected: all 13 tests pass.

- [ ] **Step 3: Run full suite to check for regressions**

  ```bash
  pipenv run pytest --no-cov -x -q
  ```

  Expected: all tests pass.

- [ ] **Step 4: Commit**

  ```bash
  git add regis/templates/html/report.html.j2
  git commit -m "feat(report): implement single-file HTML Jinja2 template"
  ```

---

## Task 5: Wire `--html` and `--sections` into the CLI

### 5a — Update `render_and_save_reports` signature

- [ ] **Step 1: Add `sections` parameter to `render_and_save_reports` in `regis/utils/report.py`**

  Change the signature:

  ```python
  def render_and_save_reports(
      report: dict[str, Any],
      formats: list[str],
      output_template: str | None,
      output_dir_template: str | None,
      theme: str,
      pretty: bool,
      base_url: str = "/",
      open_browser: bool = False,
      sections: str = "all",
  ) -> None:
  ```

  Add the new `elif fmt == "html":` branch inside the `for fmt in formats:` loop, **before** the `else:` branch:

  ```python
  elif fmt == "html":
      from regis.report.html import render_html_single

      rendered = render_html_single(report, sections=sections)
      file_tmpl = output_template or "report.html"
      write_report(
          dir_tmpl=output_dir_template or ".",
          file_tmpl=file_tmpl,
          report=report,
          fmt=fmt,
          rendered=rendered,
      )
  ```

- [ ] **Step 2: Run tests to confirm no regression**

  ```bash
  pipenv run pytest --no-cov -x -q
  ```

### 5b — Add `--html` flag and `--sections` to `analyze` command

- [ ] **Step 3: Add `--html` option to `analyze` in `regis/commands/analyze.py`**

  After the existing `--site` option (around line 127), add:

  ```python
  @click.option(
      "--html",
      "html_single",
      is_flag=True,
      default=False,
      help="Generate a self-contained single-file HTML report (report.html).",
  )
  @click.option(
      "--sections",
      "sections",
      default="all",
      help=(
          "Sections to include in the HTML report: 'all' (default), 'summary', "
          "or comma-separated analyzer slugs (e.g. 'trivy,hadolint'). "
          "Only applies to --html."
      ),
  )
  ```

- [ ] **Step 4: Add `html_single` and `sections` to the `analyze` function signature**

  ```python
  def analyze(
      url: str,
      analyzer_names: tuple[str, ...],
      playbook_paths: tuple[str, ...],
      output_template: str | None,
      output_dir_template: str | None,
      pretty: bool,
      site: bool,
      html_single: bool,
      sections: str,
      theme: str,
      meta: tuple[str, ...],
      auth: tuple[str, ...],
      cache: bool,
      platform: str | None = None,
      evaluate: bool = False,
      fail: bool = False,
      fail_level: str = "critical",
      base_url: str = "/",
      open_browser: bool = False,
      archive_dir: Path | None = None,
      max_workers: int = 4,
      rerun: str | None = None,
      report_dir: Path | None = None,
      markdown: bool = False,
      merge_meta: bool = False,
  ) -> None:
  ```

- [ ] **Step 5: Update `formats` building block in `analyze` (around line 347)**

  ```python
  formats = []
  if not archive_dir:
      formats.append("json")
  if site:
      formats.append("html-site")
  if html_single:
      formats.append("html")
  if markdown:
      formats.append("md")
  ```

- [ ] **Step 6: Pass `sections` to `render_and_save_reports` in `analyze`**

  Find the `render_and_save_reports(...)` call in `analyze` (around line 511) and add `sections=sections`:

  ```python
  render_and_save_reports(
      final_report,
      formats,
      output_template,
      output_dir_template,
      theme,
      pretty,
      base_url=base_url,
      open_browser=open_browser,
      sections=sections,
  )
  ```

  The `--rerun` path also calls `render_and_save_reports` (around line 297); add `sections=sections` there too.

### 5c — Same changes for `evaluate_cmd`

- [ ] **Step 7: Add `--html` and `--sections` options to `evaluate_cmd` (around line 571)**

  ```python
  @click.option(
      "--html",
      "html_single",
      is_flag=True,
      default=False,
      help="Generate a self-contained single-file HTML report (report.html).",
  )
  @click.option(
      "--sections",
      "sections",
      default="all",
      help=(
          "Sections to include in the HTML report: 'all' (default), 'summary', "
          "or comma-separated analyzer slugs. Only applies to --html."
      ),
  )
  ```

- [ ] **Step 8: Update `evaluate_cmd` function signature and body**

  Add `html_single: bool` and `sections: str` to the signature.

  Update formats block:

  ```python
  formats = ["json"]
  if site:
      formats.append("html-site")
  if html_single:
      formats.append("html")
  ```

  Add `sections=sections` to its `render_and_save_reports(...)` call.

- [ ] **Step 9: Run full test suite**

  ```bash
  pipenv run pytest --no-cov -x -q
  ```

  Expected: all tests pass.

- [ ] **Step 10: Commit**

  ```bash
  git add regis/commands/analyze.py regis/utils/report.py
  git commit -m "feat(cli): add --html and --sections options to analyze and evaluate"
  ```

---

## Task 6: CLI integration tests

- [ ] **Step 1: Create `tests/commands/test_analyze_html.py`**

  ```python
  """Integration tests for --html flag in regis analyze and evaluate."""

  import json
  from pathlib import Path
  from unittest.mock import MagicMock, patch

  import pytest
  from click.testing import CliRunner

  from regis.commands.analyze import analyze, evaluate_cmd


  _MINIMAL_REPORT = {
      "request": {
          "registry": "registry-1.docker.io",
          "repository": "library/nginx",
          "tag": "latest",
          "digest": "sha256-abc",
          "timestamp": "2026-04-25T10:00:00+00:00",
          "analyzers": [],
      },
      "results": {
          "trivy": {"score": 80, "vulnerabilities": []},
      },
      "playbooks": [],
  }


  @pytest.fixture()
  def runner():
      return CliRunner()


  @patch("regis.commands.analyze.RegistryClient")
  @patch("regis.commands.analyze._discover_analyzers")
  def test_html_flag_generates_report_html(mock_discover, mock_client, runner, tmp_path):
      """--html produces a report.html file."""
      mock_discover.return_value = {}

      # Build a report.json in tmp_path so the CLI uses it as cache
      report_json = tmp_path / "report.json"
      report_json.write_text(json.dumps(_MINIMAL_REPORT), encoding="utf-8")

      with runner.isolated_filesystem(temp_dir=tmp_path):
          with (
              patch("regis.commands.analyze.run_playbooks", return_value=_MINIMAL_REPORT),
              patch("regis.commands.analyze.validate_report"),
              patch("regis.commands.analyze.render_and_save_reports") as mock_render,
          ):
              result = runner.invoke(
                  analyze,
                  ["nginx:latest", "--html", "--output-dir", str(tmp_path)],
              )
              assert result.exit_code == 0, result.output
              # "html" must be in the formats list passed to render_and_save_reports
              call_args = mock_render.call_args
              formats = call_args[0][1]
              assert "html" in formats


  @patch("regis.commands.analyze.RegistryClient")
  @patch("regis.commands.analyze._discover_analyzers")
  def test_sections_passed_to_render(mock_discover, mock_client, runner, tmp_path):
      """--sections value is forwarded to render_and_save_reports."""
      mock_discover.return_value = {}

      with runner.isolated_filesystem(temp_dir=tmp_path):
          with (
              patch("regis.commands.analyze.run_playbooks", return_value=_MINIMAL_REPORT),
              patch("regis.commands.analyze.validate_report"),
              patch("regis.commands.analyze.render_and_save_reports") as mock_render,
          ):
              result = runner.invoke(
                  analyze,
                  [
                      "nginx:latest",
                      "--html",
                      "--sections",
                      "summary",
                      "--output-dir",
                      str(tmp_path),
                  ],
              )
              assert result.exit_code == 0, result.output
              call_kwargs = mock_render.call_args[1]
              assert call_kwargs.get("sections") == "summary"


  def test_evaluate_cmd_html_flag(runner, tmp_path):
      """evaluate --html produces html format in render call."""
      report_file = tmp_path / "report.json"
      report_file.write_text(json.dumps(_MINIMAL_REPORT), encoding="utf-8")

      with (
          patch("regis.commands.analyze.run_playbooks", return_value=_MINIMAL_REPORT),
          patch("regis.commands.analyze.validate_report"),
          patch("regis.commands.analyze.render_and_save_reports") as mock_render,
      ):
          result = runner.invoke(
              evaluate_cmd,
              [str(report_file), "--html", "--output-dir", str(tmp_path)],
          )
          assert result.exit_code == 0, result.output
          formats = mock_render.call_args[0][1]
          assert "html" in formats


  def test_render_and_save_html_writes_file(tmp_path):
      """render_and_save_reports with fmt=html writes report.html."""
      from regis.utils.report import render_and_save_reports

      with patch("regis.report.html.render_html_single", return_value="<html>ok</html>"):
          render_and_save_reports(
              _MINIMAL_REPORT,
              formats=["html"],
              output_template="report.html",
              output_dir_template=str(tmp_path),
              theme="default",
              pretty=True,
              sections="summary",
          )

      out = tmp_path / "report.html"
      assert out.exists()
      assert "<html>ok</html>" in out.read_text()
  ```

- [ ] **Step 2: Run the new tests**

  ```bash
  pipenv run pytest tests/commands/test_analyze_html.py -v --no-cov
  ```

  Expected: all tests pass.

- [ ] **Step 3: Run full test suite with coverage**

  ```bash
  pipenv run pytest -q
  ```

  Expected: all tests pass, coverage ≥ 90%.

- [ ] **Step 4: Lint check**

  ```bash
  pipenv run ruff check . && pipenv run ruff format --check .
  ```

  Fix any issues, then re-run.

- [ ] **Step 5: Commit**

  ```bash
  git add tests/commands/test_analyze_html.py
  git commit -m "test(cli): add integration tests for --html and --sections flags"
  ```

---

## Task 7: Final check and PR prep

- [ ] **Step 1: Smoke test with a real local report.json (if available)**

  ```bash
  # If you have a report.json locally:
  pipenv run regis evaluate path/to/report.json --html --output-dir /tmp/test-html --output report.html
  # Then open /tmp/test-html/report.html in a browser and verify it renders
  ```

- [ ] **Step 2: Verify `--site` still works (no regression on Docusaurus path)**

  ```bash
  # If Docusaurus / pnpm available:
  pipenv run regis evaluate path/to/report.json --site --output-dir /tmp/test-site
  # Verify the multi-file site is still generated
  ```

- [ ] **Step 3: Run trunk check**

  ```bash
  trunk check
  ```

  Fix any issues before opening the PR.

- [ ] **Step 4: Open PR**

  ```bash
  git push origin tritri/nostalgic-galileo-9bf742
  gh pr create \
    --title "feat(cli): add --html single-file report format" \
    --label "whats-new" \
    --body "$(cat <<'EOF'
  ## Summary

  - Adds `--html` flag to `regis analyze` and `regis evaluate` generating a self-contained `report.html` (HTML+CSS, no JS, no external dependencies).
  - Adds `--sections` option: `all` (default), `summary` (stats only), or comma-separated analyzer slugs.
  - Renames internal `"html"` format string to `"html-site"` (user-facing `--site` flag unchanged).
  - New file: `regis/report/html.py` + `regis/templates/html/report.html.j2`.

  ## Test plan

  - [ ] `pipenv run pytest tests/report/test_html_single.py` — 13 unit tests pass
  - [ ] `pipenv run pytest tests/commands/test_analyze_html.py` — integration tests pass
  - [ ] `pipenv run pytest` — full suite ≥ 90% coverage
  - [ ] `trunk check` — no lint issues
  - [ ] Manual: `regis evaluate report.json --html` generates a valid standalone HTML file
  - [ ] Manual: `regis analyze ... --site` still generates the Docusaurus site

  🤖 Generated with [Claude Code](https://claude.com/claude-code)
  EOF
  )"
  ```
