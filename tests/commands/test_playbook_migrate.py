"""Tests de `regis playbook migrate` (vocabulaire `rule` → `criterion`).

Le codemod réécrit deux surfaces d'un playbook utilisateur :

1. la clé de référence de template ``rule:`` → ``criterion:`` ;
2. les références ``rule.`` (conditions JSON-Logic) et ``${rule.…}`` (messages)
   → ``criterion.`` / ``${criterion.…}``.

Invariant de sûreté : parce que le moteur fait du *dual-bind*, un playbook
pré-migration et son jumeau migré doivent produire un rapport IDENTIQUE.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

from regis.commands.playbook import (
    _migrate_condition_tree,
    _migrate_message,
    _migrate_playbook_data,
    _migrate_var_path,
    playbook_group,
)
from regis.rules.evaluator import evaluate_rules

# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

# A playbook that exercises BOTH surfaces:
#   - a template-reference entry using the legacy `rule:` key,
#   - a fully custom rule whose condition references `rule.params.*`
#     and whose messages interpolate `${rule.…}`, including a NESTED
#     interpolation `${results.cve.${rule.params.level}_count}`.
_LEGACY_PLAYBOOK = """\
# yaml-language-server: $schema=../../schemas/playbook/v1alpha1/playbook.schema.json
apiVersion: regis.trivoallan.dev/v1alpha1
kind: Playbook
metadata:
  name: legacy
  title: Legacy Playbook
  labels:
    app.kubernetes.io/version: 1.0.0
spec:
  rules:
    # Template reference using the legacy key.
    - provider: cve
      rule: cve-count          # <- legacy template-reference key
      slug: cve-critical
      level: critical
      options:
        level: critical
        max_count: 0
    # A fully custom rule referencing rule.params in condition + messages.
    # The condition also references the BARE `{"var": "rule"}` operand, which the
    # engine dual-binds to the whole criterion object — exercising the bare-token
    # migration path (`rule` -> `criterion`, no trailing dot).
    - slug: custom-cve-gate
      provider: custom
      level: warning
      params:
        level: critical
        threshold: 0
      condition:
        and:
          - "!!":
              var: rule          # <- bare operand: whole criterion object
          - ">":
              - var: results.cve.critical_count
              - var: rule.params.threshold
      messages:
        pass: "OK: ${results.cve.${rule.params.level}_count} <= ${rule.params.threshold}"
        fail: "FAIL: ${results.cve.${rule.params.level}_count} > ${rule.params.threshold}"
