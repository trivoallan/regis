"""Coverage for regis/playbook/sections.py branches.

Targets the following uncovered lines (as of initial measurement):
  33-47   _evaluate_scorecards: _pre_evaluated fast-path
  57-64   _evaluate_scorecards: exception branch (bad condition)
  154-168 _evaluate_widgets: condition evaluation error
  180     _evaluate_widgets: options.subvalue resolution
  187     _evaluate_widgets: url template resolution
  217     _build_render_order: tags_summary exists but scorecards not in render_order
  237-265 _evaluate_section: rules list slug resolution (found & not found)
  290     _evaluate_section: hint preserved
  292     _evaluate_section: condition preserved
  328-332 resolve_widgets_final: section condition False → section dropped
  338-342 resolve_widgets_final: widget condition False → widget dropped
  365     resolve_widgets_final: subvalue re-resolution
  377     resolve_widgets_final: url re-resolution
"""

from __future__ import annotations

import pytest

from regis.playbook.sections import (
    _build_render_order,
    _evaluate_scorecards,
    _evaluate_section,
    _evaluate_widgets,
    resolve_widgets_final,
)


# ---------------------------------------------------------------------------
# _evaluate_scorecards
# ---------------------------------------------------------------------------


def test_pre_evaluated_scorecard_is_passed_through():
    """Lines 33-47: _pre_evaluated branch copies _rule_result fields."""
    defs = [
        {
            "_pre_evaluated": True,
            "_rule_result": {
                "slug": "r1",
                "description": "Rule one",
                "level": "bronze",
                "tags": ["security"],
                "analyzers": ["cve"],
                "passed": True,
                "status": "passed",
                "message": "all good",
            },
        }
    ]
    out = _evaluate_scorecards(defs, {})
    assert len(out) == 1
    sc = out[0]
    assert sc["name"] == "r1"
    assert sc["description"] == "Rule one"
    assert sc["title"] == "Rule one"
    assert sc["level"] == "bronze"
    assert sc["tags"] == ["security"]
    assert sc["analyzers"] == ["cve"]
    assert sc["passed"] is True
    assert sc["status"] == "passed"
    assert sc["message"] == "all good"


def test_pre_evaluated_scorecard_uses_slug_as_description_fallback():
    """Lines 33-47: when description absent, slug is used as description/title."""
    defs = [
        {
            "_pre_evaluated": True,
            "_rule_result": {
                "slug": "no-desc",
                "description": None,
                "level": "silver",
                "tags": [],
                "analyzers": [],
                "passed": False,
                "status": "failed",
                "message": "fail",
            },
        }
    ]
    out = _evaluate_scorecards(defs, {})
    assert out[0]["description"] == "no-desc"
    assert out[0]["title"] == "no-desc"


def test_scorecard_condition_exception_marks_incomplete():
    """Lines 57-64: an invalid condition raises → passed=False, status=incomplete."""
    # Use a badly-typed condition that json_logic cannot evaluate without error.
    # Passing a non-iterable as an operator key works reliably.
    defs = [
        {
            "name": "bad-rule",
            "level": "bronze",
            "tags": [],
            # "==" expects a list; passing an int triggers an error inside jsonLogic
            "condition": {"==": 42},
        }
    ]
    out = _evaluate_scorecards(defs, {})
    assert len(out) == 1
    assert out[0]["passed"] is False
    assert out[0]["status"] == "incomplete"


# ---------------------------------------------------------------------------
# _evaluate_widgets
# ---------------------------------------------------------------------------


def test_evaluate_widgets_subvalue_resolved():
    """Line 180: options.subvalue path is resolved into resolved_subvalue."""
    raw_context = {"score": 80}
    widgets = [{"label": "w", "options": {"subvalue": "score"}}]
    out = _evaluate_widgets(widgets, raw_context, None)
    assert len(out) == 1
    assert out[0]["resolved_subvalue"] == 80


def test_evaluate_widgets_url_template_resolved():
    """Line 187: url template is resolved into resolved_url."""
    raw_context = {"image": "nginx:1.25"}
    widgets = [{"label": "w", "url": "https://example.com/{{ image }}"}]
    out = _evaluate_widgets(widgets, raw_context, {"image": "nginx:1.25"})
    assert len(out) == 1
    assert out[0]["resolved_url"] == "https://example.com/nginx:1.25"


