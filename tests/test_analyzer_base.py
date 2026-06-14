"""Tests for BaseAnalyzer.default_criteria / default_rules back-compat shim."""

from __future__ import annotations

import json
import warnings
from typing import Any

import pytest

from regis.analyzers.base import BaseAnalyzer
from regis.analyzers.cve import CveAnalyzer


def _criterion() -> dict[str, Any]:
    return {
        "slug": "dummy",
        "level": "warning",
        "params": {"max_count": 0},
        "condition": {"<=": [{"var": "results.dummy.count"}, 0]},
        "messages": {"pass": "ok", "fail": "no"},
    }


class _NewStyleAnalyzer(BaseAnalyzer):
    """First-party-style analyzer overriding the canonical method."""

    name = "newstyle"
    schema_file = "analyzer/cve.schema.json"

    @classmethod
    def default_criteria(cls) -> list[dict[str, Any]]:
        return [_criterion()]

    def analyze(self, client, repository, tag, platform=None):  # type: ignore[no-untyped-def]
        return {}


class _LegacyAnalyzer(BaseAnalyzer):
    """Third-party-style analyzer that only overrides the deprecated method."""

    name = "legacy"
    schema_file = "analyzer/cve.schema.json"

    @classmethod
    def default_rules(cls) -> list[dict[str, Any]]:
        return [_criterion()]

    def analyze(self, client, repository, tag, platform=None):  # type: ignore[no-untyped-def]
        return {}


def test_cve_default_criteria_slugs():
    slugs = {c["slug"] for c in CveAnalyzer.default_criteria()}
    assert {"fix-available", "cve-count"} <= slugs


def test_cve_default_criteria_use_criterion_namespace():
    serialized = json.dumps(CveAnalyzer.default_criteria())
    assert "criterion.params." in serialized
    assert "rule.params." not in serialized


def test_legacy_subclass_is_picked_up_via_default_criteria():
    """A subclass overriding only the old default_rules() still works.

    The base default_criteria() must delegate to the overridden legacy method
    without emitting a warning (the subclass is external and exercised here).
    """
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        criteria = _LegacyAnalyzer.default_criteria()
    assert [c["slug"] for c in criteria] == ["dummy"]


def test_new_style_default_rules_shim_emits_deprecation_warning():
    """Calling the deprecated default_rules() on a new-style analyzer warns."""
    with pytest.warns(DeprecationWarning):
        result = _NewStyleAnalyzer.default_rules()
    assert [c["slug"] for c in result] == ["dummy"]


def test_first_party_default_rules_emits_deprecation_warning():
    with pytest.warns(DeprecationWarning):
        CveAnalyzer.default_rules()


def test_base_default_criteria_empty_without_override():
    class _Bare(BaseAnalyzer):
        name = "bare"
        schema_file = "analyzer/cve.schema.json"

        def analyze(self, client, repository, tag, platform=None):  # type: ignore[no-untyped-def]
            return {}

    # No infinite recursion, returns empty defaults.
    assert _Bare.default_criteria() == []


def test_base_analyzer_uses_context_defaults_false():
    from regis.analyzers.base import BaseAnalyzer

    assert BaseAnalyzer.uses_context is False


def test_subclass_can_opt_into_context():
    from regis.analyzers.base import BaseAnalyzer

    class CtxAnalyzer(BaseAnalyzer):
        uses_context = True

        def analyze(self, ctx):  # type: ignore[override]
            return {}

    assert CtxAnalyzer.uses_context is True
    assert CtxAnalyzer().uses_context is True
