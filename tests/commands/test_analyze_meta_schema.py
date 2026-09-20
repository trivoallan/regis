"""Metadata validation as a checkpoint: --meta-schema, exit code 3, provenance.

Exit-code contract exercised here:

- ``3`` — the call is malformed: metadata violates a schema, and at least one schema
  source beyond the well-known one was in force. Independent of ``--fail``.
- ``1`` — the image was refused by the rules (``--fail``), or regis could not run.
- unchanged — a well-known violation with no schema source in force (compatibility).
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from regis.adapters.driving.cli.commands.analyze import analyze
from regis.core.domain.analyzers.base import BaseAnalyzer

_PLAYBOOK_DOC = """apiVersion: regis.io/v1alpha1
kind: Playbook
metadata:
  name: p
  labels:
    app.kubernetes.io/version: "1.0.0"
spec: {}
"""


class _DummyAnalyzer(BaseAnalyzer):
    name = "dummy"

    def analyze(self, ctx=None):
        return {"analyzer": "dummy"}

    def validate(self, report):
        pass


def _report(
    *, valid=True, sources=(), invalid_field=None, rules=(), enforcement="enforcing"
):
    validation = {}
    if invalid_field:
        validation[invalid_field] = {
            "valid": False,
            "error": f"'{invalid_field}' is a required property",
        }
    return {
        "request": {
            "registry": "registry-1.docker.io",
            "repository": "library/nginx",
            "tag": "latest",
            "digest": "sha256-abc",
            "timestamp": "2026-09-20T10:00:00+00:00",
            "analyzers": ["dummy", "metadata"],
        },
        "results": {
            "dummy": {"analyzer": "dummy"},
            "metadata": {
                "analyzer": "metadata",
                "metadata": {},
                "metadata_validation": validation,
                "valid": valid,
                "schema_sources": [str(s) for s in sources],
                "enforcement": enforcement,
            },
        },
        "rules": list(rules),
        "playbooks": [],
    }


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def mock_infra():
    """Patch the registry and the use-case; the report is supplied per test."""
    from regis.core.application.analyze_image import AnalysisResult

    client = MagicMock()
    client.get_digest.return_value = "sha256:abc"
    use_case = MagicMock()

    def _set(report, *, breaches=0):
        use_case.run_and_evaluate.return_value = AnalysisResult(
            report=report,
            has_breaches=breaches > 0,
            breach_count=breaches,
            breached_slugs=["r"] * breaches,
        )

    with (
        patch(
            "regis.adapters.driving.cli.commands.analyze.RegistryClient",
            return_value=client,
        ),
        patch(
            "regis.adapters.driving.cli.commands.analyze._discover_analyzers",
            return_value={"dummy": _DummyAnalyzer},
        ),
        patch(
            "regis.adapters.driving.cli.commands.analyze.build_analyze_image",
            return_value=use_case,
        ),
    ):
        yield {"use_case": use_case, "set_report": _set}


def _schema(path: Path, field: str) -> Path:
    path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "required": [field],
                "properties": {field: {"type": "string"}},
            }
        ),
        encoding="utf-8",
    )
    return path


def _bundle(root: Path, field: str | None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "playbook.yaml").write_text(
        _PLAYBOOK_DOC,
        encoding="utf-8",
    )
    if field:
        _schema(root / "meta.schema.json", field)
    return root


class TestMetaSchemaOption:
    """--meta-schema accepts local paths and reaches the use-case."""

    def test_explicit_schema_is_forwarded(self, runner, tmp_path, mock_infra):
        mock_infra["set_report"](_report())
        schema = _schema(tmp_path / "saisine.schema.json", "SAISINE_URL")

        result = runner.invoke(
            analyze,
            [
                "nginx:latest",
                "--meta-schema",
                str(schema),
                "--output-dir",
                str(tmp_path / "out"),
            ],
        )

        assert result.exit_code == 0, result.output
        kwargs = mock_infra["use_case"].run_and_evaluate.call_args.kwargs
        assert list(kwargs["meta_schema_paths"]) == [schema]

    def test_bundle_schema_is_forwarded(self, runner, tmp_path, mock_infra):
        mock_infra["set_report"](_report())
        bundle = _bundle(tmp_path / "regime", "SAISINE_URL")

        result = runner.invoke(
            analyze,
            [
                "nginx:latest",
                "-p",
                str(bundle),
                "--output-dir",
                str(tmp_path / "out"),
            ],
        )

        assert result.exit_code == 0, result.output
        kwargs = mock_infra["use_case"].run_and_evaluate.call_args.kwargs
        assert list(kwargs["meta_schema_paths"]) == [bundle / "meta.schema.json"]

    def test_bundle_and_explicit_schemas_stack_in_order(
        self, runner, tmp_path, mock_infra
    ):
        mock_infra["set_report"](_report())
        bundle = _bundle(tmp_path / "regime", "PROJECT_ID")
        schema = _schema(tmp_path / "saisine.schema.json", "SAISINE_URL")

        result = runner.invoke(
            analyze,
            [
                "nginx:latest",
                "-p",
                str(bundle),
                "--meta-schema",
                str(schema),
                "--output-dir",
                str(tmp_path / "out"),
            ],
        )

        assert result.exit_code == 0, result.output
        kwargs = mock_infra["use_case"].run_and_evaluate.call_args.kwargs
        assert list(kwargs["meta_schema_paths"]) == [
            bundle / "meta.schema.json",
            schema,
        ]

    def test_missing_schema_path_is_a_usage_error(self, runner, tmp_path, mock_infra):
        mock_infra["set_report"](_report())
        result = runner.invoke(
            analyze,
            ["nginx:latest", "--meta-schema", str(tmp_path / "nope.json")],
        )
        assert result.exit_code == 2


class TestMalformedCallExitCode:
    """Exit 3 when a schema source is in force and metadata violates it."""

    def test_invalid_metadata_exits_three(self, runner, tmp_path, mock_infra):
        schema = _schema(tmp_path / "s.json", "SAISINE_URL")
        mock_infra["set_report"](
            _report(valid=False, sources=[schema], invalid_field="SAISINE_URL")
        )

        result = runner.invoke(
            analyze,
            [
                "nginx:latest",
                "--fail",
                "--evaluate",
                "--meta-schema",
                str(schema),
                "--output-dir",
                str(tmp_path / "out"),
            ],
        )

        assert result.exit_code == 3, result.output
        assert "SAISINE_URL" in result.output
        assert str(schema) in result.output

    def test_exit_three_does_not_need_fail(self, runner, tmp_path, mock_infra):
        """--fail governs the verdict on the image, not the shape of the call."""
        schema = _schema(tmp_path / "s.json", "SAISINE_URL")
        mock_infra["set_report"](
            _report(valid=False, sources=[schema], invalid_field="SAISINE_URL")
        )

        result = runner.invoke(
            analyze,
            [
                "nginx:latest",
                "--meta-schema",
                str(schema),
                "--output-dir",
                str(tmp_path / "out"),
            ],
        )

        assert result.exit_code == 3, result.output

    def test_exit_three_wins_over_a_rule_breach(self, runner, tmp_path, mock_infra):
        schema = _schema(tmp_path / "s.json", "SAISINE_URL")
        mock_infra["set_report"](
            _report(valid=False, sources=[schema], invalid_field="SAISINE_URL"),
            breaches=2,
        )

        result = runner.invoke(
            analyze,
            [
                "nginx:latest",
                "--fail",
                "--evaluate",
                "--meta-schema",
                str(schema),
                "--output-dir",
                str(tmp_path / "out"),
            ],
        )

        assert result.exit_code == 3, result.output

    def test_valid_metadata_with_schema_exits_zero(self, runner, tmp_path, mock_infra):
        schema = _schema(tmp_path / "s.json", "SAISINE_URL")
        mock_infra["set_report"](_report(valid=True, sources=[schema]))

        result = runner.invoke(
            analyze,
            [
                "nginx:latest",
                "--meta-schema",
                str(schema),
                "--output-dir",
                str(tmp_path / "out"),
            ],
        )

        assert result.exit_code == 0, result.output


class TestPreservedBehaviourWithoutSchemaSource:
    """A caller with no schema source keeps today's exit codes."""

    def test_well_known_violation_warns_but_does_not_fail(
        self, runner, tmp_path, mock_infra
    ):
        mock_infra["set_report"](
            _report(valid=False, sources=[], invalid_field="ci.platform")
        )

        result = runner.invoke(
            analyze,
            [
                "nginx:latest",
                "-m",
                "ci.platform=jenkins",
                "--output-dir",
                str(tmp_path / "out"),
            ],
        )

        assert result.exit_code == 0, result.output
        assert "ci.platform" in result.output

    def test_file_playbook_with_meta_warns_about_no_schema(
        self, runner, tmp_path, mock_infra
    ):
        mock_infra["set_report"](_report(valid=True, sources=[]))
        playbook = tmp_path / "playbook.yaml"
        playbook.write_text(
            _PLAYBOOK_DOC,
            encoding="utf-8",
        )

        result = runner.invoke(
            analyze,
            [
                "nginx:latest",
                "-p",
                str(playbook),
                "-m",
                "SAISINE_URL=https://x.example/c",
                "--output-dir",
                str(tmp_path / "out"),
            ],
        )

        assert result.exit_code == 0, result.output
        assert "playbook.yaml" in result.output
        assert "not a bundle" in result.output
        kwargs = mock_infra["use_case"].run_and_evaluate.call_args.kwargs
        assert list(kwargs["meta_schema_paths"]) == []

    def test_bundle_without_schema_does_not_warn(self, runner, tmp_path, mock_infra):
        mock_infra["set_report"](_report(valid=True, sources=[]))
        bundle = _bundle(tmp_path / "regime", None)

        result = runner.invoke(
            analyze,
            [
                "nginx:latest",
                "-p",
                str(bundle),
                "-m",
                "SAISINE_URL=https://x.example/c",
                "--output-dir",
                str(tmp_path / "out"),
            ],
        )

        assert result.exit_code == 0, result.output
        assert "not a bundle" not in result.output