def test_evaluate_widgets_condition_error_with_missing_data_keeps_widget():
    """Lines 154-168: condition raises AND missing data → widget is kept (not dropped).

    We mock MissingDataTracker to force missing_accessed=True so that the except branch
    (line 166-168) takes the "keep" path rather than ``continue``.
    """
    from unittest.mock import patch, MagicMock

    mock_tracker = MagicMock()
    mock_tracker.missing_accessed = True  # simulate prior missing access
    mock_tracker.accessed_keys = set()

    with patch(
        "regis.playbook.sections.MissingDataTracker", return_value=mock_tracker
    ):
        # Use an invalid operator so jsonLogic raises
        widgets = [{"label": "w", "condition": {"$INVALID$": []}}]
        out = _evaluate_widgets(widgets, {"x": 1}, None)

    # Widget must be kept because missing_accessed was True when exception occurred
    assert len(out) == 1
    assert out[0]["label"] == "w"


def test_evaluate_widgets_condition_false_no_missing_drops_widget():
    """Lines 155-160: condition evaluates to False with no missing data → widget dropped."""
    raw_context = {"x": 0}
    widgets = [
        {"label": "drop", "condition": {"==": [{"var": "x"}, 1]}},
        {"label": "keep", "condition": {"==": [{"var": "x"}, 0]}},
    ]
    out = _evaluate_widgets(widgets, raw_context, None)
    assert len(out) == 1
    assert out[0]["label"] == "keep"


def test_evaluate_widgets_condition_error_no_missing_drops_widget():
    """Lines 161-168: condition raises AND missing_accessed is False → widget dropped."""
    # An invalid operator that raises without triggering key access.
    # We pre-populate all keys the condition might touch; the bad op raises before any lookup.
    raw_context = {"x": 1}
    # {"bad_op": [1, 2]} will raise "Unrecognised operation" immediately, before any
    # key lookup, so missing_accessed stays False → widget is dropped.
    widgets = [{"label": "w", "condition": {"$INVALID_OP$": [1, 2]}}]
    out = _evaluate_widgets(widgets, raw_context, None)
    assert len(out) == 0


# ---------------------------------------------------------------------------
# _build_render_order
# ---------------------------------------------------------------------------


def test_build_render_order_tags_appended_when_no_scorecards_key():
    """Line 217: tags_summary present but 'scorecards' not in render_order → tags appended."""
    # A section with widgets only → 'scorecards' is not in render_order
    section = {"widgets": []}
    tags_summary = {"security": {"total": 1, "passed": 1, "percentage": 100}}
    order = _build_render_order(section, tags_summary)
    assert "tags" in order
    assert "scorecards" not in order


# ---------------------------------------------------------------------------
# _evaluate_section — rules list, hint, condition
# ---------------------------------------------------------------------------


def _make_rule(slug: str, passed: bool = True) -> dict:
    return {
        "slug": slug,
        "description": f"Rule {slug}",
        "level": "bronze",
        "tags": ["sec"],
        "analyzers": [],
        "passed": passed,
        "status": "passed" if passed else "failed",
        "message": "",
    }


def test_section_rule_reference_found_by_exact_slug():
    """Lines 237-263: rule slug found in rules registry → appended as pre-evaluated scorecard."""
    rule = _make_rule("my-rule")
    ctx = {"rules": {"my-rule": rule}}
    section = {"name": "S", "rules": ["my-rule"]}
    out = _evaluate_section(section, ctx)
    assert any(sc["name"] == "my-rule" for sc in out["scorecards"])


def test_section_rule_reference_found_by_dotted_slug():
    """Lines 237-263: 'provider.slug' format — slug part used for lookup."""
    rule = _make_rule("my-rule")
    ctx = {"rules": {"my-rule": rule}}
    section = {"name": "S", "rules": ["provider.my-rule"]}
    out = _evaluate_section(section, ctx)
    assert any(sc["name"] == "my-rule" for sc in out["scorecards"])


def test_section_rule_reference_not_found_logs_warning(caplog):
    """Lines 264-269: rule not found → warning logged, no scorecard added."""
    import logging

    ctx = {"rules": {}}
    section = {"name": "S", "rules": ["missing-rule"]}
    with caplog.at_level(logging.WARNING, logger="regis.playbook.sections"):
        out = _evaluate_section(section, ctx)
    assert out["scorecards"] == []
    assert "missing-rule" in caplog.text


def test_section_rule_reference_non_string_skipped():
    """Lines 239-241: non-string entries in rules list are silently skipped."""
    ctx = {"rules": {}}
    section = {"name": "S", "rules": [42, None]}
    out = _evaluate_section(section, ctx)
    assert out["scorecards"] == []


def test_section_hint_preserved():
    """Line 290: hint key from section dict is propagated to result."""
    out = _evaluate_section({"name": "S", "hint": "read the docs", "scorecards": []}, {})
    assert out["hint"] == "read the docs"


