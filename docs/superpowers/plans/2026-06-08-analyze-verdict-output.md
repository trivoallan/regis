# Verdict Output for `regis analyze` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surface the playbook evaluation verdict (tier + score + badges) by default on every `regis analyze` run, rendered consistently across terminal, HTML, and markdown from a single shared `Verdict` model.

**Architecture:** A pure `build_verdict(final_report)` builder in `regis/playbook/verdict.py` normalizes the verdict into a frozen dataclass; three thin renderers (terminal/click, markdown, HTML/Jinja) consume it via shared mapping helpers (`tier_label`, `badge_emoji`). Tiers stay playbook-defined with an optional declarative `icon`; severity uses colored squares (🟥🟧🟩) to avoid clashing with tier medals.

**Tech Stack:** Python 3.11, `click`, Jinja2, `pytest` (coverage gate ≥ 90 %). No new runtime dependency (`rich` explicitly avoided).

**Spec:** `docs/superpowers/specs/2026-06-08-analyze-verdict-output-design.md`

---

## Background the engineer needs

The playbook evaluator (`regis/playbook/evaluator.py`, function `evaluate()`) returns a `result` dict per playbook. After a run, `final_report["playbooks"]` is a list of these dicts. The first one (`playbooks[0]`) is what we render. Relevant keys on that dict:

- `tier` — name of the matched tier (str), or **absent** if no tier condition matched.
- `badge_labels` — list of `{"name": str, "class": str}`, already **filtered and ordered** by `spec.presentation.badges` (produced by `regis/playbook/presentation.py::_resolve_badge_labels`). `class` ∈ `error|warning|success|information`. This is the display set — use it directly.
- `rules` — list of rule dicts, each `{"slug": str, "level": str, "passed": bool, "status": str, "message": str}`. `level` ∈ `critical|warning|info`. `status` is `"incomplete"` when the rule could not evaluate (missing analyzer data).
- `rules_summary` — `{"score": int, "total": int, "passed": int, "by_tag": ...}`. `score` is the unweighted percentage (kept as-is).

The current terminal summary lives in `regis/commands/analyze.py::_print_playbook_summary` (lines ~70-118). It is only invoked when `--playbook` is explicit (gate at the call site, `analyze.py` ~line 642). We replace it. Its existing logic for counting passed/failed/incomplete and computing the worst failed level is the reference to reuse:

```python
severity_order = {"critical": 0, "warning": 1, "info": 2}
passed = [r for r in rules if r.get("passed")]
failed = [r for r in rules if not r.get("passed") and r.get("status") != "incomplete"]
incomplete = [r for r in rules if r.get("status") == "incomplete"]
worst = min((r.get("level") or "info" for r in failed),
            key=lambda lv: severity_order.get(str(lv).lower(), 99)) if failed else None
```

The `--quiet` flag is read via `click.get_current_context(silent=True).obj["quiet"]`.

## File Structure

- **Create** `regis/playbook/verdict.py` — dataclasses (`RuleLine`, `VerdictBadge`, `Verdict`), mapping tables, helpers (`tier_label`, `badge_emoji`, `level_emoji`), and `build_verdict()`. Pure, no I/O, no click.
- **Modify** `regis/playbook/evaluator.py` — emit `tier_icon` next to `tier`.
- **Modify** `regis/schemas/playbook/v1alpha1/playbook.schema.json` — optional `icon` on tier items.
- **Modify** `regis/playbooks/default/playbook.yaml` — add 🥇🥈🥉 icons.
- **Modify** `regis/commands/analyze.py` — `_render_verdict_block` (replaces `_print_playbook_summary`), called by default, respects `-q`.
- **Modify** `regis/utils/report.py` — prefix verdict header inside `_render_markdown`.
- **Modify** `regis/report/html.py` + `regis/templates/html/report.html.j2` — `.verdict` panel.
- **Create** tests as listed per task.

---

## Task 1: Verdict model and `build_verdict`

**Files:**

- Create: `regis/playbook/verdict.py`
- Test: `tests/test_verdict.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_verdict.py`:

