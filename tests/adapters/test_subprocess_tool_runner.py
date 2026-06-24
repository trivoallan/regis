"""SubprocessToolRunner delegates to scanner wrappers and raises ToolError."""

from types import SimpleNamespace

import pytest

from regis.adapters.driven.tools import subprocess_tool_runner as mod
from regis.adapters.driven.tools.subprocess_tool_runner import SubprocessToolRunner
from regis.core.domain.errors import ToolError
from regis.core.model.image_reference import ImageReference
from regis.core.ports.tool_runner import ToolResult, ToolRunner

IMAGE = ImageReference(
    registry="docker.io", repository="library/nginx", tag="1.27", platform="linux/amd64"
)


def test_is_a_tool_runner() -> None:
    assert isinstance(SubprocessToolRunner(), ToolRunner)


def test_full_ref_uses_at_separator_for_digest(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_grype(image, username, password, platform):
        captured["image"] = image
        return {"matches": []}

    monkeypatch.setattr(mod, "run_grype", fake_run_grype)
    digest_image = ImageReference(
        registry="docker.io",
        repository="library/nginx",
        tag="sha256:" + "a" * 64,
        platform="linux/amd64",
    )
    SubprocessToolRunner().scan_vulnerabilities(digest_image)
    assert captured["image"] == f"docker.io/library/nginx@sha256:{'a' * 64}"


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
    captured: dict[str, object] = {}

    def fake_run_syft(image, username, password, platform):
        captured.update(
            image=image, username=username, password=password, platform=platform
        )
        return {"bomFormat": "CycloneDX"}

    monkeypatch.setattr(mod, "run_syft", fake_run_syft)
    runner = SubprocessToolRunner("alice", "s3cret")
    assert runner.generate_sbom(IMAGE) == {"bomFormat": "CycloneDX"}
    assert captured == {
        "image": "docker.io/library/nginx:1.27",
        "username": "alice",
        "password": "s3cret",
        "platform": "linux/amd64",
    }


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


def test_scanner_raises_tool_error_directly(monkeypatch) -> None:
    def boom(*args, **kwargs):
        raise ToolError("grype failed: boom")

    monkeypatch.setattr(mod, "run_grype", boom)
    with pytest.raises(ToolError) as exc_info:
        SubprocessToolRunner().scan_vulnerabilities(IMAGE)
    assert "grype failed: boom" in str(exc_info.value)


def test_lint_dockerfile_parses_issue_list(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["input"] = kwargs.get("input")
        return SimpleNamespace(stdout='[{"code": "DL3008"}]', stderr="", returncode=1)

    monkeypatch.setattr(mod, "ensure_tool", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    assert SubprocessToolRunner().lint_dockerfile("FROM scratch") == [
        {"code": "DL3008"}
    ]
    assert captured["cmd"] == ["/usr/bin/hadolint", "-f", "json", "-"]
    assert captured["input"] == "FROM scratch"


def test_lint_dockerfile_empty_output_is_empty_list(monkeypatch) -> None:
    monkeypatch.setattr(mod, "ensure_tool", lambda name: "/usr/bin/hadolint")
    monkeypatch.setattr(
        mod.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout="  \n", stderr="", returncode=0),
    )
    assert SubprocessToolRunner().lint_dockerfile("FROM scratch") == []


def test_lint_dockerfile_invalid_json_raises_tool_error(monkeypatch) -> None:
    monkeypatch.setattr(mod, "ensure_tool", lambda name: "/usr/bin/hadolint")
    monkeypatch.setattr(
        mod.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout="not json", stderr="", returncode=0),
    )
    with pytest.raises(ToolError):
        SubprocessToolRunner().lint_dockerfile("FROM scratch")


def test_lint_dockerfile_missing_tool_raises_tool_error(monkeypatch) -> None:
    def boom(name):
        raise ToolError("hadolint not available")

    monkeypatch.setattr(mod, "ensure_tool", boom)
    with pytest.raises(ToolError):
        SubprocessToolRunner().lint_dockerfile("FROM scratch")


def test_audit_image_parses_report_and_injects_creds(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["env"] = kwargs.get("env")
        return SimpleNamespace(
            stdout='{"summary": {"fatal": 0}, "details": []}', stderr="", returncode=0
        )

    monkeypatch.setattr(mod, "ensure_tool", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    result = SubprocessToolRunner("alice", "s3cret").audit_image(IMAGE)
    assert result == {"summary": {"fatal": 0}, "details": []}
    assert captured["cmd"] == [
        "/usr/bin/dockle",
        "-f",
        "json",
        "docker.io/library/nginx:1.27",
    ]
    assert captured["env"]["DOCKER_USER"] == "alice"
    assert captured["env"]["DOCKER_PASSWORD"] == "s3cret"


def test_audit_image_no_creds_omits_docker_env(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(cmd, **kwargs):
        captured["env"] = kwargs.get("env")
        return SimpleNamespace(stdout='{"summary": {}}', stderr="", returncode=0)

    monkeypatch.setattr(mod, "ensure_tool", lambda name: "/usr/bin/dockle")
    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    SubprocessToolRunner().audit_image(IMAGE)
    assert "DOCKER_USER" not in captured["env"]
    assert "DOCKER_PASSWORD" not in captured["env"]


def test_audit_image_no_output_raises_tool_error(monkeypatch) -> None:
    monkeypatch.setattr(mod, "ensure_tool", lambda name: "/usr/bin/dockle")
    monkeypatch.setattr(
        mod.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(
            stdout="", stderr="connection refused", returncode=1
        ),
    )
    with pytest.raises(ToolError) as exc_info:
        SubprocessToolRunner().audit_image(IMAGE)
    assert "connection refused" in str(exc_info.value)


def test_audit_image_missing_tool_raises_tool_error(monkeypatch) -> None:
    def boom(name):
        raise ToolError("dockle not available")

    monkeypatch.setattr(mod, "ensure_tool", boom)
    with pytest.raises(ToolError) as exc_info:
        SubprocessToolRunner().audit_image(IMAGE)
    assert "dockle not available" in str(exc_info.value)


def test_audit_image_invalid_json_raises_tool_error(monkeypatch) -> None:
    monkeypatch.setattr(mod, "ensure_tool", lambda name: "/usr/bin/dockle")
    monkeypatch.setattr(
        mod.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout="not json", stderr="", returncode=0),
    )
    with pytest.raises(ToolError):
        SubprocessToolRunner().audit_image(IMAGE)


def test_run_returns_tool_result_with_exit_code(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["timeout"] = kwargs.get("timeout")
        return SimpleNamespace(stdout="out", stderr="err", returncode=3)

    monkeypatch.setattr(mod, "ensure_tool", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    result = SubprocessToolRunner().run("cosign", ["version"], timeout=5)
    assert result == ToolResult(stdout="out", stderr="err", exit_code=3)
    assert captured["cmd"] == ["/usr/bin/cosign", "version"]
    assert captured["timeout"] == 5


def test_run_missing_tool_raises_tool_error(monkeypatch) -> None:
    def boom(name):
        raise ToolError("cosign not available")

    monkeypatch.setattr(mod, "ensure_tool", boom)
    with pytest.raises(ToolError) as exc_info:
        SubprocessToolRunner().run("cosign", ["version"])
    assert "cosign not available" in str(exc_info.value)


def test_run_timeout_raises_tool_error(monkeypatch) -> None:
    monkeypatch.setattr(mod, "ensure_tool", lambda name: "/usr/bin/cosign")

    def boom(*a, **k):
        raise mod.subprocess.TimeoutExpired(cmd="cosign", timeout=5)

    monkeypatch.setattr(mod.subprocess, "run", boom)
    with pytest.raises(ToolError) as exc_info:
        SubprocessToolRunner().run("cosign", ["version"], timeout=5)
    assert "cosign timed out" in str(exc_info.value)
