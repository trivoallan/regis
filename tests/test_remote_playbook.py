"""Tests for remote playbook loading."""

from __future__ import annotations

import pytest
import responses
import yaml

from regis.playbook.engine import load_playbook


@responses.activate
def test_load_playbook_remote_yaml():
    url = "https://example.com/playbook.yaml"
    content = {
        "apiVersion": "regis.trivoallan.dev/v1alpha1",
        "kind": "Playbook",
        "metadata": {
            "name": "remote-playbook",
            "title": "Remote Playbook",
            "labels": {"app.kubernetes.io/version": "1.0.0"},
        },
        "spec": {
            "rules": [
                {
                    "slug": "main-rule",
                    "provider": "core",
                    "rule": "always-true",
                    "level": "warning",
                },
            ],
        },
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
    assert loaded["rules"][0]["slug"] == "main-rule"


@responses.activate
def test_load_playbook_remote_json():
    import json

    url = "https://example.com/playbook.json"
    content = {
        "apiVersion": "regis.trivoallan.dev/v1alpha1",
        "kind": "Playbook",
        "metadata": {
            "name": "remote-json",
            "title": "Remote JSON",
            "labels": {"app.kubernetes.io/version": "1.0.0"},
        },
        "spec": {
            "rules": [
                {
                    "slug": "json-rule",
                    "provider": "core",
                    "rule": "always-true",
                    "level": "warning",
                },
            ],
        },
    }
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