```python
from regis.playbook.verdict import (
    Verdict,
    VerdictBadge,
    RuleLine,
    build_verdict,
    tier_label,
    badge_emoji,
)


def _report(**pb):
    return {"playbooks": [pb]}


def test_build_verdict_from_playbooks_zero():
    report = _report(
        tier="Silver",
        tier_icon="🥈",
        rules_summary={"score": 78, "total": 20, "passed": 17},
        rules=[
            {"slug": "cve-critical", "level": "critical", "passed": False,
             "status": "failed", "message": "1 critical CVE (max 0)"},
            {"slug": "cve-high", "level": "warning", "passed": False,
             "status": "failed", "message": "12 high CVEs (max 10)"},
            {"slug": "scorecard-min", "level": "warning", "passed": False,
             "status": "incomplete", "message": "data unavailable"},
            *[{"slug": f"ok-{i}", "level": "info", "passed": True,
               "status": "passed", "message": ""} for i in range(17)],
        ],
        badge_labels=[
            {"name": "CVE: Critical", "class": "error"},
            {"name": "CVE: High", "class": "warning"},
        ],
    )
    v = build_verdict(report)
    assert v.evaluated is True
    assert v.tier == "Silver"
    assert v.tier_icon == "🥈"
    assert v.score == 78
    assert (v.total, v.passed, v.failed, v.incomplete) == (20, 17, 2, 1)
    assert v.worst_level == "critical"
    assert v.badges == [
        VerdictBadge(label="CVE: Critical", klass="error"),
        VerdictBadge(label="CVE: High", klass="warning"),
    ]
    assert [f.slug for f in v.failures] == ["cve-critical", "cve-high"]
    assert [i.slug for i in v.incompletes] == ["scorecard-min"]


def test_build_verdict_no_playbook_not_evaluated():
    v = build_verdict({"results": {}})
    assert v.evaluated is False
    assert v.tier is None and v.score == 0


def test_build_verdict_no_tier_matched():
    v = build_verdict(_report(rules_summary={"score": 42, "total": 1, "passed": 0},
                              rules=[], badge_labels=[]))
    assert v.tier is None
    assert v.tier_icon is None


def test_tier_label_variants():
    assert tier_label(None, None) == "⚪ Unrated"
    assert tier_label("Gold", "🥇") == "🥇 Gold"
    assert tier_label("Production-Ready", None) == "🏷️ Production-Ready"


def test_badge_emoji_mapping():
    assert badge_emoji("error") == "🟥"
    assert badge_emoji("warning") == "🟧"
    assert badge_emoji("success") == "🟩"
    assert badge_emoji("information") == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pipenv run pytest tests/test_verdict.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'regis.playbook.verdict'`

- [ ] **Step 3: Write the implementation**

Create `regis/playbook/verdict.py`:

```python
"""Shared verdict model for human-facing `regis analyze` output.

A single normalization point (`build_verdict`) feeds three thin renderers
(terminal, markdown, HTML) so a given tier renders identically everywhere.
Pure: no I/O, no click, no Jinja.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# --- Mapping tables (single source of truth) ---

TIER_FALLBACK_ICON = "🏷️"  # tier defined without a declared icon
TIER_NONE_LABEL = "⚪ Unrated"  # no tier condition matched

# Badge `class` is a fixed engine enum (not user-defined).
CLASS_EMOJI = {"error": "🟥", "warning": "🟧", "success": "🟩"}
# Rule `level` is a fixed engine enum.
LEVEL_EMOJI = {"critical": "🟥", "warning": "🟧", "info": "🟦"}
# click text colours (click has no orange; warning text falls back to yellow,
# the orange square emoji carries the medal-disambiguation).
LEVEL_STYLE = {"critical": "red", "warning": "yellow", "info": "blue"}

_SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}


@dataclass(frozen=True)
class RuleLine:
    slug: str
    level: str
    message: str


@dataclass(frozen=True)
class VerdictBadge:
    label: str
    klass: str


@dataclass(frozen=True)
class Verdict:
    evaluated: bool
    tier: str | None
    tier_icon: str | None
    score: int
    total: int
    passed: int
    failed: int
    incomplete: int
    worst_level: str | None
    badges: list[VerdictBadge] = field(default_factory=list)
    failures: list[RuleLine] = field(default_factory=list)
    incompletes: list[RuleLine] = field(default_factory=list)


def tier_label(tier: str | None, icon: str | None) -> str:
    """Render the tier headline label, e.g. '🥇 Gold' / '🏷️ Custom' / '⚪ Unrated'."""
    if not tier:
        return TIER_NONE_LABEL
    return f"{icon or TIER_FALLBACK_ICON} {tier}"


def badge_emoji(klass: str) -> str:
    """Emoji for a badge `class`; empty string for unknown/neutral classes."""
    return CLASS_EMOJI.get(klass, "")


def level_emoji(level: str | None) -> str:
    """Emoji for a rule `level`; empty string when unknown/None."""
    return LEVEL_EMOJI.get(str(level).lower(), "") if level else ""


def _source(final_report: dict[str, Any]) -> dict[str, Any] | None:
    """Pick the playbook result to render: playbooks[0], else top-level hoisted."""
    playbooks = final_report.get("playbooks") or []
    if playbooks:
        return playbooks[0]
    if "tier" in final_report or "rules" in final_report:
        return final_report
    return None


def build_verdict(final_report: dict[str, Any]) -> Verdict:
    """Normalize a final report into a render-ready Verdict."""
    src = _source(final_report)
    if src is None:
        return Verdict(
            evaluated=False, tier=None, tier_icon=None, score=0,
            total=0, passed=0, failed=0, incomplete=0, worst_level=None,
        )

    rules = list(src.get("rules") or [])
    passed = [r for r in rules if r.get("passed")]
    failed = [
        r for r in rules
        if not r.get("passed") and r.get("status") != "incomplete"
    ]
    incomplete = [r for r in rules if r.get("status") == "incomplete"]

    worst_level = None
    if failed:
        worst_level = min(
            (str(r.get("level") or "info").lower() for r in failed),
            key=lambda lv: _SEVERITY_ORDER.get(lv, 99),
        )

    badges = [
        VerdictBadge(label=b.get("name", ""), klass=b.get("class", ""))
        for b in (src.get("badge_labels") or [])
    ]

    def _line(r: dict[str, Any]) -> RuleLine:
        return RuleLine(
            slug=r.get("slug", "unknown"),
            level=str(r.get("level") or "info").lower(),
            message=r.get("message", ""),
        )

    summary = src.get("rules_summary") or {}
    return Verdict(
        evaluated=True,
        tier=src.get("tier"),
        tier_icon=src.get("tier_icon"),
        score=int(summary.get("score", 0)),
        total=summary.get("total", len(rules)),
        passed=len(passed),
        failed=len(failed),
        incomplete=len(incomplete),
        worst_level=worst_level,
        badges=badges,
        failures=[_line(r) for r in failed],
        incompletes=[_line(r) for r in incomplete],
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pipenv run pytest tests/test_verdict.py -v --no-cov`
Expected: PASS (5 tests)

