"""The default playbook's MR link must read the canonical top-level metadata.*."""

from __future__ import annotations

import importlib.resources

from regis.core.domain.playbook.engine import load_playbook
from regis.core.domain.playbook.evaluator import _resolve_links


def _load_default_playbook() -> dict:
    pb_dir = importlib.resources.files("regis") / "playbooks" / "default"
    return load_playbook(str(pb_dir))


def test_mr_link_resolves_from_top_level_metadata():
    playbook = _load_default_playbook()
    mr_url = "https://gitlab.example/group/proj/-/merge_requests/7"
    full_context = {"metadata": {"gitlab": {"mr_url": mr_url}}}
    result: dict = {}

    _resolve_links(playbook, result, full_context, full_context)

    assert {"label": "Return to Merge Request", "url": mr_url} in result.get(
        "links", []
    )


def test_mr_link_absent_without_metadata():
    playbook = _load_default_playbook()
    full_context = {"metadata": {}}
    result: dict = {}

    _resolve_links(playbook, result, full_context, full_context)

    labels = [link.get("label") for link in result.get("links", [])]
    assert "Return to Merge Request" not in labels
