from regis.playbook.verdict import (
    VerdictBadge,
    badge_emoji,
    build_verdict,
    tier_label,
)


def _report(**pb):
    return {"playbooks": [pb]}


def test_build_verdict_from_playbooks_zero():
    report = _report(
        tier="Silver",
        tier_icon="🥈",
        rules_summary={"score": 78, "total": 20, "passed": 17},
        rules=[
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
    v = build_verdict(
        _report(
            rules_summary={"score": 42, "total": 1, "passed": 0},
            rules=[],
            badge_labels=[],
        )
    )
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


def test_worst_level_warning_when_no_critical():
    # Locks the severity ordering: with no critical failure, worst is warning.
    v = build_verdict(
        _report(
            rules_summary={"score": 80, "total": 2, "passed": 1},
            rules=[
                {
                    "slug": "info-rule",
                    "level": "info",
                    "passed": False,
                    "status": "failed",
                    "message": "minor",
                },
                {
                    "slug": "warn-rule",
                    "level": "warning",
                    "passed": False,
                    "status": "failed",
                    "message": "watch out",
                },
            ],
            badge_labels=[],
        )
    )
    assert v.worst_level == "warning"


def test_build_verdict_from_top_level_hoisted_fields():
    # No `playbooks` key: build_verdict falls back to top-level hoisted fields
    # (the `--evaluate`/rerun shape).
    report = {
        "tier": "Gold",
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
    v = build_verdict(report)
    assert v.evaluated is True
    assert v.tier == "Gold"
    assert v.tier_icon is None
    assert (v.passed, v.failed, v.incomplete) == (1, 0, 0)