- [ ] **Step 5: Lint and commit**

```bash
pipenv run ruff format regis/playbook/verdict.py tests/test_verdict.py
pipenv run ruff check regis/playbook/verdict.py tests/test_verdict.py
git add regis/playbook/verdict.py tests/test_verdict.py
git commit -m "feat(playbook): add shared Verdict model and build_verdict"
```

---

## Task 2: Evaluator emits `tier_icon`; schema + default playbook icons

**Files:**

- Modify: `regis/playbook/evaluator.py` (tier-resolution loop, ~lines 224-237)
- Modify: `regis/schemas/playbook/v1alpha1/playbook.schema.json` (tier item properties)
- Modify: `regis/playbooks/default/playbook.yaml` (tiers block)
- Test: `tests/test_tier_icon.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_tier_icon.py`:

```python
import json
from importlib import resources

import jsonschema
import yaml

from regis.playbook.evaluator import evaluate


def _minimal_report():
    return {
        "schemaVersion": 1,
        "version": "0.0.0",
        "request": {"registry": "r", "repository": "x", "tag": "t"},
        "results": {},
    }


def test_evaluator_emits_tier_icon():
    playbook = {
        "name": "p",
        "apiVersion": "regis.io/v1alpha1",
        "tiers": [
            {"name": "Gold", "icon": "🥇",
             "condition": {">": [{"var": "rules_summary.score"}, -1]}},
        ],
        "rules": [],
    }
    result = evaluate(playbook, _minimal_report())
    assert result["tier"] == "Gold"
    assert result["tier_icon"] == "🥇"


def test_evaluator_tier_without_icon_emits_none():
    playbook = {
        "name": "p",
        "apiVersion": "regis.io/v1alpha1",
        "tiers": [
            {"name": "Plain",
             "condition": {">": [{"var": "rules_summary.score"}, -1]}},
        ],
        "rules": [],
    }
    result = evaluate(playbook, _minimal_report())
    assert result["tier"] == "Plain"
    assert result.get("tier_icon") is None


def test_schema_accepts_optional_tier_icon():
    schema_text = (
        resources.files("regis")
        / "schemas" / "playbook" / "v1alpha1" / "playbook.schema.json"
    ).read_text(encoding="utf-8")
    schema = json.loads(schema_text)
    pb = {
        "apiVersion": "regis.io/v1alpha1",
        "kind": "Playbook",
        "metadata": {"name": "t"},
        "spec": {"tiers": [{"name": "Gold", "icon": "🥇",
                            "condition": {">": [{"var": "x"}, 1]}}]},
    }
    jsonschema.validate(pb, schema)  # must not raise


def test_default_playbook_tiers_have_icons():
    pb_text = (
        resources.files("regis") / "playbooks" / "default" / "playbook.yaml"
    ).read_text(encoding="utf-8")
    pb = yaml.safe_load(pb_text)
    tiers = pb["spec"]["tiers"]
    assert [t.get("icon") for t in tiers] == ["🥇", "🥈", "🥉"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pipenv run pytest tests/test_tier_icon.py -v --no-cov`
