"""Tests for the shared regctl subprocess wrapper."""

from __future__ import annotations

import base64
import json
import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from regis.analyzers.base import AnalyzerError
from regis.registry.client import RegistryClient
from regis.utils.regctl import image_ref, run_regctl


def _client(username=None, password=None, registry="docker.io"):
    c = MagicMock(spec=RegistryClient)
    c.registry = registry
    c.username = username
    c.password = password
    return c


def test_image_ref_tag():
    assert (
        image_ref("docker.io", "library/alpine", "3.20")
        == "docker.io/library/alpine:3.20"
    )


def test_image_ref_digest_uses_at_separator():
    ref = image_ref("docker.io", "library/alpine", "sha256:abc")
    assert ref == "docker.io/library/alpine@sha256:abc"


def test_image_ref_normalizes_dockerhub():
    assert image_ref("registry-1.docker.io", "library/alpine", "3.20").startswith(
        "docker.io/"
    )


@patch("regis.utils.regctl.subprocess.run")
def test_run_regctl_no_creds(mock_run):
    mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="OUT", stderr="")
    out = run_regctl(_client(), ["tag", "ls", "docker.io/library/alpine"])
    assert out == "OUT"
    cmd = mock_run.call_args.args[0]
    assert cmd[0] == "regctl"
    assert "--host" not in cmd


@patch("regis.utils.regctl.subprocess.run")
def test_run_regctl_inline_creds(mock_run):
    mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="OUT", stderr="")
    run_regctl(_client("alice", "s3cret"), ["tag", "ls", "x"])
    cmd = mock_run.call_args.args[0]
    assert "--host" in cmd
    host_val = cmd[cmd.index("--host") + 1]
    assert host_val == "reg=docker.io,user=alice,pass=s3cret"


@patch("regis.utils.regctl.subprocess.run")
def test_run_regctl_comma_password_uses_docker_config(mock_run):
    captured: dict = {}

    def _side_effect(cmd, **kwargs):
        env = kwargs["env"]
        config_path = os.path.join(env["DOCKER_CONFIG"], "config.json")
        with open(config_path, encoding="utf-8") as fh:
            config = json.load(fh)
        captured["auth"] = config["auths"]["docker.io"]["auth"]
        return subprocess.CompletedProcess(cmd, 0, stdout="OUT", stderr="")

    mock_run.side_effect = _side_effect
    run_regctl(_client("alice", "pa,ss"), ["tag", "ls", "x"])

    cmd = mock_run.call_args.args[0]
    env = mock_run.call_args.kwargs["env"]
    assert "--host" not in cmd
    assert "DOCKER_CONFIG" in env
    # Verify the config.json contained the correct base64-encoded credential.
    decoded = base64.b64decode(captured["auth"]).decode()
    assert decoded == "alice:pa,ss"


@patch("regis.utils.regctl.subprocess.run", side_effect=FileNotFoundError())
def test_run_regctl_missing_binary_raises(mock_run):
    with pytest.raises(AnalyzerError, match="regctl not found"):
        run_regctl(_client(), ["version"])


@patch(
    "regis.utils.regctl.subprocess.run",
    side_effect=subprocess.TimeoutExpired(cmd="regctl", timeout=60),
)
def test_run_regctl_timeout_raises_analyzer_error(mock_run):
    with pytest.raises(AnalyzerError, match="timed out"):
        run_regctl(_client(), ["version"])


@patch("regis.utils.regctl.subprocess.run")
def test_run_regctl_comma_password_temp_dir_cleaned_up(mock_run):
    """The temp DOCKER_CONFIG dir must be removed after run_regctl returns."""
    recorded_dir: list[str] = []

    def _side_effect(cmd, **kwargs):
        recorded_dir.append(kwargs["env"]["DOCKER_CONFIG"])
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    mock_run.side_effect = _side_effect
    run_regctl(_client("alice", "pa,ss"), ["tag", "ls", "x"])

    assert recorded_dir, "side_effect was not called"
    assert not os.path.exists(recorded_dir[0]), "temp dir was not cleaned up"
