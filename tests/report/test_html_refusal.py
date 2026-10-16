"""A refusal explains itself: the five-field grid of the refusal-report spec.

For each failed rule: rule, observed fact, threshold, playbook, ruleset_hash.
For each incomplete rule: a distinct label and the missing keys.
"""

from regis.adapters.driven.report.html import render_html_single

_HASH = "sha256:25cc16106e1395387c0596a67e3000c0f7aeb88e56df6adc42e990b4bedf59ad"


def _report(rules: list[dict]) -> dict:
    return {
        "schemaVersion": 6,
        "request": {"registry": "r", "repository": "app", "tag": "1"},
        "results": {"cve": {}},
        "playbooks": [
            {
                "playbook_name": "pilot-sncf",
                "playbook_version": "1.0.0",
                "ruleset_hash": _HASH,
                "tier": "quarantine",
                "score": 0,
                "rules": rules,
                "rules_summary": {"score": 0, "total": len(rules)},
            }
        ],
    }


_FAILED = {
    "slug": "cve-fixable",
    "description": "All vulnerabilities should be fixed if a patch exists.",
    "level": "warning",
    "passed": False,
    "status": "failed",
    "message": "Image has 5 vulnerabilities with available fixes.",
    "analyzers": ["cve"],
    "observed": {"results.cve.fixed_count": 5},
    "threshold": {"max_count": 0},
    "missing_keys": [],
}

_INCOMPLETE = {
    "slug": "no-licence-toxique",
    "description": "No blocklisted license.",
    "level": "critical",
    "passed": False,
    "status": "incomplete",
    "message": "Image includes blocklisted licenses.",
    "analyzers": ["sbom"],
    "observed": {},
    "threshold": {"blocklist": ["GPL-3.0-only", "SSPL-1.0"]},
    "missing_keys": ["results.sbom"],
}


def _row(html: str, css: str) -> str:
    start = html.index(f'<tr class="{css}">')
    return html[start : html.index("</tr>", start)]


def _triage(html: str) -> str:
    start = html.index('<section id="triage"')
    return html[start : html.index("</section>", start)]


def test_failed_rule_shows_the_five_fields() -> None:
    html = render_html_single(_report([_FAILED]))
    row = _row(html, "rule-failed")
    triage = _triage(html)
    assert "cve-fixable" in row  # rule
    assert "All vulnerabilities should be fixed" in row  # rule description
    assert "results.cve.fixed_count" in row and "<strong>5</strong>" in row  # fact
    assert "max_count" in row and "<strong>0</strong>" in row  # threshold
    assert "pilot-sncf" in triage and "1.0.0" in triage  # playbook
    assert _HASH in triage  # ruleset_hash


def test_incomplete_rule_has_own_label_and_missing_keys() -> None:
    html = render_html_single(_report([_INCOMPLETE]))
    row = _row(html, "rule-incomplete")
    assert "Not evaluated" in row
    assert "results.sbom" in row
    assert "GPL-3.0-only, SSPL-1.0" in row  # threshold still shown
    # the failure message is not the explanation of an incomplete rule
    assert "Image includes blocklisted licenses." not in row


def test_rule_without_threshold_shows_dash() -> None:
    rule = {**_FAILED, "slug": "no-latest", "threshold": {}}
    row = _row(render_html_single(_report([rule])), "rule-failed")
    assert '<span class="muted">—</span>' in row


def test_values_are_escaped() -> None:
    rule = {**_FAILED, "observed": {"request.tag": "<script>x</script>"}}
    row = _row(render_html_single(_report([rule])), "rule-failed")
    assert "<script>x</script>" not in row