Expected: FAIL — `test_evaluator_emits_tier_icon` (KeyError/None), `test_schema_accepts_optional_tier_icon` may pass if schema is permissive, `test_default_playbook_tiers_have_icons` FAIL (no icons yet).

- [ ] **Step 3a: Emit `tier_icon` in the evaluator**

In `regis/playbook/evaluator.py`, inside the tier-resolution loop, set the icon when a tier matches. Change:

```python
                    if jsonLogic(condition, full_context):
                        result["tier"] = tier.get("name")
                        break
```

to:

```python
                    if jsonLogic(condition, full_context):
                        result["tier"] = tier.get("name")
                        result["tier_icon"] = tier.get("icon")
                        break
```

- [ ] **Step 3b: Add optional `icon` to the tier schema**

In `regis/schemas/playbook/v1alpha1/playbook.schema.json`, locate the tier item object (the `items` schema under `spec.properties.tiers`). Add `icon` to its `properties` (do NOT add it to `required`):

```json
"icon": { "type": "string", "description": "Optional display icon (emoji) for the tier." }
```

Verify the change is well-formed:

Run: `python -c "import json; json.load(open('regis/schemas/playbook/v1alpha1/playbook.schema.json'))"`
Expected: no output (valid JSON)

- [ ] **Step 3c: Add icons to the default playbook (dogfood)**

In `regis/playbooks/default/playbook.yaml`, add an `icon` line to each tier:

```yaml
tiers:
  - name: Gold
    icon: "🥇"
    condition:
      ">": [var: rules_summary.score, 90]
  - name: Silver
    icon: "🥈"
    condition:
      ">": [var: rules_summary.score, 70]
  - name: Bronze
    icon: "🥉"
    condition:
      ">": [var: rules_summary.score, 50]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pipenv run pytest tests/test_tier_icon.py tests/test_default_playbook_envelope.py tests/test_playbook_schema_v1alpha1.py -v --no-cov`
Expected: PASS (4 new + existing still green)

- [ ] **Step 5: Lint and commit**

```bash
pipenv run ruff format tests/test_tier_icon.py
git add regis/playbook/evaluator.py regis/schemas/playbook/v1alpha1/playbook.schema.json regis/playbooks/default/playbook.yaml tests/test_tier_icon.py
git commit -m "feat(playbook): declarative optional tier icon, emitted as tier_icon"
```

---

## Task 3: Terminal verdict block (replaces `_print_playbook_summary`)

**Files:**

- Modify: `regis/commands/analyze.py` — replace `_print_playbook_summary` with `_render_verdict_block`; update its call site to run by default.
- Test: `tests/test_verdict_terminal.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_verdict_terminal.py`:

```python
import re

from regis.commands.analyze import _render_verdict_block


def _strip_ansi(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def _report():
    return {
        "playbooks": [{
            "tier": "Silver",
            "tier_icon": "🥈",
            "rules_summary": {"score": 78, "total": 20, "passed": 17},
            "rules": [
                {"slug": "cve-critical", "level": "critical", "passed": False,
                 "status": "failed", "message": "1 critical CVE (max 0)"},
                {"slug": "cve-high", "level": "warning", "passed": False,
                 "status": "failed", "message": "12 high CVEs (max 10)"},
                {"slug": "scorecard-min", "level": "warning", "passed": False,
                 "status": "incomplete", "message": "data unavailable"},
                *[{"slug": f"ok-{i}", "level": "info", "passed": True,
                   "status": "passed", "message": ""} for i in range(17)],
            ],
            "badge_labels": [
                {"name": "CVE: Critical", "class": "error"},
                {"name": "CVE: High", "class": "warning"},
            ],
        }]
    }


def test_verdict_block_headline_and_lines(capsys):
    _render_verdict_block(_report(), quiet=False)
    out = _strip_ansi(capsys.readouterr().err)
    assert "🥈 Silver · 78/100" in out
    assert "17/20 règles" in out and "2 échecs" in out and "1 incomplète" in out
    assert "🟥 CVE: Critical" in out and "🟧 CVE: High" in out
    assert "[cve-critical]" in out and "1 critical CVE (max 0)" in out
    assert "[scorecard-min]" in out


def test_verdict_block_quiet_suppresses(capsys):
    _render_verdict_block(_report(), quiet=True)
    assert capsys.readouterr().err == ""


def test_verdict_block_all_pass(capsys):
    report = {"playbooks": [{
        "tier": "Gold", "tier_icon": "🥇",
        "rules_summary": {"score": 100, "total": 2, "passed": 2},
        "rules": [
            {"slug": "a", "level": "info", "passed": True, "status": "passed", "message": ""},
            {"slug": "b", "level": "info", "passed": True, "status": "passed", "message": ""},
        ],
        "badge_labels": [],
    }]}
    _render_verdict_block(report, quiet=False)
    out = _strip_ansi(capsys.readouterr().err)
    assert "🥇 Gold · 100/100" in out
    assert "tout passe ✓" in out


def test_verdict_block_not_evaluated_prints_nothing(capsys):
    _render_verdict_block({"results": {}}, quiet=False)
    assert capsys.readouterr().err == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pipenv run pytest tests/test_verdict_terminal.py -v --no-cov`
