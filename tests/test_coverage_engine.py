from regis.core.domain.playbook.engine import (
    MissingDataTracker,
    _format_date,
    _format_datetime,
    _format_time,
    _resolve_path,
    _resolve_template,
    _stringify_condition,
    evaluate,
)


def test_date_format_errors():
    assert _format_date("invalid") == "invalid"
    assert _format_datetime("invalid") == "invalid"
    assert _format_time("invalid") == "invalid"
    assert _format_date(None) is None


def test_resolve_template_edge_cases():
    # Non-string input
    assert _resolve_template(123, {}) == 123
    # Template error
    assert _resolve_template("{{ invalid.unclosed", {}) == "{{ invalid.unclosed"


def test_resolve_path_edge_cases():
    # Non-string input
    assert _resolve_path(123, {}) == 123

    # Jinja2 in path error - it might return the template string or a string representation of the error
    # but strictly it returns template_str on exception in _resolve_path
    assert (
        _resolve_path("{{ invalid() }}", {"invalid": lambda: 1 / 0})
        == "{{ invalid() }}"
    )

    # Path traversal edge cases
    context = {"a": {"b": [10, 20]}}
    assert _resolve_path("a..b", context) == [10, 20]  # skips empty parts
    assert _resolve_path("a.b.string", context) is None  # non-integer index for list
    assert _resolve_path("a.b.99", context) is None  # out of bounds
    assert _resolve_path("a.b.0.deep", context) is None  # too deep on scalar


def test_missing_data_tracker_none_and_contains():
    data = {"a": None}
    tracker = MissingDataTracker(data)

    # Trigger missing_accessed via None value
    assert tracker["a"] is None
    assert tracker.missing_accessed is True

    tracker.missing_accessed = False
    # Trigger via __contains__
    assert "b" not in tracker
    assert tracker.missing_accessed is True

    # Contains with non-string key
    assert 123 not in tracker


def test_stringify_condition_edge_cases():
    assert _stringify_condition(None, {}) == "MISSING"
    assert _stringify_condition(123, {}) == "123"

    # Operator with non-list args
    assert _stringify_condition({">": 10}, {}) == ">(10)"

    # Less common or complex operators
    assert _stringify_condition({"unknown": [1, 2]}, {}) == "unknown(1, 2)"
    assert _stringify_condition({"!": [True]}, {}) == "!(True)"
    assert _stringify_condition({"or": [True, False]}, {}) == "(True) or (False)"


def test_evaluate_errors_and_edge_cases(caplog):
    # Exercise the link / sidebar error and edge-case branches of evaluate().
    playbook = {
        "schemaVersion": 1,
        "version": "1.0.0",
        "name": "Test",
        "links": [
            "not a dict",
            {"label": "Link1", "condition": {"/": [1, 0]}},  # Condition error
            {"label": "Link2", "url": 123},  # non-string URL
            {"label": "Link3", "url": "{{ 1/0 }}"},  # Template error
        ],
        "sidebar": {"title": "Sidebar"},
        "integrations": {"gitlab": {"badges": ["non-existent"]}},
    }
    report = {"results": {}}

    result = evaluate(playbook, report)

    assert result["score"] == 0
    # Link3 failed to resolve but it seems it stayed in the list if the exception was in _resolve_template?
    # _resolve_template catches Exception and returns the template_str unchanged,
    # so the URL stays "{{ 1/0 }}".
    assert "links" in result
    assert result.get("badge_labels") is None  # No badges matched
