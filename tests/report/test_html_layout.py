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


def test_renders_without_verdict_or_triage():
    # A report with no tier/rules/playbooks is "not evaluated": the verdict
    # hero and triage panel are skipped, but the page still renders.
    html = render_html_single(
        {
            "request": {"registry": "r", "repository": "library/nginx", "tag": "1.27"},
            "results": {"oci": {"analyzer": "oci"}},
        }
    )
    assert 'id="verdict"' not in html
    assert 'id="triage"' not in html
    assert 'id="oci"' in html  # analyzer section still rendered