Expected: FAIL with `ImportError: cannot import name '_render_verdict_block'`

- [ ] **Step 3a: Add `_render_verdict_block` and delete `_print_playbook_summary`**

In `regis/commands/analyze.py`, remove the whole `_print_playbook_summary` function (lines ~70-118) and add, in its place:

```python
def _render_verdict_block(final_report: dict[str, Any], *, quiet: bool) -> None:
    """Print the evaluation verdict (tier · score, badges, failed rules) to stderr.

    Multi-line block, click-coloured. Suppressed under --quiet. Prints nothing
    when no playbook was evaluated.
    """
    if quiet:
        return

    from regis.playbook.verdict import (
        LEVEL_STYLE,
        badge_emoji,
        build_verdict,
        level_emoji,
        tier_label,
    )

    v = build_verdict(final_report)
    if not v.evaluated:
        return

    # Headline: "🥈 Silver · 78/100"
    headline = f"{tier_label(v.tier, v.tier_icon)} · {v.score}/100"
    click.echo(f"  {click.style(headline, bold=True)}", err=True)

    # Counts line
    counts = f"{v.passed}/{v.total} règles"
    if v.failed == 0 and v.incomplete == 0:
        counts += " · tout passe ✓"
    else:
        if v.failed:
            counts += f" · {v.failed} échec{'s' if v.failed > 1 else ''}"
        if v.incomplete:
            counts += f" · {v.incomplete} incomplète{'s' if v.incomplete > 1 else ''}"
        if v.worst_level:
            counts += f" · pire niveau : {level_emoji(v.worst_level)} {v.worst_level}"
    click.echo(f"  {counts}", err=True)

    # Badges line
    if v.badges:
        chips = "   ".join(f"{badge_emoji(b.klass)} {b.label}" for b in v.badges)
        click.echo(f"  {chips}", err=True)

    # Failed rules
    for f in v.failures:
        colour = LEVEL_STYLE.get(f.level, None)
        line = f"  ✗ [{f.slug}]   {f.message}"
        click.echo(click.style(line, fg=colour) if colour else line, err=True)
    # Incomplete rules
    for i in v.incompletes:
        click.echo(f"  ⚠ [{i.slug}]   {i.message}", err=True)
```

Confirm `from typing import Any` is already imported at the top of `analyze.py` (it is — used elsewhere).

- [ ] **Step 3b: Update the call site to render by default**

Find the call site (around line 642):

```python
    # Only print the summary when the user explicitly requested a playbook —
    # avoids changing stdout for default runs that auto-load the built-in playbook.
    if playbook_paths:
        _print_playbook_summary(final_report)
```

Replace it with:

```python
    # Surface the verdict (tier · score · badges) by default; --quiet suppresses it.
    quiet_flag = bool(ctx.obj.get("quiet")) if (ctx := click.get_current_context(silent=True)) and ctx.obj else False
    _render_verdict_block(final_report, quiet=quiet_flag)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pipenv run pytest tests/test_verdict_terminal.py -v --no-cov`
Expected: PASS (4 tests)

- [ ] **Step 4b: Guard against regressions in the existing CLI tests**

The old behaviour printed a `Playbook · …` line only under `--playbook`. Some `tests/test_cli.py` cases may assert that exact string or assert its absence on default runs.

