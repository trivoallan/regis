"""RegctlImageInspector adapts the regctl CLI to the ImageInspector port."""

import subprocess
from unittest.mock import create_autospec

import pytest

from regis.adapters.driven.registry import regctl_image_inspector as mod
from regis.adapters.driven.registry.client import RegistryClient
from regis.adapters.driven.registry.regctl_image_inspector import RegctlImageInspector
from regis.core.domain.errors import RegistryError
from regis.core.ports.image_inspector import ImageInspector


def _inspector() -> tuple[RegctlImageInspector, RegistryClient]:
    client = create_autospec(RegistryClient, instance=True)
    client.registry = "docker.io"
    client.repository = "library/nginx"
    return RegctlImageInspector(client), client


def test_is_an_image_inspector() -> None:
    inspector, _ = _inspector()
    assert isinstance(inspector, ImageInspector)


def test_list_tags_splits_and_drops_blanks(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_regctl(client, args):
        captured["args"] = args
        return "1.27\n1.26\n\n  \nlatest\n"

    monkeypatch.setattr(mod, "run_regctl", fake_run_regctl)
    inspector, _ = _inspector()
    assert inspector.list_tags() == ["1.27", "1.26", "latest"]
    assert captured["args"] == ["tag", "ls", "docker.io/library/nginx"]


def test_get_manifest_parses_raw_body(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_regctl(client, args):
        captured["args"] = args
        return '{"schemaVersion": 2, "mediaType": "application/vnd.oci.image.index.v1+json"}'

    monkeypatch.setattr(mod, "run_regctl", fake_run_regctl)
    inspector, _ = _inspector()
    assert inspector.get_manifest("1.27") == {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.index.v1+json",
    }
    assert captured["args"] == [
        "manifest",
        "get",
        "docker.io/library/nginx:1.27",
        "--format",
        "raw-body",
    ]


def test_get_blob_parses_config(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_regctl(client, args):
        captured["args"] = args
        return '{"architecture": "amd64", "os": "linux", "config": {}}'

    monkeypatch.setattr(mod, "run_regctl", fake_run_regctl)
    inspector, _ = _inspector()
    assert inspector.get_blob("sha256:abc123") == {
        "architecture": "amd64",
        "os": "linux",
        "config": {},
    }
    assert captured["args"] == [
        "blob",
        "get",
        "docker.io/library/nginx",
        "sha256:abc123",
    ]


def test_get_digest_strips(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_regctl(client, args):
        captured["args"] = args
        return "sha256:deadbeef\n"

    monkeypatch.setattr(mod, "run_regctl", fake_run_regctl)
    inspector, _ = _inspector()
    assert inspector.get_digest("1.27") == "sha256:deadbeef"
    assert captured["args"] == ["manifest", "head", "docker.io/library/nginx:1.27"]


def test_get_digest_empty_returns_none(monkeypatch) -> None:
    monkeypatch.setattr(mod, "run_regctl", lambda client, args: "  \n")
    inspector, _ = _inspector()
    assert inspector.get_digest("1.27") is None


def test_normalizes_docker_hub_host(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_regctl(client, args):
        captured["args"] = args
        return "1.0\n"

    monkeypatch.setattr(mod, "run_regctl", fake_run_regctl)
    client = create_autospec(RegistryClient, instance=True)
    client.registry = "registry-1.docker.io"
    client.repository = "library/nginx"
    RegctlImageInspector(client).list_tags()
    assert captured["args"] == ["tag", "ls", "docker.io/library/nginx"]


def test_run_regctl_registry_error_propagates(monkeypatch) -> None:
    def boom(client, args):
        raise RegistryError("regctl not found")

    monkeypatch.setattr(mod, "run_regctl", boom)
    inspector, _ = _inspector()
    with pytest.raises(RegistryError) as exc_info:
        inspector.list_tags()
    assert "regctl not found" in str(exc_info.value)


def test_translates_called_process_error(monkeypatch) -> None:
    def boom(client, args):
        raise subprocess.CalledProcessError(1, "regctl", stderr="manifest unknown")

    monkeypatch.setattr(mod, "run_regctl", boom)
    inspector, _ = _inspector()
    with pytest.raises(RegistryError):
        inspector.get_manifest("nope")


def test_translates_invalid_json(monkeypatch) -> None:
    monkeypatch.setattr(mod, "run_regctl", lambda client, args: "not json")
    inspector, _ = _inspector()
    with pytest.raises(RegistryError):
        inspector.get_manifest("1.27")