class TestRerunMetadata:
    """--rerun metadata honours --meta-schema and the same exit code."""

    _EXISTING = {
        "version": "0.1.0",
        "request": {
            "registry": "r",
            "repository": "repo",
            "tag": "latest",
            "timestamp": "2026-09-20T00:00:00+00:00",
        },
        "results": {},
    }

    def _run(self, runner, tmp_path, args):
        report_dir = tmp_path / "rpt"
        report_dir.mkdir()
        (report_dir / "report.json").write_text(
            json.dumps(self._EXISTING), encoding="utf-8"
        )
        with (
            patch("regis.adapters.driving.cli.commands.analyze.validate_report"),
            patch(
                "regis.adapters.driving.cli.commands.analyze._discover_analyzers",
                return_value={"dummy": _DummyAnalyzer},
            ),
        ):
            result = runner.invoke(
                analyze,
                ["--rerun", "metadata", "--report", str(report_dir), *args],
            )
        return result, json.loads((report_dir / "report.json").read_text())

    def test_rerun_missing_required_field_exits_three(self, runner, tmp_path):
        schema = _schema(tmp_path / "s.json", "SAISINE_URL")
        result, report = self._run(
            runner, tmp_path, ["--meta-schema", str(schema), "-m", "PROJECT_ID=P-1"]
        )

        assert result.exit_code == 3, result.output
        meta = report["results"]["metadata"]
        assert meta["valid"] is False
        assert meta["metadata_validation"]["SAISINE_URL"]["valid"] is False
        assert meta["schema_sources"] == [str(schema)]

    def test_rerun_with_the_field_exits_zero(self, runner, tmp_path):
        schema = _schema(tmp_path / "s.json", "SAISINE_URL")
        result, report = self._run(
            runner,
            tmp_path,
            ["--meta-schema", str(schema), "-m", "SAISINE_URL=https://x.example/c"],
        )

        assert result.exit_code == 0, result.output
        assert report["results"]["metadata"]["valid"] is True

    def test_rerun_without_schema_keeps_today_behaviour(self, runner, tmp_path):
        result, report = self._run(runner, tmp_path, ["-m", "ci.platform=jenkins"])

        assert result.exit_code == 0, result.output
        assert report["results"]["metadata"]["valid"] is False
        assert report["results"]["metadata"]["schema_sources"] == []