Run: `pipenv run pytest tests/test_cli.py -v --no-cov`
Expected: PASS. If any test asserts the literal `Playbook ·` summary line or "no summary on default run", update that test to assert the new verdict block (tier · score) instead — the new behaviour is intentional (verdict by default). Note each such change in the commit body.

- [ ] **Step 5: Lint and commit**

```bash
pipenv run ruff format regis/commands/analyze.py tests/test_verdict_terminal.py
pipenv run ruff check regis/commands/analyze.py tests/test_verdict_terminal.py
git add regis/commands/analyze.py tests/test_verdict_terminal.py tests/test_cli.py
git commit -m "feat(analyze): render verdict block (tier, score, badges) by default"
```

---

## Task 4: Markdown verdict header

**Files:**

- Modify: `regis/utils/report.py` — `_render_markdown` (prefix verdict header after the `# {image_ref}` title).
- Test: `tests/test_utils_report.py` (append cases)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_utils_report.py`:

```python
def test_markdown_includes_verdict_header():
    from regis.utils.report import _render_markdown

    report = {
        "request": {"registry": "r", "repository": "x", "tag": "t"},
        "playbooks": [{
            "tier": "Silver", "tier_icon": "🥈",
            "rules_summary": {"score": 78, "total": 20, "passed": 17},
            "rules": [
                {"slug": "cve-critical", "level": "critical", "passed": False,
                 "status": "failed", "message": "1 critical CVE (max 0)"},
                {"slug": "scorecard-min", "level": "warning", "passed": False,
                 "status": "incomplete", "message": "data unavailable"},
                *[{"slug": f"ok-{i}", "level": "info", "passed": True,
                   "status": "passed", "message": ""} for i in range(17)],
            ],
            "badge_labels": [{"name": "CVE: Critical", "class": "error"}],
        }],
    }
    md = _render_markdown(report)
    assert "## 🥈 Silver · 78/100" in md
    assert "🟥 CVE: Critical" in md
    assert "| ✗ | cve-critical | critical | 1 critical CVE (max 0) |" in md
    assert "| ⚠ | scorecard-min | warning | data unavailable |" in md


def test_markdown_no_verdict_when_not_evaluated():
    from regis.utils.report import _render_markdown

    md = _render_markdown({"request": {"registry": "r", "repository": "x", "tag": "t"},
                           "results": {}})
    assert "Unrated" not in md  # no verdict header emitted
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pipenv run pytest tests/test_utils_report.py -k verdict -v --no-cov`
Expected: FAIL (`## 🥈 Silver` not found)

- [ ] **Step 3: Implement the verdict prefix**

In `regis/utils/report.py`, add a module-level helper and call it inside `_render_markdown` right after the title line is built (`lines: list[str] = [f"# {image_ref}", ""]`).

Add the helper above `_render_markdown`:

```python
def _verdict_markdown(report: dict[str, Any]) -> list[str]:
    """Render the verdict header (tier · score, badges, failed rules) as md lines."""
    from regis.playbook.verdict import badge_emoji, build_verdict, tier_label

    v = build_verdict(report)
    if not v.evaluated:
        return []

    lines = [f"## {tier_label(v.tier, v.tier_icon)} · {v.score}/100", ""]

    counts = f"**{v.passed}/{v.total} règles**"
    if v.failed == 0 and v.incomplete == 0:
        counts += " · tout passe ✓"
    else:
        if v.failed:
            counts += f" · {v.failed} échec{'s' if v.failed > 1 else ''}"
        if v.incomplete:
            counts += f" · {v.incomplete} incomplète{'s' if v.incomplete > 1 else ''}"
        if v.worst_level:
            counts += f" · pire niveau : {v.worst_level}"
    lines += [counts, ""]

    if v.badges:
        lines += [" · ".join(f"{badge_emoji(b.klass)} {b.label}" for b in v.badges), ""]

    if v.failures or v.incompletes:
        lines += ["| | Règle | Niveau | Résultat |", "| --- | --- | --- | --- |"]
        for f in v.failures:
            lines.append(f"| ✗ | {f.slug} | {f.level} | {f.message} |")
        for i in v.incompletes:
            lines.append(f"| ⚠ | {i.slug} | {i.level} | {i.message} |")
        lines.append("")

    return lines
```

Then in `_render_markdown`, change:

```python
    lines: list[str] = [f"# {image_ref}", ""]
```

to:

```python
    lines: list[str] = [f"# {image_ref}", ""]
    lines += _verdict_markdown(report)
```

Confirm `from typing import Any` is imported at the top of `regis/utils/report.py` (it is).

- [ ] **Step 4: Run tests to verify they pass**

