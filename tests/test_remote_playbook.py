"""Tests for remote playbook loading."""

from __future__ import annotations

import pytest
import responses
import yaml

from regis_cli.playbook.engine import load_playbook


@responses.activate
def test_load_playbook_remote_yaml():
    url = "https://example.com/playbook.yaml"
    content = {
        "name": "Remote Playbook",
        "sections": [{"name": "Main", "scorecards": []}],
    }
    responses.add(
        responses.GET,
        url,
        body=yaml.dump(content),
        status=200,
        content_type="text/yaml",
    )

    loaded = load_playbook(url)
    assert loaded["name"] == "Remote Playbook"
    assert loaded["sections"][0]["name"] == "Main"


@responses.activate
def test_load_playbook_remote_json():
    import json

    url = "https://example.com/playbook.json"
    content = {"name": "Remote JSON", "sections": []}
    responses.add(
        responses.GET,
        url,
        body=json.dumps(content),
        status=200,
        content_type="application/json",
    )

    loaded = load_playbook(url)
    assert loaded["name"] == "Remote JSON"


@responses.activate
def test_load_playbook_remote_error():
    url = "https://example.com/missing.yaml"
    responses.add(
        responses.GET,
        url,
        status=404,
    )

    with pytest.raises(ValueError, match="Failed to download playbook from"):
        load_playbook(url)
