"""SubprocessToolRunner delegates to scanner wrappers and raises ToolError."""

import pytest

from regis.adapters.driven.tools import subprocess_tool_runner as mod
from regis.adapters.driven.tools.subprocess_tool_runner import SubprocessToolRunner
from regis.core.domain.errors import AnalyzerError, ToolError
from regis.core.model.image_reference import ImageReference
from regis.core.ports.tool_runner import ToolRunner

IMAGE = ImageReference(
    registry="docker.io", repository="library/nginx", tag="1.27", platform="linux/amd64"
)


def test_is_a_tool_runner() -> None:
    assert isinstance(SubprocessToolRunner(), ToolRunner)


def test_scan_vulnerabilities_delegates_to_grype(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_grype(image, username, password, platform):
        captured.update(
            image=image, username=username, password=password, platform=platform
        )
        return {"matches": []}

    monkeypatch.setattr(mod, "run_grype", fake_run_grype)
    runner = SubprocessToolRunner("alice", "s3cret")
    assert runner.scan_vulnerabilities(IMAGE) == {"matches": []}
    assert captured == {
        "image": "docker.io/library/nginx:1.27",
        "username": "alice",
        "password": "s3cret",
        "platform": "linux/amd64",
    }


def test_generate_sbom_delegates_to_syft(monkeypatch) -> None:
    monkeypatch.setattr(
        mod,
        "run_syft",
        lambda image, username, password, platform: {"bomFormat": "CycloneDX"},
    )
    assert SubprocessToolRunner().generate_sbom(IMAGE) == {"bomFormat": "CycloneDX"}


def test_scan_secrets_delegates_to_trufflehog_without_platform(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_trufflehog(image, username, password):
        captured.update(image=image, username=username, password=password)
        return [{"DetectorName": "AWS"}]

    monkeypatch.setattr(mod, "run_trufflehog", fake_run_trufflehog)
    assert SubprocessToolRunner("u", "p").scan_secrets(IMAGE) == [
        {"DetectorName": "AWS"}
    ]
    assert captured == {
        "image": "docker.io/library/nginx:1.27",
        "username": "u",
        "password": "p",
    }


def test_scanner_translates_analyzer_error_to_tool_error(monkeypatch) -> None:
    def boom(*args, **kwargs):
        raise AnalyzerError("grype failed: boom")

    monkeypatch.setattr(mod, "run_grype", boom)
    with pytest.raises(ToolError) as exc_info:
        SubprocessToolRunner().scan_vulnerabilities(IMAGE)
    assert "grype failed: boom" in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, AnalyzerError)
