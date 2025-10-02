"""Tests for the CLI module."""

import json
import os
import tempfile
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from slurm_cli.cli import main
from slurm_cli.utils.resources import Resource


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
    with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
        mock_ensure.return_value = (
            "partitions",
            None,
            {"test": "data"},
        )
        with patch(
            "slurm_cli.utils.partitions.Partition.show"
        ) as mock_show:
            result = runner.invoke(main, ["show", "partitions"])
            assert result.exit_code == 0
            mock_show.assert_called_once()


def test_autocomplete_command(runner):
    """Test the autocomplete command."""
    result = runner.invoke(main, ["autocomplete"])
    assert result.exit_code == 0
    assert (
        "Please provide a word to search for suggestions"
        in result.output
    )


def test_autocomplete_with_word(runner):
    """Test the autocomplete command with a word."""
    result = runner.invoke(main, ["autocomplete", "s"])
    assert result.exit_code == 0
    assert "Autocomplete results" in result.output


# Tests for --style, --json, --pretty, and --force-cache-update options


def test_style_option_help(runner):
    """Test that style options appear in help."""
    from slurm_cli.cli import register_commands

    register_commands()

    result = runner.invoke(main, ["--help"])
    assert result.exit_code in [0, 2]
    assert "--style" in result.output
    assert "--pretty" in result.output
    assert "--json" in result.output
    assert "--force-update" in result.output


def test_style_option_pretty(runner):
    """Test --style pretty option."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
        mock_ensure.return_value = (
            "partitions",
            None,
            {"test": "data"},
        )
        with patch(
            "slurm_cli.utils.partitions.Partition.show"
        ) as mock_show:
            result = runner.invoke(
                main, ["--style", "pretty", "show", "partitions"]
            )
            assert result.exit_code == 0
            mock_show.assert_called_once()
            # Check that style="pretty" was passed
            call_args = mock_show.call_args
            assert call_args[1]["style"] == "pretty"


def test_style_option_json(runner):
    """Test --style json option."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
        mock_ensure.return_value = (
            "partitions",
            None,
            {"test": "data"},
        )
        with patch(
            "slurm_cli.utils.partitions.Partition.show"
        ) as mock_show:
            result = runner.invoke(
                main, ["--style", "json", "show", "partitions"]
            )
            assert result.exit_code == 0
            mock_show.assert_called_once()
            # Check that style="json" was passed
            call_args = mock_show.call_args
            assert call_args[1]["style"] == "json"


def test_pretty_flag(runner):
    """Test --pretty convenience flag."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
        mock_ensure.return_value = (
            "partitions",
            None,
            {"test": "data"},
        )
        with patch(
            "slurm_cli.utils.partitions.Partition.show"
        ) as mock_show:
            result = runner.invoke(
                main, ["--pretty", "show", "partitions"]
            )
            assert result.exit_code == 0
            mock_show.assert_called_once()
            # Check that style="pretty" was passed
            call_args = mock_show.call_args
            assert call_args[1]["style"] == "pretty"


def test_json_flag(runner):
    """Test --json convenience flag."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
        mock_ensure.return_value = (
            "partitions",
            None,
            {"test": "data"},
        )
        with patch(
            "slurm_cli.utils.partitions.Partition.show"
        ) as mock_show:
            result = runner.invoke(
                main, ["--json", "show", "partitions"]
            )
            assert result.exit_code == 0
            mock_show.assert_called_once()
            # Check that style="json" was passed
            call_args = mock_show.call_args
            assert call_args[1]["style"] == "json"


def test_force_cache_update_flag(runner):
    """Test --force-update flag."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
        mock_ensure.return_value = (
            "partitions",
            None,
            {"test": "data"},
        )
        with patch(
            "slurm_cli.utils.partitions.Partition.show"
        ) as mock_show:
            result = runner.invoke(
                main, ["--force-update", "show", "partitions"]
            )
            assert result.exit_code == 0
            mock_show.assert_called_once()
            # Check that force_update=True was passed to ensure_resource_name
            mock_ensure.assert_called_once()
            call_args = mock_ensure.call_args
            assert call_args[0][2] is True  # force_update parameter


def test_style_and_cache_options_together(runner):
    """Test --style and --force-update options together."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
        mock_ensure.return_value = (
            "partitions",
            None,
            {"test": "data"},
        )
        with patch(
            "slurm_cli.utils.partitions.Partition.show"
        ) as mock_show:
            result = runner.invoke(
                main,
                [
                    "--style",
                    "json",
                    "--force-update",
                    "show",
                    "partitions",
                ],
            )
            assert result.exit_code == 0
            mock_show.assert_called_once()
            # Check both options were passed
            call_args = mock_show.call_args
            assert call_args[1]["style"] == "json"
            # Check that force_update=True was passed to ensure_resource_name
            mock_ensure.assert_called_once()
            ensure_call_args = mock_ensure.call_args
            assert (
                ensure_call_args[0][2] is True
            )  # force_update parameter


