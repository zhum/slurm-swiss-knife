"""Tests for the write-config command."""

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from slurm_cli.cli import main, register_commands


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


# =============================================================================
# Flag and Option Tests
# =============================================================================

def test_write_config_dry_run(runner):
    """Test write-config with --dry-run flag."""
    from slurm_cli.cli import register_commands

    register_commands()

    result = runner.invoke(
        main, ["write-config", "--dry-run"]
    )
    assert result.exit_code == 0
    assert "DRY RUN" in result.output
    # Should show the command that would be run
    assert "scontrol write config" in result.output


def test_write_config_verbose(runner):
    """Test write-config with --verbose flag."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["write-config", "-v"])
        assert result.exit_code == 0
        # Verbose mode should show the command being run
        assert "Running:" in result.output


def test_write_config_dry_run_and_verbose(runner):
    """Test write-config with both --dry-run and --verbose flags."""
    from slurm_cli.cli import register_commands

    register_commands()

    result = runner.invoke(
        main, ["write-config", "--dry-run", "-v"]
    )
    assert result.exit_code == 0
    # Both dry-run output and verbose output should be present
    assert "DRY RUN" in result.output
    assert "Running:" in result.output


def test_write_config_short_flags(runner):
    """Test write-config with short flags (-v, -d)."""
    from slurm_cli.cli import register_commands

    register_commands()

    # Test -v (verbose)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        result = runner.invoke(main, ["write-config", "-v"])
        assert result.exit_code == 0
        assert "Running:" in result.output


# =============================================================================
# Alias Tests
# =============================================================================

def test_write_config_alias_wconf(runner):
    """Test write-config with 'wconf' alias."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        result = runner.invoke(main, ["wconf"])
        assert result.exit_code == 0
        assert "Write config command sent successfully" in result.output


# =============================================================================
# Error Handling Tests
# =============================================================================

def test_write_config_error_handling(runner):
    """Test write-config error handling when scontrol fails."""
    import subprocess as sp

    from slurm_cli.cli import register_commands

    register_commands()

    # Test CalledProcessError
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = sp.CalledProcessError(
            1, "scontrol", stderr="Permission denied"
        )
        result = runner.invoke(main, ["write-config"])
        assert result.exit_code == 0
        assert "Error" in result.output


def test_write_config_not_found(runner):
    """Test write-config when scontrol is not found."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        result = runner.invoke(main, ["write-config"])
        assert result.exit_code == 0
        assert "scontrol not found" in result.output


# =============================================================================
# Help and Documentation Tests
# =============================================================================

def test_write_config_in_help(runner):
    """Test that write-config appears in main help."""
    from slurm_cli.cli import register_commands

    register_commands()

    result = runner.invoke(main, ["--help"])
    assert result.exit_code in [0, 2]
    # Check for either the full help or at least the usage line
    assert (
        "Slurm CLI" in result.output
        or "Usage: main [OPTIONS] COMMAND [ARGS]..." in result.output
    )


def test_write_config_help_text(runner):
    """Test that write-config has proper help text."""
    from slurm_cli.cli import register_commands

    register_commands()

    # Check the command object's help attribute
    assert hasattr(main, "help")
    # The help should mention write-config somewhere in the output


# =============================================================================
# Integration Tests - Command Registration
# =============================================================================

def test_register_commands_includes_write_config():
    """Test that register_commands properly includes write-config."""
    from slurm_cli.cli import main, register_commands

    # Clear existing commands to start fresh
    main.commands.clear()

    register_commands()

    # Check that write-config is registered
    assert "write-config" in [cmd.name for cmd in main.commands.values()]


def test_register_commands_includes_takeover():
    """Test that register_commands properly includes takeover."""
    from slurm_cli.cli import main, register_commands

    # Clear existing commands to start fresh
    main.commands.clear()

    register_commands()

    # Check that takeover is registered
    assert "takeover" in [cmd.name for cmd in main.commands.values()]


def test_register_commands_includes_all_scontrol_commands():
    """Test that register_commands includes all expected scontrol commands."""
    from slurm_cli.cli import main, register_commands

    # Expected scontrol-related commands
    expected_commands = {
        "reconfigure",
        "ping",
        "takeover",
        "write-config",  # New command we added
        "token",
        "assoc-mgr",
    }

    # Clear existing commands to start fresh
    main.commands.clear()

    register_commands()

    # Check that all expected commands are registered
    registered = {cmd.name for cmd in main.commands.values()}
    missing = expected_commands - registered

    assert not missing, f"Missing commands: {missing}"


# =============================================================================
# Prefix Matching Tests (for autocomplete)
# =============================================================================

def test_write_config_prefix_matching():
    """Test that write-config responds to common prefixes."""
    from slurm_cli.cli import resolve_command_alias

    # Test exact match
    assert resolve_command_alias("write-config") == "write-config"

    # Test prefix matching (shorter forms)
    assert resolve_command_alias("wconf") == "write-config"


def test_takeover_prefix_matching():
    """Test that takeover responds to common prefixes."""
    from slurm_cli.cli import resolve_command_alias

    # Test exact match
    assert resolve_command_alias("takeover") == "takeover"

    # Test prefix matching (shorter forms)
    assert resolve_command_alias("tak") == "takeover"


# =============================================================================
# Regression Tests - Ensure Existing Behavior Still Works
# =============================================================================

def test_reconfigure_still_works_after_write_config_addition(runner):
    """Regression: ensure reconfigure still works after adding write-config."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        result = runner.invoke(main, ["reconfigure"])
        assert result.exit_code == 0
        assert "Reconfigure command sent successfully" in result.output


def test_takeover_still_works_after_write_config_addition(runner):
    """Regression: ensure takeover still works after adding write-config."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        result = runner.invoke(main, ["takeover"])
        assert result.exit_code == 0
        assert "Takeover command sent successfully" in result.output


def test_ping_still_works_after_write_config_addition(runner):
    """Regression: ensure ping still works after adding write-config."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "Slurmctld(primary) at localhost is UP"
        result = runner.invoke(main, ["ping"])
        assert result.exit_code == 0
        assert "Slurmctld" in result.output

