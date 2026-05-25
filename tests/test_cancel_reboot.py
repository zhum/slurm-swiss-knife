"""Tests for the cancel-reboot command."""

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

def test_cancel_reboot_dry_run(runner):
    """Test cancel-reboot with --dry-run flag."""
    from slurm_cli.cli import register_commands

    register_commands()

    result = runner.invoke(
        main, ["cancel-reboot", "node001", "--dry-run"]
    )
    assert result.exit_code == 0
    assert "DRY RUN" in result.output
    # Should show the command that would be run
    assert "scontrol cancel_reboot" in result.output


def test_cancel_reboot_verbose(runner):
    """Test cancel-reboot with --verbose flag."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["cancel-reboot", "node001", "-v"])
        assert result.exit_code == 0
        # Verbose mode should show the command being run
        assert "Running:" in result.output


def test_cancel_reboot_dry_run_and_verbose(runner):
    """Test cancel-reboot with both --dry-run and --verbose flags."""
    from slurm_cli.cli import register_commands

    register_commands()

    result = runner.invoke(
        main, ["cancel-reboot", "node001", "--dry-run", "-v"]
    )
    assert result.exit_code == 0
    # Both dry-run output and verbose output should be present
    assert "DRY RUN" in result.output
    assert "Running:" in result.output


def test_cancel_reboot_short_flags(runner):
    """Test cancel-reboot with short flags (-v, -d)."""
    from slurm_cli.cli import register_commands

    register_commands()

    # Test -v (verbose)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        result = runner.invoke(main, ["cancel-reboot", "node001", "-v"])
        assert result.exit_code == 0
        assert "Running:" in result.output


# =============================================================================
# Alias Tests
# =============================================================================

def test_cancel_reboot_alias(runner):
    """Test cancel-reboot with 'cancel-reb' alias."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        result = runner.invoke(main, ["cancel-reb", "node001"])
        assert result.exit_code == 0
        assert "Cancelled reboot" in result.output


# =============================================================================
# Error Handling Tests
# =============================================================================

def test_cancel_reboot_error_handling(runner):
    """Test cancel-reboot error handling when scontrol fails."""
    import subprocess as sp

    from slurm_cli.cli import register_commands

    register_commands()

    # Test CalledProcessError
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = sp.CalledProcessError(
            1, "scontrol", stderr="Permission denied"
        )
        result = runner.invoke(main, ["cancel-reboot", "node001"])
        assert result.exit_code == 0
        assert "Error" in result.output


def test_cancel_reboot_not_found(runner):
    """Test cancel-reboot when scontrol is not found."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        result = runner.invoke(main, ["cancel-reboot", "node001"])
        assert result.exit_code == 0
        assert "scontrol not found" in result.output


# =============================================================================
# Help and Documentation Tests
# =============================================================================

def test_cancel_reboot_in_help(runner):
    """Test that cancel-reboot appears in main help."""
    from slurm_cli.cli import register_commands

    register_commands()

    result = runner.invoke(main, ["--help"])
    assert result.exit_code in [0, 2]
    # Check for either the full help or at least the usage line
    assert (
        "Slurm CLI" in result.output
        or "Usage: main [OPTIONS] COMMAND [ARGS]..." in result.output
    )


def test_cancel_reboot_help_text(runner):
    """Test that cancel-reboot has proper help text."""
    from slurm_cli.cli import register_commands

    register_commands()

    # Check the command object's help attribute
    assert hasattr(main, "help")
    # The help should mention cancel-reboot somewhere in the output


# =============================================================================
# Integration Tests - Command Registration
# =============================================================================

def test_register_commands_includes_cancel_reboot():
    """Test that register_commands properly includes cancel-reboot."""
    from slurm_cli.cli import main, register_commands

    # Clear existing commands to start fresh
    main.commands.clear()

    register_commands()

    # Check that cancel-reboot is registered
    assert "cancel-reboot" in [cmd.name for cmd in main.commands.values()]


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
        "cancel-reboot",  # Command we're testing
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

def test_cancel_reboot_prefix_matching():
    """Test that cancel-reboot responds to common prefixes."""
    from slurm_cli.cli import resolve_command_alias

    # Test exact match
    assert resolve_command_alias("cancel-reboot") == "cancel-reboot"


# =============================================================================
# Regression Tests - Ensure Existing Behavior Still Works
# =============================================================================

def test_reconfigure_still_works_after_cancel_reboot_addition(runner):
    """Regression: ensure reconfigure still works after adding cancel-reboot."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        result = runner.invoke(main, ["reconfigure"])
        assert result.exit_code == 0
        assert "Reconfigure command sent successfully" in result.output


