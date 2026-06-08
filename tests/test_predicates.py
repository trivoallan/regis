"""Tests for shared rule/meta predicate helpers."""

import pytest

from regis.utils.predicates import is_empty, is_falsy, is_truthy, is_url, matches


@pytest.mark.parametrize("value", ["true", "TRUE", "1", "yes", "On", " true "])
def test_is_truthy_true(value):
    assert is_truthy(value) is True


def test_is_truthy_bool():
    assert is_truthy(True) is True


@pytest.mark.parametrize("value", ["false", "0", "no", "off", "maybe", "", None, 1, 0])
def test_is_truthy_false(value):
    assert is_truthy(value) is False


@pytest.mark.parametrize("value", ["false", "FALSE", "0", "no", "Off", " false "])
def test_is_falsy_true(value):
    assert is_falsy(value) is True


def test_is_falsy_bool():
    assert is_falsy(False) is True


@pytest.mark.parametrize("value", ["true", "1", "maybe", "", None, 0])
def test_is_falsy_false(value):
    assert is_falsy(value) is False


@pytest.mark.parametrize(
    "value", ["http://x.io", "https://github.com/org/repo/actions/runs/1"]
)
def test_is_url_true(value):
    assert is_url(value) is True


@pytest.mark.parametrize(
    "value",
    [
        "not a url",
        "ftp://x.io",
        "github.com",
        "",
        None,
        123,
        "https://",
        "https://not a url",
        "https://exa mple.com",
    ],
)
def test_is_url_false(value):
    assert is_url(value) is False


@pytest.mark.parametrize("value", [None, "", "   "])
def test_is_empty_true(value):
    assert is_empty(value) is True


@pytest.mark.parametrize("value", ["x", "0", 0, False])
def test_is_empty_false(value):
    assert is_empty(value) is False


def test_matches_hit():
    assert matches("job-42", r"^job-[0-9]+$") is True


def test_matches_miss():
    assert matches("job-x", r"^job-[0-9]+$") is False


def test_matches_invalid_regex_is_false():
    assert matches("anything", r"[unclosed") is False


@pytest.mark.parametrize("value", [None, 123])
def test_matches_non_string_is_false(value):
    assert matches(value, r".*") is False