def test_section_condition_preserved():
    """Line 292: condition key from section dict is propagated to result."""
    cond = {"==": [1, 1]}
    out = _evaluate_section({"name": "S", "condition": cond, "scorecards": []}, {})
    assert out["condition"] == cond


def test_section_without_hint_has_no_hint_key():
    """Negative: when no hint provided, result must not contain the hint key."""
    out = _evaluate_section({"name": "S", "scorecards": []}, {})
    assert "hint" not in out


# ---------------------------------------------------------------------------
# resolve_widgets_final
# ---------------------------------------------------------------------------


def test_resolve_widgets_final_drops_section_with_false_condition():
    """Lines 328-332: section whose condition evaluates to False is removed."""
    pages = [
        {
            "sections": [
                {
                    "name": "keep",
                    "condition": {"==": [1, 1]},
                    "widgets": [],
                },
                {
                    "name": "drop",
                    "condition": {"==": [1, 0]},
                    "widgets": [],
                },
            ]
        }
    ]
    resolve_widgets_final(pages, {})
    names = [s["name"] for s in pages[0]["sections"]]
    assert names == ["keep"]


def test_resolve_widgets_final_drops_section_with_exception_condition():
    """Lines 328-332: section whose condition raises is also removed."""
    pages = [
        {
            "sections": [
                {"name": "bad", "condition": {"$INVALID$": []}, "widgets": []},
                {"name": "good", "widgets": []},
            ]
        }
    ]
    resolve_widgets_final(pages, {})
    names = [s["name"] for s in pages[0]["sections"]]
    assert names == ["good"]


def test_resolve_widgets_final_drops_widget_with_false_condition():
    """Lines 338-342: widget whose condition evaluates to False is removed."""
    pages = [
        {
            "sections": [
                {
                    "widgets": [
                        {"label": "keep", "condition": {"==": [1, 1]}},
                        {"label": "drop", "condition": {"==": [1, 0]}},
                    ]
                }
            ]
        }
    ]
    resolve_widgets_final(pages, {})
    labels = [w["label"] for w in pages[0]["sections"][0]["widgets"]]
    assert labels == ["keep"]


def test_resolve_widgets_final_drops_widget_with_exception_condition():
    """Lines 338-342: widget whose condition raises is also removed."""
    pages = [
        {
            "sections": [
                {
                    "widgets": [
                        {"label": "bad", "condition": {"$INVALID$": []}},
                        {"label": "good"},
                    ]
                }
            ]
        }
    ]
    resolve_widgets_final(pages, {})
    labels = [w["label"] for w in pages[0]["sections"][0]["widgets"]]
    assert labels == ["good"]


def test_resolve_widgets_final_re_resolves_subvalue_when_none():
    """Line 365: resolved_subvalue is None → re-resolved from full_context."""
    full_ctx = {"score": 42}
    pages = [
        {
            "sections": [
                {
                    "widgets": [
                        {
                            "label": "w",
                            "options": {"subvalue": "score"},
                            "resolved_subvalue": None,
                        }
                    ]
                }
            ]
        }
    ]
    resolve_widgets_final(pages, full_ctx)
    widget = pages[0]["sections"][0]["widgets"][0]
    assert widget["resolved_subvalue"] == 42


def test_resolve_widgets_final_re_resolves_url_when_none():
    """Line 377: resolved_url is None → re-resolved from full_context."""
    full_ctx = {"image": "redis:7"}
    pages = [
        {
            "sections": [
                {
                    "widgets": [
                        {
                            "label": "w",
                            "url": "https://hub.docker.com/r/{{ image }}",
                            "resolved_url": None,
                        }
                    ]
                }
            ]
        }
    ]
    resolve_widgets_final(pages, full_ctx)
    widget = pages[0]["sections"][0]["widgets"][0]
    assert widget["resolved_url"] == "https://hub.docker.com/r/redis:7"


def test_resolve_widgets_final_re_resolves_value_with_playbook_prefix():
    """Lines 346-355: value starting with 'playbook' prefix → re-resolved even if not None."""
    full_ctx = {"playbook": {"name": "default"}, "score": 0}
    pages = [
        {
            "sections": [
                {
                    "widgets": [
                        {
                            "label": "w",
                            "value": "playbook.name",
                            "resolved_value": "stale",
                        }
                    ]
                }
            ]
        }
    ]
    resolve_widgets_final(pages, full_ctx)
    widget = pages[0]["sections"][0]["widgets"][0]
    assert widget["resolved_value"] == "default"
