"""Coverage for regis/core/domain/playbook/conditions.py branches."""

from regis.core.domain.playbook.conditions import (
    ConditionResult,
    _stringify_condition,
    evaluate_condition,
)


def test_falsy_condition_returns_none():
    assert evaluate_condition(None, {}) is None
    assert evaluate_condition({}, {}) is None


def test_condition_passes_with_complete_data():
    """Normal path: condition evaluates to True, no missing data (line 51)."""
    res = evaluate_condition({"==": [{"var": "x"}, 1]}, {"x": 1})
    assert isinstance(res, ConditionResult)
    assert res.passed is True
    assert res.incomplete is False


def test_condition_exception_returns_incomplete():
    res = evaluate_condition({"/": [1, 0]}, {})  # division by zero
    assert isinstance(res, ConditionResult)
    assert res.passed is False and res.incomplete is True


def test_stringify_none_returns_missing():
    """Line 64: None condition → 'MISSING'."""
    out = _stringify_condition(None, {})
    assert out == "MISSING"


def test_stringify_var_missing_value():
    """Line 74: var not in context → 'key (MISSING)'."""
    out = _stringify_condition({"var": "x"}, {})
    assert out == "x (MISSING)"


def test_stringify_args_not_list():
    """Line 78: non-list args are wrapped in a list."""
    # "!" with a scalar arg (not a list) exercises the `args = [args]` branch
    out = _stringify_condition({"!": True}, {})
    assert "True" in out


def test_stringify_comparison_fewer_than_two_parts():
    """Line 87: comparison operator with single arg falls back to func notation."""
    out = _stringify_condition({"==": [1]}, {})
    assert out == "==(1)"


def test_stringify_not_operator():
    """Line 91: '!' operator → '!(…)'."""
    out = _stringify_condition({"!": [{"==": [1, 1]}]}, {})
    assert out.startswith("!(")


def test_stringify_or_operator():
    """Lines 94-95: 'or' operator joins with ' or '."""
    out = _stringify_condition({"or": [{"==": [1, 1]}, {"==": [2, 2]}]}, {})
    assert " or " in out


def test_stringify_unknown_operator_fallback():
    """Lines 96-97: unknown operator falls back to 'op(…)' notation."""
    out = _stringify_condition({"cat": ["hello", " ", "world"]}, {})
    assert out.startswith("cat(")


def test_stringify_in_operator():
    out = _stringify_condition(
        {"in": [{"var": "x"}, {"var": "xs"}]}, {"x": "a", "xs": ["a"]}
    )
    assert " in " in out


def test_stringify_and_operator():
    out = _stringify_condition({"and": [{"==": [1, 1]}, {"==": [2, 2]}]}, {})
    assert " and " in out
