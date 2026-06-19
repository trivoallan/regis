"""The --sarif flag is registered on analyze and evaluate."""

from click.testing import CliRunner

from regis.adapters.driving.cli.commands.analyze import analyze, evaluate_cmd


def test_analyze_help_contains_sarif_flag():
    result = CliRunner().invoke(analyze, ["--help"])
    assert result.exit_code == 0
    assert "--sarif" in result.output


def test_evaluate_help_contains_sarif_flag():
    result = CliRunner().invoke(evaluate_cmd, ["--help"])
    assert result.exit_code == 0
    assert "--sarif" in result.output