"""

_SAMPLE_REPORT = {
    "request": {"registry": "docker.io", "analyzers": ["cve"]},
    "results": {
        "cve": {
            "critical_count": 3,
            "high_count": 5,
            "fixed_count": 0,
        }
    },
}


def _write(tmp_path: Path, text: str) -> Path:
    pb = tmp_path / "playbook.yaml"
    pb.write_text(text, encoding="utf-8")
    return pb


# --------------------------------------------------------------------------- #
# Unit tests — the fragile bits
# --------------------------------------------------------------------------- #


def test_migrate_var_path_bare_rule_has_no_trailing_dot() -> None:
    # Bare operand must become `criterion` (no trailing dot): the engine
    # dual-binds {"var": "rule"} / {"var": "criterion"} to the whole criterion
    # object, whereas {"var": "criterion."} would resolve to None and change
    # evaluation.
    assert _migrate_var_path("rule") == "criterion"


def test_migrate_var_path_dotted_and_untouched() -> None:
    # Dotted legacy path is rewritten.
    assert _migrate_var_path("rule.params.x") == "criterion.params.x"
    # Already-migrated path is idempotent.
    assert _migrate_var_path("criterion.params.x") == "criterion.params.x"
    # Identifiers that merely start with `rule` are left untouched.
    assert _migrate_var_path("rules_summary") == "rules_summary"
    assert _migrate_var_path("ruler") == "ruler"
    assert _migrate_var_path("results.cve.critical_count") == (
        "results.cve.critical_count"
    )


def test_migrate_condition_tree_rewrites_var_paths() -> None:
    tree = {
        ">": [
            {"var": "results.cve.critical_count"},
            {"var": "rule.params.threshold"},
        ]
    }
    out = _migrate_condition_tree(tree)
    assert out == {
        ">": [
            {"var": "results.cve.critical_count"},
            {"var": "criterion.params.threshold"},
        ]
    }
    # results.* untouched.
    assert out[">"][0] == {"var": "results.cve.critical_count"}


def test_migrate_condition_tree_nested_and_lists() -> None:
    tree = {
        "and": [
            {"<": [{"var": "rule.params.a"}, 1]},
            {"or": [{"==": [{"var": "rule.params.b"}, {"var": "results.x.y"}]}]},
        ]
    }
    out = _migrate_condition_tree(tree)
    assert out["and"][0]["<"][0] == {"var": "criterion.params.a"}
    assert out["and"][1]["or"][0]["=="][0] == {"var": "criterion.params.b"}
    assert out["and"][1]["or"][0]["=="][1] == {"var": "results.x.y"}


def test_migrate_condition_tree_idempotent() -> None:
    tree = {">": [{"var": "criterion.params.threshold"}, 0]}
    assert _migrate_condition_tree(tree) == tree


def test_migrate_condition_tree_does_not_touch_rule_prefixed_other_keys() -> None:
    # `ruler.x` and `rules_summary.score` must not be touched (only `rule.`).
    tree = {">": [{"var": "rules_summary.score"}, 90]}
    assert _migrate_condition_tree(tree) == tree


def test_migrate_message_simple() -> None:
    assert (
        _migrate_message("threshold is ${rule.params.threshold}")
        == "threshold is ${criterion.params.threshold}"
    )


def test_migrate_message_nested_interpolation() -> None:
    # Inner ${rule.…} rewritten; outer ${results.…} preserved intact.
    src = "${results.cve.${rule.params.level}_count} > ${rule.params.threshold}"
    expected = (
        "${results.cve.${criterion.params.level}_count} > ${criterion.params.threshold}"
    )
    assert _migrate_message(src) == expected


def test_migrate_message_leaves_results_alone() -> None:
    assert _migrate_message("${results.cve.critical_count}") == (
        "${results.cve.critical_count}"
    )


def test_migrate_message_idempotent() -> None:
    src = "${results.cve.${criterion.params.level}_count}"
    assert _migrate_message(src) == src


def test_migrate_playbook_data_renames_key_and_refs() -> None:
    data = yaml.safe_load(_LEGACY_PLAYBOOK)
    _migrate_playbook_data(data)
    rules = data["spec"]["rules"]
    # 1. template-reference key renamed.
    assert "rule" not in rules[0]
    assert rules[0]["criterion"] == "cve-count"
    # other keys untouched.
    assert rules[0]["provider"] == "cve"
    assert rules[0]["slug"] == "cve-critical"
    # 2. condition + messages rewritten.
    custom = rules[1]
    cond = custom["condition"]
    # Bare `{"var": "rule"}` -> `{"var": "criterion"}` (no trailing dot).
    assert cond["and"][0]["!!"] == {"var": "criterion"}
    assert cond["and"][1][">"][1] == {"var": "criterion.params.threshold"}
    assert "${criterion.params.level}" in custom["messages"]["pass"]
    assert (
        "${results.cve.${criterion.params.level}_count}" in custom["messages"]["fail"]
    )


# --------------------------------------------------------------------------- #
# Safety-net invariant: migration MUST NOT change evaluation
# --------------------------------------------------------------------------- #


def test_migration_preserves_evaluation(tmp_path: Path) -> None:
    """Pre- and post-migration playbooks evaluate to an IDENTICAL report."""
    pb = _write(tmp_path, _LEGACY_PLAYBOOK)

    before = yaml.safe_load(pb.read_text(encoding="utf-8"))
    # Custom rules live under spec.rules; evaluate_rules reads `rules`.
    res_before = evaluate_rules(_SAMPLE_REPORT, {"rules": before["spec"]["rules"]})

    CliRunner().invoke(playbook_group, ["migrate", "-i", str(pb)])

    after = yaml.safe_load(pb.read_text(encoding="utf-8"))
    res_after = evaluate_rules(_SAMPLE_REPORT, {"rules": after["spec"]["rules"]})

    assert res_after == res_before


def test_migrate_idempotent(tmp_path: Path) -> None:
    """migrate(migrate(pb)) == migrate(pb)."""
    pb = _write(tmp_path, _LEGACY_PLAYBOOK)
    CliRunner().invoke(playbook_group, ["migrate", "-i", str(pb)])
    once = pb.read_text(encoding="utf-8")
    CliRunner().invoke(playbook_group, ["migrate", "-i", str(pb)])
    twice = pb.read_text(encoding="utf-8")
    assert twice == once
    # And no legacy tokens remain.
    assert "rule:" not in twice
    assert "${rule." not in twice


# --------------------------------------------------------------------------- #
# CLI shape
# --------------------------------------------------------------------------- #


def test_migrate_stdout_default_does_not_touch_file(tmp_path: Path) -> None:
    pb = _write(tmp_path, _LEGACY_PLAYBOOK)
    original = pb.read_text(encoding="utf-8")
    result = CliRunner().invoke(playbook_group, ["migrate", str(pb)])
    assert result.exit_code == 0, result.output
    # Migrated content goes to stdout.
    assert "criterion: cve-count" in result.output
    assert "${criterion.params.level}" in result.output
    # File on disk is unchanged in default (stdout) mode.
    assert pb.read_text(encoding="utf-8") == original


def test_migrate_in_place_rewrites_file(tmp_path: Path) -> None:
    pb = _write(tmp_path, _LEGACY_PLAYBOOK)
    result = CliRunner().invoke(playbook_group, ["migrate", "--in-place", str(pb)])
    assert result.exit_code == 0, result.output
    text = pb.read_text(encoding="utf-8")
    assert "criterion: cve-count" in text
    assert "rule: cve-count" not in text
    assert "${criterion.params.level}" in text


def test_migrate_preserves_comments(tmp_path: Path) -> None:
    pb = _write(tmp_path, _LEGACY_PLAYBOOK)
    CliRunner().invoke(playbook_group, ["migrate", "-i", str(pb)])
    text = pb.read_text(encoding="utf-8")
    # ruamel round-trip keeps the leading schema comment.
    assert "yaml-language-server" in text


def test_migrate_already_migrated_is_noop(tmp_path: Path) -> None:
    pb = _write(tmp_path, _LEGACY_PLAYBOOK)
    CliRunner().invoke(playbook_group, ["migrate", "-i", str(pb)])
    once = pb.read_text(encoding="utf-8")
    result = CliRunner().invoke(playbook_group, ["migrate", "-i", str(pb)])
    assert result.exit_code == 0, result.output
    assert pb.read_text(encoding="utf-8") == once


# A hand-written playbook that is already `criterion`-native: the legacy `rule`
# vocabulary is entirely absent (template-reference key, condition var paths and
# message interpolations all use `criterion`). Migration must round-trip it
# byte-for-byte.
_CRITERION_NATIVE_PLAYBOOK = """\
# yaml-language-server: $schema=../../schemas/playbook/v1alpha1/playbook.schema.json
apiVersion: regis.trivoallan.dev/v1alpha1
kind: Playbook
metadata:
  name: native
  title: Criterion-native Playbook
  labels:
    app.kubernetes.io/version: 1.0.0
