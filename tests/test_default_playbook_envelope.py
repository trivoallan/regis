"""Le playbook par défaut livré est au format enveloppe et chargeable."""

from __future__ import annotations

import importlib.resources

from regis.playbook.loader import load_playbook


def test_default_playbook_loads_as_envelope() -> None:
    path = importlib.resources.files("regis.playbooks.default").joinpath(
        "playbook.yaml"
    )
    with importlib.resources.as_file(path) as p:
        pb = load_playbook(p)
    assert pb["apiVersion"] == "regis.trivoallan.dev/v1alpha1"
    assert pb["kind"] == "Playbook"
    assert pb["slug"] == "default"
    assert pb["version"] == "1.0.0"
    assert any(r["slug"] == "cve-critical" for r in pb["rules"])
    assert [t["name"] for t in pb["tiers"]] == ["Gold", "Silver", "Bronze"]
