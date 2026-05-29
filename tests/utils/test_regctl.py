"""Tests for the shared regctl subprocess wrapper."""

from __future__ import annotations

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
    assert image_ref("docker.io", "library/alpine", "3.20") == "docker.io/library/alpine:3.20"


def test_image_ref_digest_uses_at_separator():
    ref = image_ref("docker.io", "library/alpine", "sha256:abc")
    assert ref == "docker.io/library/alpine@sha256:abc"


def test_image_ref_normalizes_dockerhub():
    assert image_ref("registry-1.docker.io", "library/alpine", "3.20").startswith("docker.io/")


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
    mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="OUT", stderr="")
    run_regctl(_client("alice", "pa,ss"), ["tag", "ls", "x"])
    cmd = mock_run.call_args.args[0]
    env = mock_run.call_args.kwargs["env"]
    assert "--host" not in cmd
    assert "DOCKER_CONFIG" in env


@patch("regis.utils.regctl.subprocess.run", side_effect=FileNotFoundError())
def test_run_regctl_missing_binary_raises(mock_run):
    with pytest.raises(AnalyzerError, match="regctl not found"):
        run_regctl(_client(), ["version"])