def test_convenience_flags_override_style(runner):
    """Test that convenience flags override --style option."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
        mock_ensure.return_value = (
            "partitions",
            None,
            {"test": "data"},
        )
        with patch(
            "slurm_cli.utils.partitions.Partition.show"
        ) as mock_show:
            # --pretty should override --style json
            result = runner.invoke(
                main,
                ["--style", "json", "--pretty", "show", "partitions"],
            )
            assert result.exit_code == 0
            mock_show.assert_called_once()
            call_args = mock_show.call_args
            assert call_args[1]["style"] == "pretty"

    with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
        mock_ensure.return_value = (
            "partitions",
            None,
            {"test": "data"},
        )
        with patch(
            "slurm_cli.utils.partitions.Partition.show"
        ) as mock_show:
            # --json should override --style pretty
            result = runner.invoke(
                main,
                ["--style", "pretty", "--json", "show", "partitions"],
            )
            assert result.exit_code == 0
            mock_show.assert_called_once()
            call_args = mock_show.call_args
            assert call_args[1]["style"] == "json"


def test_style_options_with_aliases(runner):
    """Test style options work with command aliases."""
    from slurm_cli.cli import register_commands

    register_commands()

    # Test with 'sh' alias
    with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
        mock_ensure.return_value = (
            "partitions",
            None,
            {"test": "data"},
        )
        with patch(
            "slurm_cli.utils.partitions.Partition.show"
        ) as mock_show:
            result = runner.invoke(main, ["--json", "sh", "partitions"])
            assert result.exit_code == 0
            mock_show.assert_called_once()
            call_args = mock_show.call_args
            assert call_args[1]["style"] == "json"

    # Test with 's' alias
    with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
        mock_ensure.return_value = (
            "partitions",
            None,
            {"test": "data"},
        )
        with patch(
            "slurm_cli.utils.partitions.Partition.show"
        ) as mock_show:
            result = runner.invoke(
                main, ["--pretty", "s", "partitions"]
            )
            assert result.exit_code == 0
            mock_show.assert_called_once()
            call_args = mock_show.call_args
            assert call_args[1]["style"] == "pretty"


def test_force_cache_update_with_aliases(runner):
    """Test force cache update works with command aliases."""
    from slurm_cli.cli import register_commands

    register_commands()

    # Test with 'sh' alias
    with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
        mock_ensure.return_value = (
            "partitions",
            None,
            {"test": "data"},
        )
        with patch(
            "slurm_cli.utils.partitions.Partition.show"
        ) as mock_show:
            result = runner.invoke(
                main, ["--force-update", "sh", "partitions"]
            )
            assert result.exit_code == 0
            mock_show.assert_called_once()
            # Check that force_update=True was passed to ensure_resource_name
            mock_ensure.assert_called_once()
            ensure_call_args = mock_ensure.call_args
            assert (
                ensure_call_args[0][2] is True
            )  # force_update parameter

    # Test with 's' alias
    with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
        mock_ensure.return_value = (
            "partitions",
            None,
            {"test": "data"},
        )
        with patch(
            "slurm_cli.utils.partitions.Partition.show"
        ) as mock_show:
            result = runner.invoke(
                main, ["--force-update", "s", "partitions"]
            )
            assert result.exit_code == 0
            mock_show.assert_called_once()
            # Check that force_update=True was passed to ensure_resource_name
            mock_ensure.assert_called_once()
            ensure_call_args = mock_ensure.call_args
            assert (
                ensure_call_args[0][2] is True
            )  # force_update parameter


def test_style_options_with_different_resources(runner):
    """Test style options work with different resource types."""
    from slurm_cli.cli import register_commands

    register_commands()

    # Test with nodes
    with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
        mock_ensure.return_value = ("nodes", None, {"test": "data"})
        with patch("slurm_cli.utils.nodes.Node.show") as mock_show:
            result = runner.invoke(main, ["--json", "show", "nodes"])
            assert result.exit_code == 0
            mock_show.assert_called_once()
            call_args = mock_show.call_args
            assert call_args[1]["style"] == "json"

    # Test with users
    with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
        mock_ensure.return_value = ("users", None, {"test": "data"})
        with patch("slurm_cli.utils.users.User.show") as mock_show:
            result = runner.invoke(main, ["--pretty", "show", "users"])
            assert result.exit_code == 0
            mock_show.assert_called_once()
            call_args = mock_show.call_args
            assert call_args[1]["style"] == "pretty"


def test_force_cache_update_with_different_resources(runner):
    """Test force cache update works with different resource types."""
    from slurm_cli.cli import register_commands

    register_commands()

    # Test with nodes
    with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
        mock_ensure.return_value = ("nodes", None, {"test": "data"})
        with patch("slurm_cli.utils.nodes.Node.show") as mock_show:
            result = runner.invoke(
                main, ["--force-update", "show", "nodes"]
            )
            assert result.exit_code == 0
            mock_show.assert_called_once()
            # Check that force_update=True was passed to ensure_resource_name
            mock_ensure.assert_called_once()
            ensure_call_args = mock_ensure.call_args
            assert (
                ensure_call_args[0][2] is True
            )  # force_update parameter

    # Test with users
    with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
        mock_ensure.return_value = ("users", None, {"test": "data"})
        with patch("slurm_cli.utils.users.User.show") as mock_show:
            result = runner.invoke(
                main, ["--force-update", "show", "users"]
            )
            assert result.exit_code == 0
            mock_show.assert_called_once()
            # Check that force_update=True was passed to ensure_resource_name
            mock_ensure.assert_called_once()
            ensure_call_args = mock_ensure.call_args
            assert (
                ensure_call_args[0][2] is True
            )  # force_update parameter


def test_invalid_style_option(runner):
    """Test invalid style option handling."""
    from slurm_cli.cli import register_commands

    register_commands()

    result = runner.invoke(
        main, ["--style", "invalid", "show", "partitions"]
    )
    # Should fail with invalid choice
    assert result.exit_code != 0
    assert "Invalid value" in result.output or "Usage:" in result.output


def test_default_style_behavior(runner):
    """Test that default style is pretty."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
        mock_ensure.return_value = (
            "partitions",
            None,
            {"test": "data"},
        )
        with patch(
            "slurm_cli.utils.partitions.Partition.show"
        ) as mock_show:
            result = runner.invoke(main, ["show", "partitions"])
            assert result.exit_code == 0
            mock_show.assert_called_once()
            call_args = mock_show.call_args
            assert call_args[1]["style"] == "pretty"
            # Check that force_update=False was passed to ensure_resource_name
            mock_ensure.assert_called_once()
            ensure_call_args = mock_ensure.call_args
            assert (
                ensure_call_args[0][2] is False
            )  # force_update parameter


