"""Unit tests for the shared ``--fail`` breach helper.

Pins the unified semantics that the analyze use-case and the analyze / rules
evaluate CLI commands now share (they had drifted on ``none``/unknown).
"""

import pytest

from regis.core.domain.rules.breach import breached_slugs

_RULES = [
    {"slug": "crit", "level": "critical", "passed": False},
    {"slug": "warn", "level": "warning", "passed": False},
    {"slug": "info", "level": "info", "passed": False},
    {"slug": "ok", "level": "critical", "passed": True},  # passing -> never a breach
]


@pytest.mark.parametrize(
    "fail_level, expected",
    [
        ("critical", ["crit"]),
        ("warning", ["crit", "warn"]),
        ("info", ["crit", "warn", "info"]),
        ("CRITICAL", ["crit"]),  # case-insensitive
        ("none", []),  # "never fail"
        ("", []),  # unknown -> never fail
        ("bogus", []),  # unknown -> never fail (NOT "fail as critical")
    ],
)
def test_threshold_is_at_or_above_and_excludes_passing(fail_level, expected):
    assert breached_slugs(_RULES, fail_level) == expected


def test_unlabelled_rule_level_is_treated_as_info():
    # An unlabelled non-passing rule is least-severe (info): it breaches only at
    # fail_level=info, never at warning/critical.
    rules = [{"slug": "bare", "passed": False}]
    assert breached_slugs(rules, "info") == ["bare"]
    assert breached_slugs(rules, "warning") == []
    assert breached_slugs(rules, "critical") == []


def test_missing_slug_falls_back_to_unknown():
    assert breached_slugs([{"level": "critical", "passed": False}], "critical") == [
        "unknown"
    ]


def test_empty_rules_never_breaches():
    assert breached_slugs([], "info") == []
