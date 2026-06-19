from regis.adapters.driven.report.html import render_html_single


def _report():
    return {
        "schemaVersion": 1,
        "request": {"registry": "r", "repository": "x", "tag": "t"},
        "results": {},
        "playbooks": [
            {
                "tier": "Silver",
                "tier_icon": "🥈",
                "rules_summary": {"score": 78, "total": 20, "passed": 17},
                "rules": [
                    {
                        "slug": "cve-critical",
                        "level": "critical",
                        "passed": False,
                        "status": "failed",
                        "message": "1 critical CVE (max 0)",
                    },
                    *[
                        {
                            "slug": f"ok-{i}",
                            "level": "info",
                            "passed": True,
                            "status": "passed",
                            "message": "",
                        }
                        for i in range(17)
                    ],
                ],
                "badge_labels": [
                    {"name": "CVE: Critical", "class": "error"},
                    {"name": "SBOM: Present", "class": "success"},
                ],
            }
        ],
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
    html = render_html_single(
        {
            "schemaVersion": 1,
            "request": {"registry": "r", "repository": "x", "tag": "t"},
            "results": {},
        }
    )
    assert 'class="verdict"' not in html


def test_html_all_pass_branch_and_panel_ordering():
    report = {
        "schemaVersion": 1,
        "request": {"registry": "r", "repository": "x", "tag": "t"},
        "results": {},
        "playbooks": [
            {
                "tier": "Gold",
                "tier_icon": "🥇",
                "rules_summary": {"score": 100, "total": 1, "passed": 1},
                "rules": [
                    {
                        "slug": "ok",
                        "level": "info",
                        "passed": True,
                        "status": "passed",
                        "message": "",
                    },
                ],
                "badge_labels": [],
            }
        ],
    }
    html = render_html_single(report)
    assert "🥇 Gold · 100/100" in html
    assert "all pass ✓" in html
    # The verdict panel renders above the existing playbook-results section.
    assert html.index('class="verdict"') < html.index('id="playbooks"')
