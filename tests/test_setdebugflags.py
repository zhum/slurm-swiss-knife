"""Tests for the setdebugflags command."""

from unittest.mock import patch

import pytest

from slurm_cli.cli import main


@pytest.fixture
def runner():
    from click.testing import CliRunner

    return CliRunner()


@pytest.fixture(autouse=True)
def register():
    from slurm_cli.cli import register_commands

    register_commands()


def test_setdebugflags_enable_flag(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["setdebugflags", "+Backfill"])
        assert result.exit_code == 0
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == [
            "scontrol",
            "setdebugflags",
            "+Backfill",
        ]


def test_setdebugflags_disable_flag(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["setdebugflags", "-Agent"])
        assert result.exit_code == 0
        assert mock_run.call_args[0][0] == [
            "scontrol",
            "setdebugflags",
            "-Agent",
        ]


def test_setdebugflags_multiple_flags(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["setdebugflags", "+Backfill", "+Agent", "-Gang"])
        assert result.exit_code == 0
        cmd = mock_run.call_args[0][0]
        assert cmd == [
            "scontrol",
            "setdebugflags",
            "+Backfill",
            "+Agent",
            "-Gang",
        ]


def test_setdebugflags_case_insensitive(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["setdebugflags", "+backfill"])
        assert result.exit_code == 0
        cmd = mock_run.call_args[0][0]
        assert "+Backfill" in cmd


def test_setdebugflags_with_nodes(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["setdebugflags", "+Backfill", "nodes=node001"])
        assert result.exit_code == 0
        cmd = mock_run.call_args[0][0]
        assert "+Backfill" in cmd
        assert "nodes=node001" in cmd


def test_setdebugflags_dry_run(runner):
    result = runner.invoke(main, ["setdebugflags", "--dry-run", "+Backfill"])
    assert result.exit_code == 0
    assert "DRY RUN" in result.output
    assert "scontrol setdebugflags +Backfill" in result.output


def test_setdebugflags_verbose(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["setdebugflags", "-v", "+Backfill"])
        assert result.exit_code == 0
        assert "Running: scontrol setdebugflags" in result.output


def test_setdebugflags_invalid_flag(runner):
    result = runner.invoke(main, ["setdebugflags", "+NotAFlag"])
    assert result.exit_code == 0
    assert "Unknown flag" in result.output or "Error" in result.output


def test_setdebugflags_missing_prefix(runner):
    result = runner.invoke(main, ["setdebugflags", "Backfill"])
    assert result.exit_code == 0
    assert "+" in result.output or "-" in result.output or "Error" in result.output


def test_setdebugflags_sdf_alias(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["sdf", "+Backfill"])
        assert result.exit_code == 0
        assert mock_run.call_args[0][0] == [
            "scontrol",
            "setdebugflags",
            "+Backfill",
        ]


def test_setdebugflags_error(runner):
    import subprocess as sp

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = sp.CalledProcessError(1, "scontrol", stderr="Error")
        result = runner.invoke(main, ["setdebugflags", "+Backfill"])
        assert result.exit_code == 0
        assert "Error" in result.output


def test_setdebugflags_not_found(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        result = runner.invoke(main, ["setdebugflags", "+Backfill"])
        assert result.exit_code == 0
        assert "scontrol not found" in result.output


def test_setdebugflags_all_valid_flags(runner):
    """Verify all documented flags are accepted."""
    from slurm_cli.cli import SETDEBUGFLAGS_FLAGS

    for flag in SETDEBUGFLAGS_FLAGS:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = ""
            mock_run.return_value.returncode = 0
            result = runner.invoke(main, ["setdebugflags", f"+{flag}"])
            assert result.exit_code == 0, f"Flag +{flag} failed: {result.output}"
            cmd = mock_run.call_args[0][0]
            assert f"+{flag}" in cmd