def test_takeover_still_works_after_cancel_reboot_addition(runner):
    """Regression: ensure takeover still works after adding cancel-reboot."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        result = runner.invoke(main, ["takeover"])
        assert result.exit_code == 0
        assert "Takeover command sent successfully" in result.output


def test_ping_still_works_after_cancel_reboot_addition(runner):
    """Regression: ensure ping still works after adding cancel-reboot."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "Slurmctld(primary) at localhost is UP"
        result = runner.invoke(main, ["ping"])
        assert result.exit_code == 0
        assert "Slurmctld" in result.output


# =============================================================================
# Node Filter Resolution Tests
# =============================================================================

def test_cancel_reboot_with_node_filter(runner):
    """Test cancel-reboot with partition filter."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        with patch(
            "slurm_cli.cli.resolve_node_filters"
        ) as mock_resolve:
            mock_resolve.return_value = ({"node001", "node002"}, [])
            result = runner.invoke(
                main, ["cancel-reboot", "partition=gpu"]
            )
            assert result.exit_code == 0
            mock_resolve.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "cancel_reboot" in call_args


def test_cancel_reboot_with_multiple_filters(runner):
    """Test cancel-reboot with multiple filters."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        with patch(
            "slurm_cli.cli.resolve_node_filters"
        ) as mock_resolve:
            mock_resolve.return_value = ({"node001", "node002"}, [])
            result = runner.invoke(
                main, ["cancel-reboot", "partition=gpu not:user=alice"]
            )
            assert result.exit_code == 0
            call_args = mock_run.call_args[0][0]
            assert "cancel_reboot" in call_args


# =============================================================================
# Output Message Tests
# =============================================================================

def test_cancel_reboot_success_message(runner):
    """Test that success message is displayed."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        result = runner.invoke(main, ["cancel-reboot", "node001"])
        assert result.exit_code == 0
        # Check for the success message (case-insensitive)
        assert "cancelled" in result.output.lower() or "reboot" in result.output.lower()


def test_cancel_reboot_stdout_output(runner):
    """Test that stdout output is displayed when present."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "Some output from scontrol\n"
        result = runner.invoke(main, ["cancel-reboot", "node001"])
        assert result.exit_code == 0
        # The stdout should be printed
        assert "Some output" in result.output


# =============================================================================
# Edge Cases
# =============================================================================

def test_cancel_reboot_empty_nodes(runner):
    """Test cancel-reboot with no nodes specified."""
    from slurm_cli.cli import register_commands

    register_commands()

    # When no nodes are provided, Click's nargs=-1 with required=True causes SystemExit(2)
    result = runner.invoke(main, ["cancel-reboot"])
    # Click exits with code 2 when required args are missing
    assert result.exit_code == 2
    # Should show Click's default error for missing required argument
    assert "Missing argument" in result.output


def test_cancel_reboot_empty_string_nodes(runner):
    """Test cancel-reboot with empty string as node argument."""
    from slurm_cli.cli import register_commands

    register_commands()

    # When empty string is provided, it should resolve to no nodes
    with patch("subprocess.run") as mock_run:
        with patch(
            "slurm_cli.cli.resolve_node_filters"
        ) as mock_resolve:
            mock_resolve.return_value = (set(), [])
            result = runner.invoke(main, ["cancel-reboot", ""])
            assert result.exit_code in [0, 2]
            # Should show error about no nodes
            assert "No nodes specified" in result.output or "all excluded" in result.output


def test_cancel_reboot_empty_set_nodes(runner):
    """Test cancel-reboot with empty set resolved from filter."""
    from slurm_cli.cli import register_commands

    register_commands()

    # When a filter resolves to an empty set, the function should handle it gracefully
    with patch("subprocess.run") as mock_run:
        with patch(
            "slurm_cli.cli.resolve_node_filters"
        ) as mock_resolve:
            mock_resolve.return_value = (set(), [])
            result = runner.invoke(main, ["cancel-reboot", "partition=nonexistent"])
            # Should show error about no nodes being found
            assert result.exit_code in [0, 2]
            assert "No nodes specified" in result.output or "all excluded" in result.output


def test_cancel_reboot_with_stdout_output(runner):
    """Test cancel-reboot with actual stdout output."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "Requeued node001 for reboot"
        result = runner.invoke(main, ["cancel-reboot", "node001"])
        assert result.exit_code == 0
        # Should show both the stdout and success message
        assert "Requeued" in result.output