class TestAdvisoryDerogation:
    """--meta-advisory suspends the sanction; it never hides the finding."""

    def test_advisory_exits_zero_but_still_reports(self, runner, tmp_path, mock_infra):
        schema = _schema(tmp_path / "s.json", "SAISINE_URL")
        mock_infra["set_report"](
            _report(
                valid=False,
                sources=[schema],
                invalid_field="SAISINE_URL",
                enforcement="advisory",
            )
        )

        result = runner.invoke(
            analyze,
            [
                "nginx:latest",
                "--meta-schema",
                str(schema),
                "--meta-advisory",
                "--output-dir",
                str(tmp_path / "out"),
            ],
        )

        assert result.exit_code == 0, result.output
        # The suspended sanction stays loud: the failing field is still named.
        assert "SAISINE_URL" in result.output
        assert "advisory" in result.output
        kwargs = mock_infra["use_case"].run_and_evaluate.call_args.kwargs
        assert kwargs["meta_advisory"] is True

    def test_advisory_via_environment(self, runner, tmp_path, mock_infra):
        schema = _schema(tmp_path / "s.json", "SAISINE_URL")
        mock_infra["set_report"](
            _report(
                valid=False,
                sources=[schema],
                invalid_field="SAISINE_URL",
                enforcement="advisory",
            )
        )

        result = runner.invoke(
            analyze,
            [
                "nginx:latest",
                "--meta-schema",
                str(schema),
                "--output-dir",
                str(tmp_path / "out"),
            ],
            env={"REGIS_META_ADVISORY": "1"},
        )

        assert result.exit_code == 0, result.output
        kwargs = mock_infra["use_case"].run_and_evaluate.call_args.kwargs
        assert kwargs["meta_advisory"] is True

    def test_enforcing_is_the_default(self, runner, tmp_path, mock_infra):
        """Non-regression: without the derogation the sanction still applies."""
        schema = _schema(tmp_path / "s.json", "SAISINE_URL")
        mock_infra["set_report"](
            _report(valid=False, sources=[schema], invalid_field="SAISINE_URL")
        )

        result = runner.invoke(
            analyze,
            [
                "nginx:latest",
                "--meta-schema",
                str(schema),
                "--output-dir",
                str(tmp_path / "out"),
            ],
        )

        assert result.exit_code == 3, result.output
        kwargs = mock_infra["use_case"].run_and_evaluate.call_args.kwargs
        assert kwargs["meta_advisory"] is False

    def test_advisory_does_not_mask_a_rule_breach(self, runner, tmp_path, mock_infra):
        """The derogation covers the metadata contract only, never the verdict."""
        schema = _schema(tmp_path / "s.json", "SAISINE_URL")
        mock_infra["set_report"](
            _report(
                valid=False,
                sources=[schema],
                invalid_field="SAISINE_URL",
                enforcement="advisory",
            ),
            breaches=2,
        )

        result = runner.invoke(
            analyze,
            [
                "nginx:latest",
                "--fail",
                "--evaluate",
                "--meta-schema",
                str(schema),
                "--meta-advisory",
                "--output-dir",
                str(tmp_path / "out"),
            ],
        )

        assert result.exit_code == 1, result.output


class TestRerunAdvisory:
    """The derogation is available on the rerun path too, and recorded there."""

    def test_rerun_advisory_exits_zero_and_records(self, runner, tmp_path):
        schema = _schema(tmp_path / "s.json", "SAISINE_URL")
        result, report = TestRerunMetadata()._run(
            runner,
            tmp_path,
            ["--meta-schema", str(schema), "--meta-advisory", "-m", "PROJECT_ID=P-1"],
        )

        assert result.exit_code == 0, result.output
        meta = report["results"]["metadata"]
        assert meta["enforcement"] == "advisory"
        assert meta["valid"] is False
        assert meta["metadata_validation"]["SAISINE_URL"]["valid"] is False