spec:
  rules:
    - provider: cve
      criterion: cve-count
      slug: cve-critical
      level: critical
      options:
        level: critical
        max_count: 0
    - slug: custom-cve-gate
      provider: custom
      level: warning
      params:
        level: critical
        threshold: 0
      condition:
        and:
          - "!!":
              var: criterion
          - ">":
              - var: results.cve.critical_count
              - var: criterion.params.threshold
      messages:
        pass: "OK: ${results.cve.${criterion.params.level}_count} <= ${criterion.params.threshold}"
        fail: "FAIL: ${results.cve.${criterion.params.level}_count} > ${criterion.params.threshold}"
"""


def test_migrate_malformed_yaml_raises_friendly_error(tmp_path: Path) -> None:
    """A malformed playbook surfaces a friendly ClickException, not a traceback."""
    # Unbalanced flow mapping — ruamel raises during load.
    pb = _write(tmp_path, "spec:\n  rules: [ {rule: cve-count\n")
    result = CliRunner().invoke(playbook_group, ["migrate", "-i", str(pb)])
    # Friendly ClickException -> exit code 1 with the message on stderr/stdout,
    # NOT an unhandled exception bubbling a raw ruamel traceback to the user.
    assert result.exit_code != 0
    assert "Failed to load playbook" in result.output
    assert not isinstance(result.exception, SystemExit) or result.exit_code == 1
    assert "Traceback (most recent call last)" not in result.output


def test_migrate_criterion_native_roundtrips_byte_identical(tmp_path: Path) -> None:
    """An already-`criterion`-only playbook round-trips byte-for-byte."""
    pb = _write(tmp_path, _CRITERION_NATIVE_PLAYBOOK)
    original = pb.read_text(encoding="utf-8")
    result = CliRunner().invoke(playbook_group, ["migrate", "-i", str(pb)])
    assert result.exit_code == 0, result.output
    assert pb.read_text(encoding="utf-8") == original
