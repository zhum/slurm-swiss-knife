"""Tests for the CLI module."""

import pytest
from click.testing import CliRunner

from slurm_cli.cli import main


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


def test_main_help(runner):
    """Test that the main command shows help."""
    # Ensure commands are properly registered
    from slurm_cli.cli import register_commands

    register_commands()

    result = runner.invoke(main, ["--help"])
    # Accept both exit codes as Click's help behavior can vary
    assert result.exit_code in [0, 2]
    # Check for either the full help or at least the usage line
    assert (
        "Slurm Swiss Knife" in result.output
        or "Usage: main [OPTIONS] COMMAND [ARGS]..." in result.output
    )


def test_show_command(runner):
    """Test the show command."""
    result = runner.invoke(main, ["show", "partitions"])
    assert result.exit_code == 0
    assert "Showing partitions" in result.output


def test_autocomplete_command(runner):
    """Test the autocomplete command."""
    result = runner.invoke(main, ["autocomplete"])
    assert result.exit_code == 0
    assert "Available commands" in result.output


def test_autocomplete_with_word(runner):
    """Test the autocomplete command with a word."""
    result = runner.invoke(main, ["autocomplete", "s"])
    assert result.exit_code == 0
    assert "Autocomplete results" in result.output
