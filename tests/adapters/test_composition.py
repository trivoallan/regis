"""Tests for the CLI composition root."""

from __future__ import annotations

from regis.adapters.driven.registry.regctl_image_inspector import RegctlImageInspector
from regis.adapters.driven.tools.subprocess_tool_runner import SubprocessToolRunner
from regis.adapters.driving.cli.composition import build_analyze_image
from regis.core.application.analyze_image import AnalyzeImage
from regis.core.model.image_reference import ImageReference
from regis.registry.client import RegistryClient

IMAGE = ImageReference(registry="reg.example", repository="ns/app", tag="1.0")


def test_build_returns_wired_analyze_image():
    uc = build_analyze_image("user", "pass")
    assert isinstance(uc, AnalyzeImage)
    assert isinstance(uc._tools, SubprocessToolRunner)


def test_inspector_factory_builds_regctl_inspector_for_image():
    uc = build_analyze_image("user", "pass")
    inspector = uc._inspector_factory(IMAGE)
    assert isinstance(inspector, RegctlImageInspector)


def test_legacy_client_factory_builds_registry_client_with_repo_and_creds():
    uc = build_analyze_image("user", "pass")
    client = uc._legacy_client_factory(IMAGE)
    assert isinstance(client, RegistryClient)
    assert client.registry == "reg.example"
    assert client.repository == "ns/app"
    assert client.username == "user"
    assert client.password == "pass"


def test_creds_may_be_none():
    uc = build_analyze_image(None, None)
    client = uc._legacy_client_factory(IMAGE)
    assert client.username is None and client.password is None