Run: `pipenv run pytest tests/test_utils_report.py -v --no-cov`
Expected: PASS (new + existing)

- [ ] **Step 5: Lint and commit**

```bash
pipenv run ruff format regis/utils/report.py tests/test_utils_report.py
pipenv run ruff check regis/utils/report.py tests/test_utils_report.py
git add regis/utils/report.py tests/test_utils_report.py
git commit -m "feat(report): prefix markdown output with verdict header"
```

---

## Task 5: HTML verdict panel

**Files:**

- Modify: `regis/report/html.py` — build verdict, pass display fields to the template.
- Modify: `regis/templates/html/report.html.j2` — `.verdict` panel after `</header>`.
- Test: `tests/report/test_html_verdict.py`

- [ ] **Step 1: Write the failing test**

Create `tests/report/test_html_verdict.py`:

```python
from regis.report.html import render_html_single


def _report():
    return {
        "schemaVersion": 1,
        "request": {"registry": "r", "repository": "x", "tag": "t"},
        "results": {},
        "playbooks": [{
            "tier": "Silver", "tier_icon": "🥈",
            "rules_summary": {"score": 78, "total": 20, "passed": 17},
            "rules": [
                {"slug": "cve-critical", "level": "critical", "passed": False,
                 "status": "failed", "message": "1 critical CVE (max 0)"},
                *[{"slug": f"ok-{i}", "level": "info", "passed": True,
                   "status": "passed", "message": ""} for i in range(17)],
            ],
            "badge_labels": [
                {"name": "CVE: Critical", "class": "error"},
                {"name": "SBOM: Present", "class": "success"},
            ],
        }],
    }


def test_html_has_verdict_panel():
    html = render_html_single(_report())
    assert 'class="verdict"' in html
    assert "🥈 Silver · 78/100" in html
    # badge chips reuse the existing CSS badge classes
    assert "badge-failed" in html  # error -> failed
    assert "badge-passed" in html  # success -> passed
    assert "CVE: Critical" in html


def test_html_no_panel_when_not_evaluated():
    html = render_html_single({"schemaVersion": 1,
                               "request": {"registry": "r", "repository": "x", "tag": "t"},
                               "results": {}})
    assert 'class="verdict"' not in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pipenv run pytest tests/report/test_html_verdict.py -v --no-cov`
Expected: FAIL (`class="verdict"` not found)

- [ ] **Step 3a: Pass verdict display fields from `html.py`**

In `regis/report/html.py`, before `return template.render(`, build the verdict view:

```python
    from regis.playbook.verdict import badge_emoji, build_verdict, tier_label

    _v = build_verdict(report)
    _BADGE_CSS = {"error": "failed", "warning": "warning", "success": "passed"}
    verdict_view = None
    if _v.evaluated:
        verdict_view = {
            "headline": f"{tier_label(_v.tier, _v.tier_icon)} · {_v.score}/100",
            "passed": _v.passed,
            "total": _v.total,
            "failed": _v.failed,
            "incomplete": _v.incomplete,
            "worst_level": _v.worst_level,
            "badges": [
                {"label": b.label, "emoji": badge_emoji(b.klass),
                 "css": _BADGE_CSS.get(b.klass, "none")}
                for b in _v.badges
            ],
            "failures": [{"slug": f.slug, "level": f.level, "message": f.message}
                         for f in _v.failures],
            "incompletes": [{"slug": i.slug, "level": i.level, "message": i.message}
                            for i in _v.incompletes],
        }
```

Then add `verdict=verdict_view,` to the `template.render(...)` keyword arguments.

- [ ] **Step 3b: Render the panel in the template**

In `regis/templates/html/report.html.j2`, immediately after the `</header>` line, insert:

```jinja
{% if verdict %}
<section class="verdict">
  <h2 class="verdict-headline">{{ verdict.headline }}</h2>
  <p class="verdict-counts">
    <strong>{{ verdict.passed }}/{{ verdict.total }} rules</strong>
    {% if verdict.failed %} · {{ verdict.failed }} failed{% endif %}
    {% if verdict.incomplete %} · {{ verdict.incomplete }} incomplete{% endif %}
    {% if verdict.worst_level %} · worst: {{ verdict.worst_level }}{% endif %}
    {% if not verdict.failed and not verdict.incomplete %} · all pass ✓{% endif %}
  </p>
  {% if verdict.badges %}
  <p class="verdict-badges">
    {% for b in verdict.badges %}
    <span class="badge badge-{{ b.css }}">{{ b.emoji }} {{ b.label }}</span>
    {% endfor %}
  </p>
  {% endif %}
  {% if verdict.failures or verdict.incompletes %}
  <table class="verdict-rules">
    <tbody>
      {% for f in verdict.failures %}
      <tr><td>✗</td><td>{{ f.slug }}</td><td>{{ f.level }}</td><td>{{ f.message }}</td></tr>
      {% endfor %}
      {% for i in verdict.incompletes %}
      <tr><td>⚠</td><td>{{ i.slug }}</td><td>{{ i.level }}</td><td>{{ i.message }}</td></tr>
      {% endfor %}
    </tbody>
  </table>
  {% endif %}
</section>
{% endif %}
```

