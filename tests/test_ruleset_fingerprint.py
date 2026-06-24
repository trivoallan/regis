"""Unit tests for the resolved-ruleset fingerprint."""

from regis.core.domain.rules.fingerprint import ruleset_fingerprint


def _rule(slug, level="critical", condition=None, **extra):
    return {
        "slug": slug,
        "level": level,
        "condition": condition if condition is not None else {">": [{"var": "x"}, 0]},
        **extra,
    }


def test_deterministic():
    rules = [_rule("a"), _rule("b")]
    assert ruleset_fingerprint(rules) == ruleset_fingerprint(rules)


def test_order_independent():
    a, b = _rule("a"), _rule("b")
    assert ruleset_fingerprint([a, b]) == ruleset_fingerprint([b, a])


def test_threshold_change_changes_hash():
    # The core guarantee: loosening a threshold inside the condition changes the hash.
    loose = ruleset_fingerprint([_rule("cve", condition={"<=": [{"var": "n"}, 9999]})])
    strict = ruleset_fingerprint([_rule("cve", condition={"<=": [{"var": "n"}, 0]})])
    assert loose != strict


def test_severity_change_changes_hash():
    crit = ruleset_fingerprint([_rule("a", level="critical")])
    info = ruleset_fingerprint([_rule("a", level="info")])
    assert crit != info


def test_cosmetic_change_is_stable():
    bare = ruleset_fingerprint([_rule("a")])
    decorated = ruleset_fingerprint(
        [_rule("a", description="x", message="y", tags=["t"])]
    )
    assert bare == decorated


def test_format_is_prefixed_sha256():
    h = ruleset_fingerprint([_rule("a")])
    assert h.startswith("sha256:")
    assert len(h) == len("sha256:") + 64
