"""Tests for the CLI module."""

import pytest
from click.testing import CliRunner

from slurm_swiss_knife.cli import main


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


def test_main_help(runner):
    """Test that the main command shows help."""
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Slurm Swiss Knife" in result.output


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
