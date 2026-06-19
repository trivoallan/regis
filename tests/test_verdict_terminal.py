import re

from regis.adapters.driving.cli.commands.analyze import _render_verdict_block


def _strip_ansi(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def _report():
    return {
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
                    {
                        "slug": "cve-high",
                        "level": "warning",
                        "passed": False,
                        "status": "failed",
                        "message": "12 high CVEs (max 10)",
                    },
                    {
                        "slug": "scorecard-min",
                        "level": "warning",
                        "passed": False,
                        "status": "incomplete",
                        "message": "data unavailable",
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
                    {"name": "CVE: High", "class": "warning"},
                ],
            }
        ]
    }


def test_verdict_block_headline_and_lines(capsys):
    _render_verdict_block(_report(), quiet=False)
    out = _strip_ansi(capsys.readouterr().err)
    assert "🥈 Silver · 78/100" in out
    assert "17/20 rules" in out and "2 failed" in out and "1 incomplete" in out
    assert "worst: 🟥 critical" in out
    assert "🟥 CVE: Critical" in out and "🟧 CVE: High" in out
    assert "[cve-critical]" in out and "1 critical CVE (max 0)" in out
    assert "[scorecard-min]" in out


def test_verdict_block_quiet_suppresses(capsys):
    _render_verdict_block(_report(), quiet=True)
    assert capsys.readouterr().err == ""


def test_verdict_block_all_pass(capsys):
    report = {
        "playbooks": [
            {
                "tier": "Gold",
                "tier_icon": "🥇",
                "rules_summary": {"score": 100, "total": 2, "passed": 2},
                "rules": [
                    {
                        "slug": "a",
                        "level": "info",
                        "passed": True,
                        "status": "passed",
                        "message": "",
                    },
                    {
                        "slug": "b",
                        "level": "info",
                        "passed": True,
                        "status": "passed",
                        "message": "",
                    },
                ],
                "badge_labels": [],
            }
        ]
    }
    _render_verdict_block(report, quiet=False)
    out = _strip_ansi(capsys.readouterr().err)
    assert "🥇 Gold · 100/100" in out
    assert "all pass ✓" in out


def test_verdict_block_not_evaluated_prints_nothing(capsys):
    _render_verdict_block({"results": {}}, quiet=False)
    assert capsys.readouterr().err == ""
