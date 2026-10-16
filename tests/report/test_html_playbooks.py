"""The "Playbook results" table reads the keys the playbook evaluator emits."""

from regis.adapters.driven.report.html import render_html_single


def _report(playbooks: list[dict]) -> dict:
    return {
        "request": {"registry": "r", "repository": "app", "tag": "1"},
        "results": {},
        "playbooks": playbooks,
    }


def _table(html: str) -> str:
    start = html.index('<section id="playbooks">')
    return html[start : html.index("</section>", start)]


def test_shows_playbook_name_version_and_tier() -> None:
    html = render_html_single(
        _report(
            [
                {
                    "playbook_name": "pilot-sncf",
                    "playbook_version": "1.2.0",
                    "tier": "quarantine",
                    "tier_icon": "🚫",
                    "score": 40,
                    "rules": [{"passed": False}, {"passed": True}],
                }
            ]
        )
    )
    table = _table(html)
    assert "pilot-sncf" in table
    assert "1.2.0" in table
    assert "quarantine" in table
    assert "—" not in table


def test_counts_failed_rules_not_incomplete() -> None:
    html = render_html_single(
        _report(
            [
                {
                    "playbook_name": "p",
                    "tier": "gold",
                    "score": 50,
                    "rules": [
                        {"passed": False, "status": "failed"},
                        {"passed": False, "status": "failed"},
                        {"passed": False, "status": "incomplete"},
                        {"passed": True, "status": "passed"},
                    ],
                }
            ]
        )
    )
    assert "<td>2</td>" in _table(html)


def test_dash_only_when_playbook_has_no_tier() -> None:
    html = render_html_single(
        _report([{"playbook_name": "p", "score": 0, "rules": []}])
    )
    table = _table(html)
    assert "p" in table
    assert "—" in table