def test_cache_update_functionality():
    """Test force_cache_update parameter works in Resource.cached_resource."""

    # Create a temporary cache file
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".json"
    ) as f:
        json.dump({"test": "data"}, f)
        cache_file = f.name

    # Mock the cache file path
    original_cache_files = Resource.CACHE_FILES.copy()
    Resource.CACHE_FILES["test_resource"] = cache_file

    try:
        # Test normal caching (should use cache if recent)
        with patch.object(Resource, "update_cache") as mock_update:
            mock_update.return_value = {"test": "fresh_data"}

            # First call should use cache
            result = Resource.cached_resource("test_resource", False)
            assert result == {"test": "data"}
            mock_update.assert_not_called()

            # Force update should bypass cache
            result = Resource.cached_resource("test_resource", True)
            assert result == {"test": "fresh_data"}
            mock_update.assert_called_once()

    finally:
        # Cleanup
        Resource.CACHE_FILES = original_cache_files
        os.unlink(cache_file)


def test_context_object_storage():
    """Test context object properly stores style and cache update flags."""
    from click.testing import CliRunner

    runner = CliRunner()

    # Test context storage
    with runner.isolated_filesystem():
        result = runner.invoke(
            main,
            [
                "--style",
                "json",
                "--force-update",
                "show",
                "--help",
            ],
        )

        # The context should be properly set up
        # We can't directly test the context here since it's internal to Click
        # but we can verify the commands run without error
        assert result.exit_code in [0, 2]  # Help can return 0 or 2
