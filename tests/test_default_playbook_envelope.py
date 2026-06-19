"""Le playbook par défaut livré est au format enveloppe et chargeable."""

from __future__ import annotations

import importlib.resources

from regis.core.domain.playbook.loader import load_playbook


def test_default_playbook_loads_as_envelope() -> None:
    path = importlib.resources.files("regis.playbooks.default").joinpath(
        "playbook.yaml"
    )
    with importlib.resources.as_file(path) as p:
        pb = load_playbook(p)
    assert pb["apiVersion"] == "regis.io/v1alpha1"
    assert pb["kind"] == "Playbook"
    assert pb["slug"] == "default"
    assert pb["version"] == "2.0.0"
    assert any(r["slug"] == "cve-critical" for r in pb["rules"])
    # Security criteria previously auto-injected are now declared explicitly.
    declared_slugs = {r["slug"] for r in pb["rules"]}
    assert {"dockle-fatal", "hadolint-error", "secret-scan"} <= declared_slugs
    # OCI heuristics are NOT declared by the default playbook.
    assert "max-size" not in declared_slugs
    assert "layers-count" not in declared_slugs
    assert [t["name"] for t in pb["tiers"]] == ["Gold", "Silver", "Bronze"]
