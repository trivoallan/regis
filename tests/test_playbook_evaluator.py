"""Coverage for regis/playbook/evaluator.py branches."""

from __future__ import annotations

from regis.playbook.evaluator import (
    _resolve_links,
    evaluate,
)

# ---------------------------------------------------------------------------
# evaluate — score derives from rules
# ---------------------------------------------------------------------------


def test_score_derives_from_rules():
    """result['score'] mirrors the rules score (no scorecard subsystem)."""
    pb = {
        "name": "x",
        "rules": [
            {"slug": "a", "provider": "core", "rule": "always-true", "level": "info"},
        ],
    }
    out = evaluate(pb, {})
    assert out["score"] == out["rules_summary"]["score"]
    # No scorecard-era keys remain on the result.
    assert "pages" not in out
    assert "total_scorecards" not in out
    assert "passed_scorecards" not in out


# ---------------------------------------------------------------------------
# _resolve_links
# ---------------------------------------------------------------------------


def test_resolve_links_format_from_report():
    """URL with {key} placeholders is formatted from the report dict."""
    playbook = {"links": [{"label": "Repo", "url": "https://github.com/{repo}"}]}
    result: dict = {}
    _resolve_links(playbook, result, {}, {"repo": "acme/regis"})
    assert result["links"] == [
        {"label": "Repo", "url": "https://github.com/acme/regis"}
    ]


def test_resolve_links_missing_key_skipped():
    """URL referencing a missing key triggers exception → link is skipped."""
    playbook = {
        "links": [{"label": "Missing", "url": "https://example.com/{no_such_key}"}]
    }
    result: dict = {}
    _resolve_links(playbook, result, {}, {})
    assert "links" not in result


def test_resolve_links_condition_false_skipped():
    """Link with a False condition is not included."""
    playbook = {
        "links": [
            {"label": "Nope", "url": "https://x.com", "condition": {"==": [1, 0]}}
        ]
    }
    result: dict = {}
    _resolve_links(playbook, result, {}, {})
    assert "links" not in result


def test_resolve_links_condition_exception_skipped():
    """Link whose condition raises is skipped."""
    playbook = {
        "links": [
            {
                "label": "Bad",
                "url": "https://x.com",
                "condition": {"__bad_op__": [1, 2]},
            }
        ]
    }
    result: dict = {}
    _resolve_links(playbook, result, {}, {})
    assert "links" not in result


# ---------------------------------------------------------------------------
# evaluate — tier / badge / label branches
# ---------------------------------------------------------------------------


def test_badge_without_value_uses_scope_as_label():
    """Badge with no value gets label == scope."""
    out = evaluate({"name": "x", "badges": [{"slug": "s", "scope": "Status"}]}, {})
    badge = out["badges"][0]
    assert badge["label"] == "Status"
    assert badge["value"] is None


def test_badge_value_interpolation():
    """${var} in badge value is interpolated from the full context."""
    pb = {
        "name": "x",
        "badges": [{"slug": "v", "scope": "Version", "value": "${version}"}],
    }
    out = evaluate(pb, {"version": "1.2.3"})
    assert out["badges"][0]["value"] == "1.2.3"
    assert out["badges"][0]["label"] == "Version: 1.2.3"


def test_badge_condition_exception_is_skipped():
    """Badge whose condition raises is omitted from results."""
    pb = {
        "name": "x",
        "badges": [
            {
                "slug": "bad",
                "scope": "T",
                "value": "X",
                "condition": {"__bad_op__": [1, 2]},
            },
        ],
    }
    out = evaluate(pb, {})
    assert all(b["slug"] != "bad" for b in out.get("badges", []))


def test_badge_condition_false_is_skipped():
    """Badge whose condition is False is omitted."""
    pb = {
        "name": "x",
        "badges": [
            {"slug": "hidden", "scope": "T", "value": "X", "condition": {"==": [1, 0]}},
        ],
    }
    out = evaluate(pb, {})
    assert all(b["slug"] != "hidden" for b in out.get("badges", []))


def test_tier_condition_exception_does_not_crash():
    """A tier whose condition raises should be silently skipped without crashing."""
    pb = {
        "name": "x",
        "tiers": [
            {"name": "Gold", "condition": {"__bad_op__": [1, 2]}},
        ],
    }
    out = evaluate(pb, {})
    assert "tier" not in out


def test_tier_condition_matched():
    """A tier whose condition is True is set in the result."""
    pb = {
        "name": "x",
        "tiers": [
            {"name": "Gold", "icon": "star", "condition": {"==": [1, 1]}},
        ],
    }
    out = evaluate(pb, {})
    assert out["tier"] == "Gold"
    assert out["tier_icon"] == "star"


# ---------------------------------------------------------------------------
# _resolve_links — edge cases (lines 123, 142, 146)
# ---------------------------------------------------------------------------


def test_resolve_links_non_dict_link_skipped():
    """Non-dict items in links list are silently skipped (line 123)."""
    playbook = {"links": ["not-a-dict", {"label": "OK", "url": "https://x.com"}]}
    result: dict = {}
    _resolve_links(playbook, result, {}, {})
    assert result["links"] == [{"label": "OK", "url": "https://x.com"}]


def test_resolve_links_non_string_url_skipped():
    """Link with a non-string url is skipped (line 142)."""
    playbook = {"links": [{"label": "No URL"}, {"label": "OK", "url": "https://y.com"}]}
    result: dict = {}
    _resolve_links(playbook, result, {}, {})
    assert result["links"] == [{"label": "OK", "url": "https://y.com"}]


def test_resolve_links_jinja2_template_url():
    """URL containing {{ }} is resolved via _resolve_template (line 146)."""
    playbook = {"links": [{"label": "Tmpl", "url": "https://x.com/{{ repo }}"}]}
    result: dict = {}
    full_context = {"repo": "acme/regis"}
    _resolve_links(playbook, result, full_context, {})
    assert "links" in result
    assert "acme/regis" in result["links"][0]["url"]


# ---------------------------------------------------------------------------
# evaluate — sidebar and source_name (lines 294, 300)
# ---------------------------------------------------------------------------


def test_evaluate_sidebar_passed_through():
    """Playbook with a sidebar dict attaches it to the result (line 294)."""
    pb = {"name": "x", "sidebar": {"items": ["Foo", "Bar"]}}
    out = evaluate(pb, {})
    assert out["sidebar"] == {"items": ["Foo", "Bar"]}


def test_evaluate_source_name_set():
    """source_name parameter populates _meta in the result (line 300)."""
    out = evaluate({"name": "x"}, {}, source_name="my-playbook.yaml")
    assert out["_meta"] == {"source_name": "my-playbook.yaml"}
