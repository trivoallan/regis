"""Tests de `regis playbook upgrade` (legacy plat → enveloppe k8s)."""

from __future__ import annotations

import yaml
from click.testing import CliRunner

from regis.commands.playbook import playbook_group
from regis.core.domain.playbook.loader import load_playbook


def _run(path) -> str:
    result = CliRunner().invoke(playbook_group, ["upgrade", str(path)])
    assert result.exit_code == 0, result.output
    return result.output


def test_upgrade_flat_to_envelope(tmp_path) -> None:
    pb = tmp_path / "playbook.yaml"
    pb.write_text(
        "schemaVersion: 1\n"
        'version: "2.1.0"\n'
        "name: My Playbook\n"
        "slug: my-pb\n"
        "rules:\n"
        "  - provider: cve\n"
        "    rule: cve-count\n"
        "    slug: c\n"
        "    level: info\n",
        encoding="utf-8",
    )
    _run(pb)
    data = yaml.safe_load(pb.read_text(encoding="utf-8"))
    assert data["apiVersion"] == "regis.io/v1alpha1"
    assert data["kind"] == "Playbook"
    assert data["metadata"]["name"] == "my-pb"
    assert data["metadata"]["title"] == "My Playbook"
    assert data["metadata"]["labels"]["app.kubernetes.io/version"] == "2.1.0"
    assert data["spec"]["rules"][0]["slug"] == "c"
    assert load_playbook(pb)["name"] == "My Playbook"


def test_upgrade_slugifies_name_when_no_slug(tmp_path) -> None:
    pb = tmp_path / "playbook.yaml"
    pb.write_text("name: My Cool Playbook\nrules: []\n", encoding="utf-8")
    _run(pb)
    data = yaml.safe_load(pb.read_text(encoding="utf-8"))
    assert data["metadata"]["name"] == "my-cool-playbook"
    assert data["metadata"]["labels"]["app.kubernetes.io/version"] == "1.0.0"


def test_upgrade_drops_deprecated_pages(tmp_path) -> None:
    pb = tmp_path / "playbook.yaml"
    pb.write_text(
        "name: P\nslug: p\npages:\n  - title: Overview\n    sections: []\n",
        encoding="utf-8",
    )
    out = _run(pb)
    data = yaml.safe_load(pb.read_text(encoding="utf-8"))
    assert "pages" not in data and "pages" not in data.get("spec", {})
    assert "Dropped deprecated: pages" in out


def test_upgrade_is_idempotent(tmp_path) -> None:
    pb = tmp_path / "playbook.yaml"
    pb.write_text("name: P\nslug: p\nrules: []\n", encoding="utf-8")
    _run(pb)
    first = pb.read_text(encoding="utf-8")
    out = _run(pb)
    assert pb.read_text(encoding="utf-8") == first
    assert "nothing to do" in out


def test_upgrade_slugifies_legacy_slug(tmp_path) -> None:
    pb = tmp_path / "playbook.yaml"
    pb.write_text("name: P\nslug: My_Legacy_Slug\nrules: []\n", encoding="utf-8")
    _run(pb)
    data = yaml.safe_load(pb.read_text(encoding="utf-8"))
    assert data["metadata"]["name"] == "my-legacy-slug"
    # L'enveloppe produite est rechargeable (donc valide).
    assert load_playbook(pb)["slug"] == "my-legacy-slug"


def test_upgrade_suggests_validate(tmp_path) -> None:
    pb = tmp_path / "playbook.yaml"
    pb.write_text("name: P\nslug: p\nrules: []\n", encoding="utf-8")
    out = _run(pb)
    assert "regis playbook validate" in out
