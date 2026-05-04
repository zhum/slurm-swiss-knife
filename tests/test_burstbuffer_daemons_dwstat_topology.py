"""Tests for burstbuffer, daemons, dwstat, and topology commands."""

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


# --- burstbuffer ---


def test_burstbuffer_basic(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "Name=lustreFS1 TotalSpace=1000GiB\n"
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["burstbuffer"])
        assert result.exit_code == 0
        assert "lustreFS1" in result.output
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == ["scontrol", "burstbuffer"]


def test_burstbuffer_verbose(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["burstbuffer", "-v"])
        assert result.exit_code == 0
        assert "Running: scontrol burstbuffer" in result.output


def test_burstbuffer_dry_run(runner):
    result = runner.invoke(main, ["burstbuffer", "--dry-run"])
    assert result.exit_code == 0
    assert "DRY RUN" in result.output
    assert "scontrol burstbuffer" in result.output


def test_burstbuffer_error(runner):
    import subprocess as sp

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = sp.CalledProcessError(1, "scontrol", stderr="Error")
        result = runner.invoke(main, ["burstbuffer"])
        assert result.exit_code == 0
        assert "Error" in result.output


def test_burstbuffer_not_found(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        result = runner.invoke(main, ["burstbuffer"])
        assert result.exit_code == 0
        assert "scontrol not found" in result.output


# --- daemons ---


def test_daemons_basic(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "slurmctld slurmd\n"
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["daemons"])
        assert result.exit_code == 0
        assert "slurmctld slurmd" in result.output
        assert mock_run.call_args[0][0] == ["scontrol", "daemons"]


def test_daemons_verbose(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["daemons", "-v"])
        assert result.exit_code == 0
        assert "Running: scontrol daemons" in result.output


def test_daemons_dry_run(runner):
    result = runner.invoke(main, ["daemons", "--dry-run"])
    assert result.exit_code == 0
    assert "DRY RUN" in result.output
    assert "scontrol daemons" in result.output


def test_daemons_error(runner):
    import subprocess as sp

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = sp.CalledProcessError(1, "scontrol", stderr="Error")
        result = runner.invoke(main, ["daemons"])
        assert result.exit_code == 0
        assert "Error" in result.output


def test_daemons_not_found(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        result = runner.invoke(main, ["daemons"])
        assert result.exit_code == 0
        assert "scontrol not found" in result.output


# --- dwstat ---


def test_dwstat_basic(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "pool: id: 1 free: 800GiB\n"
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["dwstat"])
        assert result.exit_code == 0
        assert "pool" in result.output
        assert mock_run.call_args[0][0] == ["scontrol", "dwstat"]


def test_dwstat_verbose(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["dwstat", "-v"])
        assert result.exit_code == 0
        assert "Running: scontrol dwstat" in result.output


def test_dwstat_dry_run(runner):
    result = runner.invoke(main, ["dwstat", "--dry-run"])
    assert result.exit_code == 0
    assert "DRY RUN" in result.output
    assert "scontrol dwstat" in result.output


def test_dwstat_error(runner):
    import subprocess as sp

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = sp.CalledProcessError(1, "scontrol", stderr="Error")
        result = runner.invoke(main, ["dwstat"])
        assert result.exit_code == 0
        assert "Error" in result.output


def test_dwstat_not_found(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        result = runner.invoke(main, ["dwstat"])
        assert result.exit_code == 0
        assert "scontrol not found" in result.output


# --- topology ---


def test_topology_basic(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "SwitchName=s0 Switches=s1,s2\n"
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["topology"])
        assert result.exit_code == 0
        assert "SwitchName=s0" in result.output
        assert mock_run.call_args[0][0] == ["scontrol", "topology"]


def test_topology_verbose(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["topology", "-v"])
        assert result.exit_code == 0
        assert "Running: scontrol topology" in result.output


def test_topology_dry_run(runner):
    result = runner.invoke(main, ["topology", "--dry-run"])
    assert result.exit_code == 0
    assert "DRY RUN" in result.output
    assert "scontrol topology" in result.output


def test_topology_error(runner):
    import subprocess as sp

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = sp.CalledProcessError(1, "scontrol", stderr="Error")
        result = runner.invoke(main, ["topology"])
        assert result.exit_code == 0
        assert "Error" in result.output


def test_topology_not_found(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        result = runner.invoke(main, ["topology"])
        assert result.exit_code == 0
        assert "scontrol not found" in result.output