Add a small style rule in the `<style>` block (near the other `.badge` rules, ~line 71):

```css
.verdict {
  margin: 1rem 0;
  padding: 0.75rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
}
.verdict-headline {
  margin: 0 0 0.25rem;
  font-size: 1.4rem;
}
.verdict-badges {
  margin: 0.5rem 0 0;
}
.verdict-rules {
  margin-top: 0.5rem;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pipenv run pytest tests/report/test_html_verdict.py -v --no-cov`
Expected: PASS (2 tests)

- [ ] **Step 5: Lint and commit**

```bash
pipenv run ruff format regis/report/html.py tests/report/test_html_verdict.py
pipenv run ruff check regis/report/html.py tests/report/test_html_verdict.py
git add regis/report/html.py regis/templates/html/report.html.j2 tests/report/test_html_verdict.py
git commit -m "feat(report): add verdict panel to single-file HTML report"
```

---

## Task 6: Full-suite verification and documentation

**Files:**

- Modify: `docs/website/docs/reference/cli.md` (analyze output section, if present)
- Test: full suite

- [ ] **Step 1: Run the full test suite with coverage**

Run: `pipenv run pytest`
Expected: PASS, coverage ≥ 90 % (project gate). If `regis/playbook/verdict.py` drags coverage, add the missing-branch cases (e.g. `level_emoji(None)`, unknown badge class) to `tests/test_verdict.py`.

- [ ] **Step 2: Manual smoke check of the three surfaces**

Run (any public image):

```bash
pipenv run regis analyze docker.io/library/alpine:3.20 --html --markdown -o report
```

Expected: terminal shows the verdict block (tier · score, badges, any failed rules); `report.html` contains a `.verdict` panel; `report.md` opens with a `## <tier> · <score>/100` header. Confirm `-q` suppresses the terminal block:

```bash
pipenv run regis analyze docker.io/library/alpine:3.20 -q
```

Expected: no verdict block on stderr.

- [ ] **Step 3: Update CLI reference docs**

In `docs/website/docs/reference/cli.md`, find the `regis analyze` section. Add a short subsection documenting the verdict block (shown by default, suppressed by `-q`), the tier `icon` field, and the markdown/HTML verdict header. Keep it to a few sentences with one example block matching the terminal mock from the spec.

- [ ] **Step 4: Run lint + format across touched files**

```bash
pipenv run ruff format .
pipenv run ruff check .
trunk check --fix
```

Expected: clean (or only auto-fixed formatting, which you then stage).

- [ ] **Step 5: Commit docs**

```bash
git add docs/website/docs/reference/cli.md
git commit -m "docs(reference): document the analyze verdict output"
```

---

## Self-Review notes (addressed)

- **Spec coverage:** terminal/HTML/markdown renderers (Tasks 3/4/5), shared `Verdict` model + mappings (Task 1), declarative tier `icon` + `tier_icon` emission + default-playbook dogfood (Task 2), default-by-default behaviour + `-q` (Task 3 call site), edge cases (no-tier → `⚪ Unrated`, no-icon → `🏷️`, incomplete rows, not-evaluated → no block) all covered by tests. Score model untouched (spec: display only). `presentation.badges` orphan slugs handled by consuming pre-resolved `badge_labels` (already filtered/ordered), so no playbook fix needed here.
- **Type consistency:** `build_verdict`, `Verdict`, `VerdictBadge`, `RuleLine`, `tier_label`, `badge_emoji`, `level_emoji`, `LEVEL_STYLE`, `CLASS_EMOJI`, `LEVEL_EMOJI` names are identical across Tasks 1/3/4/5. Badge source is `badge_labels` (`{name, class}`) everywhere. Rule dict keys (`slug/level/passed/status/message`) match the evaluator output documented in Background.
- **Severity colour caveat:** click has no orange — `warning` rule text uses `yellow`; the orange square emoji 🟧 carries the disambiguation (documented in `verdict.py`).
