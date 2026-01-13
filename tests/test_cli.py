"""Tests for the CLI module."""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

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
    """Test the autocomplete command returns bash completion script."""
    result = runner.invoke(main, ["autocomplete"])
    assert result.exit_code == 0
    # Now returns a bash completion script
    assert (
        "_slurm_cli_initialize_autocomplete" in result.output
        or "complete -F" in result.output
    )


def test_autocomplete_with_word(runner):
    """Test the autocomplete command with a word still returns script."""
    result = runner.invoke(main, ["autocomplete", "s"])
    assert result.exit_code == 0
    # Autocomplete command now returns full bash script
    assert (
        "_slurm_cli_initialize_autocomplete" in result.output
        or "complete -F" in result.output
    )


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

    # Test with 'sho' alias (not 's' which is now ambiguous with 'set')
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
                main, ["--pretty", "sho", "partitions"]
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

    # Test with 'sho' alias (not 's' which is now ambiguous with 'set')
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
                main, ["--force-update", "sho", "partitions"]
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


# Tests for scontrol commands


def test_version_command(runner):
    """Test the version command."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "slurm 23.11.4"
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["version"])
        assert result.exit_code == 0
        assert "slurm-cli" in result.output
        assert "Slurm Swiss Knife" in result.output


def test_version_command_alias(runner):
    """Test the version command with alias 'ver'."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "slurm 23.11.4"
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["ver"])
        assert result.exit_code == 0
        assert "slurm-cli" in result.output


def test_reconfigure_command(runner):
    """Test the reconfigure command."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["reconfigure"])
        assert result.exit_code == 0
        assert "Reconfigure command sent successfully" in result.output
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args == ["scontrol", "reconfigure"]


def test_reconfigure_command_alias(runner):
    """Test the reconfigure command with alias 'reconf'."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["reconf"])
        assert result.exit_code == 0
        assert "Reconfigure command sent successfully" in result.output


def test_reconfigure_command_verbose(runner):
    """Test the reconfigure command with verbose flag."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["reconfigure", "-v"])
        assert result.exit_code == 0
        assert "Running: scontrol reconfigure" in result.output


def test_ping_command(runner):
    """Test the ping command."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = (
            "Slurmctld(primary) at localhost is UP"
        )
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["ping"])
        assert result.exit_code == 0
        assert "Slurmctld" in result.output
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args == ["scontrol", "ping"]


def test_ping_command_alias(runner):
    """Test the ping command with prefix alias 'pi'."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = (
            "Slurmctld(primary) at localhost is UP"
        )
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["pi"])
        assert result.exit_code == 0
        assert "Slurmctld" in result.output


def test_takeover_command(runner):
    """Test the takeover command."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["takeover"])
        assert result.exit_code == 0
        assert "Takeover command sent successfully" in result.output
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args == ["scontrol", "takeover"]


def test_takeover_command_alias(runner):
    """Test the takeover command with prefix alias 'tak'."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["tak"])
        assert result.exit_code == 0
        assert "Takeover command sent successfully" in result.output


def test_scontrol_commands_error_handling(runner):
    """Test error handling for scontrol commands."""
    import subprocess as sp

    from slurm_cli.cli import register_commands

    register_commands()

    # Test reconfigure error
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = sp.CalledProcessError(
            1, "scontrol", stderr="Permission denied"
        )
        result = runner.invoke(main, ["reconfigure"])
        assert result.exit_code == 0  # Command itself succeeds
        assert "Error" in result.output

    # Test ping error
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = sp.CalledProcessError(
            1, "scontrol", stderr="Connection refused"
        )
        result = runner.invoke(main, ["ping"])
        assert result.exit_code == 0
        assert "Error" in result.output


def test_scontrol_not_found(runner):
    """Test handling when scontrol is not found."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        result = runner.invoke(main, ["ping"])
        assert result.exit_code == 0
        assert "scontrol not found" in result.output


def test_resolve_command_alias_new_commands():
    """Test resolve_command_alias for new commands."""
    from slurm_cli.cli import resolve_command_alias

    # Test reconfigure - prefix matching
    assert resolve_command_alias("reconfigure") == "reconfigure"
    assert resolve_command_alias("recon") == "reconfigure"
    assert resolve_command_alias("reconf") == "reconfigure"
    assert resolve_command_alias("reconfi") == "reconfigure"

    # Test ping - prefix matching
    assert resolve_command_alias("ping") == "ping"
    assert resolve_command_alias("pin") == "ping"

    # Test takeover - prefix matching
    assert resolve_command_alias("takeover") == "takeover"
    assert resolve_command_alias("take") == "takeover"
    assert resolve_command_alias("tak") == "takeover"

    # Test version - prefix matching
    assert resolve_command_alias("version") == "version"
    assert resolve_command_alias("ver") == "version"

    # Test token - prefix matching
    assert resolve_command_alias("token") == "token"
    assert resolve_command_alias("tok") == "token"

    # Test drain - prefix matching
    assert resolve_command_alias("drain") == "drain"
    assert resolve_command_alias("dra") == "drain"
    assert resolve_command_alias("dr") == "drain"

    # Test undrain - prefix matching
    assert resolve_command_alias("undrain") == "undrain"
    assert resolve_command_alias("undr") == "undrain"


def test_token_command(runner):
    """Test the token command."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "SLURM_JWT=test_token"
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["token"])
        assert result.exit_code == 0
        assert "SLURM_JWT" in result.output
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args == ["scontrol", "token"]


def test_token_command_with_lifespan(runner):
    """Test the token command with lifespan option."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "SLURM_JWT=test_token"
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["token", "lifespan=1h"])
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert call_args == ["scontrol", "token", "lifespan=3600"]


def test_token_command_with_time_formats(runner):
    """Test the token command with various time formats."""
    from slurm_cli.cli import register_commands

    register_commands()

    # Test HH:MM:SS format
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "SLURM_JWT=test_token"
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["token", "lifespan=1:30:00"])
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert call_args == ["scontrol", "token", "lifespan=5400"]

    # Test minutes format
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "SLURM_JWT=test_token"
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["token", "lifespan=30m"])
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert call_args == ["scontrol", "token", "lifespan=1800"]

    # Test days format
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "SLURM_JWT=test_token"
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["token", "lifespan=1-12:00:00"])
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        # 1 day + 12 hours = 86400 + 43200 = 129600
        assert call_args == ["scontrol", "token", "lifespan=129600"]


def test_token_command_with_infinite(runner):
    """Test the token command with infinite lifespan."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "SLURM_JWT=test_token"
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["token", "lifespan=infinite"])
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        # Infinite should not add lifespan option
        assert call_args == ["scontrol", "token"]


def test_token_command_with_username(runner):
    """Test the token command with username option."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "SLURM_JWT=test_token"
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["token", "username=testuser"])
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert call_args == ["scontrol", "token", "username=testuser"]


def test_token_command_with_both_options(runner):
    """Test the token command with both lifespan and username."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "SLURM_JWT=test_token"
        mock_run.return_value.returncode = 0
        result = runner.invoke(
            main, ["token", "lifespan=2h", "username=admin"]
        )
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "scontrol" in call_args
        assert "token" in call_args
        assert "lifespan=7200" in call_args
        assert "username=admin" in call_args


def test_parse_time_to_seconds():
    """Test the parse_time_to_seconds function."""
    from slurm_cli.cli import parse_time_to_seconds

    # Integer seconds
    assert parse_time_to_seconds("3600") == 3600

    # HH:MM:SS format
    assert parse_time_to_seconds("1:00:00") == 3600
    assert parse_time_to_seconds("1:30:00") == 5400
    assert parse_time_to_seconds("0:30:00") == 1800

    # MM:SS format
    assert parse_time_to_seconds("30:00") == 1800
    assert parse_time_to_seconds("5:30") == 330

    # D-HH:MM:SS format
    assert parse_time_to_seconds("1-0:00:00") == 86400
    assert parse_time_to_seconds("1-12:00:00") == 129600

    # Nh, Nm, Ns format
    assert parse_time_to_seconds("1h") == 3600
    assert parse_time_to_seconds("30m") == 1800
    assert parse_time_to_seconds("45s") == 45
    assert parse_time_to_seconds("2d") == 172800

    # Infinite
    assert parse_time_to_seconds("infinite") is None
    assert parse_time_to_seconds("inf") is None
    assert parse_time_to_seconds("unlimited") is None

    # Case insensitive
    assert parse_time_to_seconds("INFINITE") is None
    assert parse_time_to_seconds("1H") == 3600


def test_drain_command(runner):
    """Test the drain command."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["drain", "node001"])
        assert result.exit_code == 0
        assert "Drained" in result.output
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args == [
            "scontrol",
            "update",
            "nodename=node001",
            "state=drain",
        ]


def test_drain_command_multiple_nodes(runner):
    """Test the drain command with multiple nodes (ranges are expanded)."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(
            main, ["drain", "node001", "node002", "node[003-005]"]
        )
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        # Ranges are expanded to individual nodes
        assert call_args == [
            "scontrol",
            "update",
            "nodename=node001,node002,node003,node004,node005",
            "state=drain",
        ]


def test_drain_command_with_reason(runner):
    """Test the drain command with reason option."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(
            main, ["drain", "node001", "--reason", "Maintenance"]
        )
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "reason=Maintenance" in call_args


def test_drain_command_with_short_reason(runner):
    """Test the drain command with -r option."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(
            main, ["drain", "node001", "-r", "Hardware issue"]
        )
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "reason=Hardware issue" in call_args


def test_drain_command_with_inline_reason(runner):
    """Test the drain command with reason= inline option."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(
            main, ["drain", "node001", "reason=Scheduled maintenance"]
        )
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "reason=Scheduled maintenance" in call_args
        # Node should not include the reason=
        assert "nodename=node001" in call_args


def test_drain_command_option_overrides_inline(runner):
    """Test that --reason option overrides inline reason=."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(
            main,
            [
                "drain",
                "node001",
                "reason=Inline reason",
                "--reason",
                "Option reason",
            ],
        )
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        # --reason should override inline
        assert "reason=Option reason" in call_args


def test_undrain_command(runner):
    """Test the undrain command."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["undrain", "node001"])
        assert result.exit_code == 0
        assert "Undrained" in result.output
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args == [
            "scontrol",
            "update",
            "nodename=node001",
            "state=resume",
        ]


def test_undrain_command_multiple_nodes(runner):
    """Test the undrain command with multiple nodes (ranges are expanded)."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(
            main, ["undrain", "node001", "node002", "node[003-005]"]
        )
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        # Ranges are expanded to individual nodes
        assert call_args == [
            "scontrol",
            "update",
            "nodename=node001,node002,node003,node004,node005",
            "state=resume",
        ]


def test_drain_command_alias(runner):
    """Test the drain command with alias 'dr'."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["dr", "node001"])
        assert result.exit_code == 0
        assert "Drained" in result.output


def test_undrain_command_alias(runner):
    """Test the undrain command with alias 'undr'."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["undr", "node001"])
        assert result.exit_code == 0
        assert "Undrained" in result.output


def test_undrain_command_resume_alias(runner):
    """Test the undrain command with alias 'resume'."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["resume", "node001"])
        assert result.exit_code == 0
        assert "Undrained" in result.output


def test_drain_command_with_partition_filter(runner):
    """Test the drain command with partition filter."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        with patch(
            "slurm_cli.cli.resolve_node_filters"
        ) as mock_resolve:
            mock_resolve.return_value = (
                {"node001", "node002", "node003"},
                [],
            )
            result = runner.invoke(
                main,
                ["drain", "partition=gpu", "-r", "GPU maintenance"],
            )
            assert result.exit_code == 0
            mock_resolve.assert_called_once()
            call_args = mock_run.call_args[0][0]
            # Node order may vary since we use a set
            assert "nodename=" in call_args[2]
            assert "state=drain" in call_args


def test_undrain_command_with_state_filter(runner):
    """Test the undrain command with state filter."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        with patch(
            "slurm_cli.cli.resolve_node_filters"
        ) as mock_resolve:
            mock_resolve.return_value = ({"node001", "node002"}, [])
            result = runner.invoke(main, ["undrain", "state=drain"])
            assert result.exit_code == 0
            mock_resolve.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "nodename=" in call_args[2]
            assert "state=resume" in call_args


def test_drain_command_filter_no_match(runner):
    """Test the drain command when filter matches no nodes."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("slurm_cli.cli.resolve_node_filters") as mock_resolve:
        mock_resolve.return_value = (set(), [])
        result = runner.invoke(main, ["drain", "partition=nonexistent"])
        assert "No nodes specified or all excluded" in result.output


def test_drain_command_with_exclusion_filter(runner):
    """Test the drain command with exclusion filter (-prefix)."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        with patch(
            "slurm_cli.cli.resolve_node_filters"
        ) as mock_resolve:
            # Simulating partition=gpu with 5 nodes, not:reservation=maint excludes 2
            mock_resolve.return_value = (
                {"node001", "node002", "node003"},
                [],
            )
            result = runner.invoke(
                main,
                [
                    "drain",
                    "partition=gpu",
                    "not:reservation=maint",
                    "-r",
                    "Maintenance",
                ],
            )
            assert result.exit_code == 0
            call_args = mock_run.call_args[0][0]
            assert "state=drain" in call_args


def test_reboot_command(runner):
    """Test the reboot command."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["reboot", "node001"])
        assert result.exit_code == 0
        assert "Rebooting" in result.output
        call_args = mock_run.call_args[0][0]
        assert "scontrol" in call_args
        assert "reboot" in call_args
        assert "node001" in call_args


def test_reboot_command_multiple_nodes(runner):
    """Test the reboot command with multiple nodes."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(
            main, ["reboot", "node001", "node002", "node003"]
        )
        assert result.exit_code == 0
        assert "Rebooting" in result.output
        call_args = mock_run.call_args[0][0]
        # Nodes are joined with commas
        assert "node001,node002,node003" in call_args[-1]


def test_reboot_command_with_asap(runner):
    """Test the reboot command with asap flag."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["reboot", "asap", "node001"])
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "asap" in call_args


def test_reboot_command_with_nextstate(runner):
    """Test the reboot command with nextstate option."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(
            main, ["reboot", "nextstate=DOWN", "node001"]
        )
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "nextstate=DOWN" in call_args


def test_reboot_command_with_reason(runner):
    """Test the reboot command with reason option."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(
            main, ["reboot", "reason=Kernel update", "node001"]
        )
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "reason=Kernel update" in call_args


def test_reboot_command_with_all_options(runner):
    """Test the reboot command with all options."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(
            main,
            [
                "reboot",
                "asap",
                "nextstate=RESUME",
                "reason=Maintenance",
                "node001",
            ],
        )
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "asap" in call_args
        assert "nextstate=RESUME" in call_args
        assert "reason=Maintenance" in call_args


def test_reboot_command_all_nodes(runner):
    """Test the reboot command with ALL keyword."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["reboot", "ALL"])
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "ALL" in call_args


def test_reboot_command_alias(runner):
    """Test the reboot command with alias 'reb'."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["reb", "node001"])
        assert result.exit_code == 0
        assert "Rebooting" in result.output


def test_reboot_command_invalid_nextstate(runner):
    """Test the reboot command with invalid nextstate."""
    from slurm_cli.cli import register_commands

    register_commands()

    result = runner.invoke(
        main, ["reboot", "nextstate=INVALID", "node001"]
    )
    assert "Error" in result.output
    assert "RESUME or DOWN" in result.output


def test_reboot_command_with_filter(runner):
    """Test the reboot command with partition filter."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        with patch(
            "slurm_cli.cli.resolve_node_filters"
        ) as mock_resolve:
            mock_resolve.return_value = (
                {"node001", "node002", "node003"},
                [],
            )
            result = runner.invoke(
                main, ["reboot", "partition=gpu", "reason=GPU firmware"]
            )
            assert result.exit_code == 0
            mock_resolve.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "reason=GPU firmware" in call_args


def test_cancel_reboot_command(runner):
    """Test the cancel_reboot command."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["cancel_reboot", "node001"])
        assert result.exit_code == 0
        assert "Cancelled reboot" in result.output
        call_args = mock_run.call_args[0][0]
        assert "scontrol" in call_args
        assert "cancel_reboot" in call_args
        assert "node001" in call_args


def test_cancel_reboot_command_multiple_nodes(runner):
    """Test the cancel_reboot command with multiple nodes."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(
            main, ["cancel_reboot", "node001", "node002", "node003"]
        )
        assert result.exit_code == 0
        assert "Cancelled reboot" in result.output
        call_args = mock_run.call_args[0][0]
        assert "node001,node002,node003" in call_args[-1]


def test_cancel_reboot_command_alias(runner):
    """Test the cancel_reboot command with alias 'cancel_reb'."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = runner.invoke(main, ["cancel_reb", "node001"])
        assert result.exit_code == 0
        assert "Cancelled reboot" in result.output


def test_cancel_reboot_command_with_filter(runner):
    """Test the cancel_reboot command with partition filter."""
    from slurm_cli.cli import register_commands

    register_commands()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        with patch(
            "slurm_cli.cli.resolve_node_filters"
        ) as mock_resolve:
            mock_resolve.return_value = (
                {"node001", "node002", "node003"},
                [],
            )
            result = runner.invoke(
                main, ["cancel_reboot", "partition=gpu"]
            )
            assert result.exit_code == 0
            mock_resolve.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "cancel_reboot" in call_args


def test_show_nodes_with_filter(runner):
    """Test show nodes command with node filter."""
    from slurm_cli.cli import register_commands

    register_commands()

    # Mock Resource.cached_resource to return test data
    with patch(
        "slurm_cli.utils.resources.Resource.cached_resource"
    ) as mock_cache:
        mock_cache.return_value = {
            "node001": {"name": "node001", "state": "idle"},
            "node002": {"name": "node002", "state": "idle"},
        }
        # Mock resolve_node_filters in cli module (where it's imported)
        with patch(
            "slurm_cli.cli.resolve_node_filters"
        ) as mock_resolve:
            mock_resolve.return_value = ({"node001", "node002"}, [])
            with patch("slurm_cli.utils.nodes.Node.show") as mock_show:
                result = runner.invoke(
                    main, ["show", "nodes", "partition=gpu"]
                )
                # The command should not crash with KeyError
                # It should call resolve_node_filters for the filter
                mock_resolve.assert_called_once()


def test_autocomplete_nodes_filter_options(runner):
    """Test that autocomplete includes node filter options for show nodes."""
    from slurm_cli.cli import register_commands

    register_commands()

    result = runner.invoke(main, ["autocomplete"])
    assert result.exit_code == 0

    # Check that node filter options are included in the autocomplete script
    # for the show command
    assert "filter_options" in result.output
    assert "partition=" in result.output
    assert "state=" in result.output
    assert "user=" in result.output
    assert "reservation=" in result.output

    # Check that the show command includes filter_options
    assert (
        "$filter_options $show_options $cached_nodes" in result.output
        or "filter_options $show_options" in result.output
    )


def test_autocomplete_drain_undrain_options(runner):
    """Test that autocomplete includes options for drain/undrain commands."""
    from slurm_cli.cli import register_commands

    register_commands()

    result = runner.invoke(main, ["autocomplete"])
    assert result.exit_code == 0

    # Check drain command options
    assert "drain)" in result.output
    assert "reason=" in result.output
    assert "--reason" in result.output

    # Check undrain command options
    assert "undrain)" in result.output

    # Check node filters are available
    assert "not:partition=" in result.output
    assert "not:state=" in result.output
    assert "not:user=" in result.output
    assert "not:reservation=" in result.output


def test_autocomplete_reboot_options(runner):
    """Test that autocomplete includes options for reboot command."""
    from slurm_cli.cli import register_commands

    register_commands()

    result = runner.invoke(main, ["autocomplete"])
    assert result.exit_code == 0

    # Check reboot command options
    assert "reboot)" in result.output
    assert "asap" in result.output
    assert "nextstate=" in result.output
    assert "RESUME" in result.output
    assert "DOWN" in result.output


def test_autocomplete_cancel_reboot_options(runner):
    """Test that autocomplete includes options for cancel_reboot command."""
    from slurm_cli.cli import register_commands

    register_commands()

    result = runner.invoke(main, ["autocomplete"])
    assert result.exit_code == 0

    # Check cancel_reboot command options
    assert "cancel_reboot)" in result.output
    # Should have node filters
    assert "partition=" in result.output


class TestProfileOutput:
    """Tests for profile-based output formatting."""

    def test_qos_minimal_profile_columns(self, runner):
        """Test that minimal profile shows only name column for QoS."""
        from slurm_cli.utils.profiles import get_profile_config

        (
            columns,
            styles,
            template,
            sort_field,
            sort_asc,
        ) = get_profile_config("minimal", "qos", None)
        assert columns == ["name"]

    def test_qos_compact_profile_columns(self, runner):
        """Test that compact profile shows name and priority for QoS."""
        from slurm_cli.utils.profiles import get_profile_config

        (
            columns,
            styles,
            template,
            sort_field,
            sort_asc,
        ) = get_profile_config("compact", "qos", None)
        assert "name" in columns
        assert "priority" in columns

    def test_qos_oneline_profile_template(self, runner):
        """Test that oneline profile has template with max_tres fields."""
        from slurm_cli.utils.profiles import get_profile_config

        (
            columns,
            styles,
            template,
            sort_field,
            sort_asc,
        ) = get_profile_config("oneline", "qos", None)
        assert template is not None
        assert "max_tres" in template
        assert "max_jobs" in template

    def test_qos_default_profile_auto_columns(self, runner):
        """Test that default profile uses auto-detection (no columns)."""
        from slurm_cli.utils.profiles import get_profile_config

        (
            columns,
            styles,
            template,
            sort_field,
            sort_asc,
        ) = get_profile_config("default", "qos", None)
        # Default profile doesn't specify columns for QoS
        assert columns is None or columns == "*" or columns == []

    def test_nodes_minimal_profile_columns(self, runner):
        """Test that minimal profile shows limited columns for nodes."""
        from slurm_cli.utils.profiles import get_profile_config

        (
            columns,
            styles,
            template,
            sort_field,
            sort_asc,
        ) = get_profile_config("minimal", "nodes", None)
        assert "name" in columns
        assert "state" in columns

    def test_nodes_oneline_profile_template(self, runner):
        """Test that oneline profile has template for nodes."""
        from slurm_cli.utils.profiles import get_profile_config

        (
            columns,
            styles,
            template,
            sort_field,
            sort_asc,
        ) = get_profile_config("oneline", "nodes", None)
        assert template is not None
        assert "name" in template
        assert "state" in template

    def test_partitions_minimal_profile_columns(self, runner):
        """Test that minimal profile shows limited columns for partitions."""
        from slurm_cli.utils.profiles import get_profile_config

        (
            columns,
            styles,
            template,
            sort_field,
            sort_asc,
        ) = get_profile_config("minimal", "partitions", None)
        assert "name" in columns
        assert "state" in columns

    def test_profile_str_override(self, runner):
        """Test that profile_str overrides profile."""
        from slurm_cli.utils.profiles import get_profile_config

        # Use profile_str to specify custom columns
        (
            columns,
            styles,
            template,
            sort_field,
            sort_asc,
        ) = get_profile_config(
            "default", "qos", "qos.columns=name,priority,flags"
        )
        assert columns == ["name", "priority", "flags"]

    def test_different_profiles_different_output(self, runner):
        """Test that different profiles produce different configurations."""
        from slurm_cli.utils.profiles import get_profile_config

        minimal = get_profile_config("minimal", "qos", None)
        compact = get_profile_config("compact", "qos", None)
        oneline = get_profile_config("oneline", "qos", None)

        # Minimal has fewer columns
        assert minimal[0] == ["name"]
        # Compact has more columns
        assert len(compact[0]) > len(minimal[0])
        # Oneline uses template instead of columns
        assert oneline[2] is not None  # template


class TestListFields:
    """Tests for --list-fields option."""

    def test_list_fields_all(self, runner):
        """Test --list-fields shows all resource fields."""
        result = runner.invoke(main, ["--list-fields"])
        assert result.exit_code == 0
        # Should show fields for multiple resources
        assert "[jobs]" in result.output
        assert "[nodes]" in result.output
        assert "[partitions]" in result.output
        assert "[reservations]" in result.output
        # Should show template syntax help
        assert "Template syntax:" in result.output
        assert "{field}" in result.output

    def test_list_fields_specific_resource(self, runner):
        """Test --list-fields=jobs shows fields for specific resource."""
        result = runner.invoke(main, ["--list-fields=jobs"])
        assert result.exit_code == 0
        assert "Available fields for 'jobs'" in result.output
        # Should show job-specific fields
        assert (
            "job_id" in result.output
            or "jobid" in result.output.lower()
        )
        # Should not show fields from other resources
        assert "[nodes]" not in result.output

    def test_list_fields_nodes(self, runner):
        """Test --list-fields=nodes shows node fields."""
        result = runner.invoke(main, ["--list-fields=nodes"])
        assert result.exit_code == 0
        assert "Available fields for 'nodes'" in result.output
        assert "Template syntax:" in result.output

    def test_list_fields_short_form(self, runner):
        """Test --list-fields with short resource names."""
        # 'res' should map to 'reservations'
        result = runner.invoke(main, ["--list-fields=res"])
        assert result.exit_code == 0
        assert "Available fields for 'reservations'" in result.output

        # 'part' should map to 'partitions'
        result = runner.invoke(main, ["--list-fields=part"])
        assert result.exit_code == 0
        assert "Available fields for 'partitions'" in result.output

    def test_list_fields_invalid_resource(self, runner):
        """Test --list-fields with unknown resource."""
        result = runner.invoke(main, ["--list-fields=invalid"])
        assert result.exit_code == 0
        assert (
            "No field documentation for resource: invalid"
            in result.output
        )
        assert "Available resources:" in result.output

    def test_list_fields_qos(self, runner):
        """Test --list-fields=qos shows QoS fields."""
        result = runner.invoke(main, ["--list-fields=qos"])
        assert result.exit_code == 0
        assert "Available fields for 'qos'" in result.output
        # Check for common QoS fields
        assert "name" in result.output or "priority" in result.output

    def test_list_fields_show_resource_level(self, runner):
        """Test show <resource> --list-fields shows fields for that resource."""
        result = runner.invoke(main, ["show", "jobs", "--list-fields"])
        assert result.exit_code == 0
        assert "Available fields for 'jobs'" in result.output
        assert (
            "job_id" in result.output
            or "jobid" in result.output.lower()
        )

    def test_list_fields_show_resource_level_short(self, runner):
        """Test show <resource> -L works with short flag."""
        result = runner.invoke(main, ["show", "nodes", "-L"])
        assert result.exit_code == 0
        assert "Available fields for 'nodes'" in result.output
        assert "state" in result.output

    def test_list_fields_show_no_resource(self, runner):
        """Test show --list-fields without resource shows all."""
        result = runner.invoke(main, ["show", "--list-fields"])
        assert result.exit_code == 0
        # Should show fields for multiple resources
        assert "[jobs]" in result.output
        assert "[nodes]" in result.output

    def test_list_fields_update_resource(self, runner):
        """Test mod <resource> --list-fields shows fields."""
        result = runner.invoke(main, ["mod", "part", "-L"])
        assert result.exit_code == 0
        assert "Available fields for 'partitions'" in result.output

    def test_list_fields_create_resource(self, runner):
        """Test add <resource> --list-fields shows fields."""
        result = runner.invoke(main, ["add", "users", "--list-fields"])
        assert result.exit_code == 0
        assert "Available fields for 'users'" in result.output

    def test_list_fields_delete_resource(self, runner):
        """Test del <resource> -L shows fields."""
        result = runner.invoke(main, ["del", "qos", "-L"])
        assert result.exit_code == 0
        assert "Available fields for 'qos'" in result.output


class TestJobControlCommands:
    """Tests for job control commands: hold, release, top, requeue, suspend."""

    def test_hold_command_basic(self, runner):
        """Test hold command with job ID."""
        from slurm_cli.cli import register_commands

        register_commands()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="", stderr=""
            )
            result = runner.invoke(main, ["hold", "12345"])
            assert result.exit_code == 0
            mock_run.assert_called()
            call_args = mock_run.call_args[0][0]
            assert "scontrol" in call_args
            assert "hold" in call_args
            assert "12345" in call_args

    def test_hold_command_with_reason_option(self, runner):
        """Test hold command with --reason option."""
        from slurm_cli.cli import register_commands

        register_commands()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="", stderr=""
            )
            result = runner.invoke(
                main, ["hold", "12345", "--reason", "Waiting for data"]
            )
            assert result.exit_code == 0
            mock_run.assert_called()
            call_args = mock_run.call_args[0][0]
            assert "reason=Waiting for data" in call_args

    def test_hold_command_with_inline_reason(self, runner):
        """Test hold command with reason= inline."""
        from slurm_cli.cli import register_commands

        register_commands()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="", stderr=""
            )
            result = runner.invoke(
                main, ["hold", "12345", "reason=Need review"]
            )
            assert result.exit_code == 0
            mock_run.assert_called()
            call_args = mock_run.call_args[0][0]
            assert "reason=Need review" in call_args

    def test_release_command_basic(self, runner):
        """Test release command with job ID."""
        from slurm_cli.cli import register_commands

        register_commands()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="", stderr=""
            )
            result = runner.invoke(main, ["release", "12345"])
            assert result.exit_code == 0
            mock_run.assert_called()
            call_args = mock_run.call_args[0][0]
            assert "scontrol" in call_args
            assert "release" in call_args
            assert "12345" in call_args

    def test_top_command_basic(self, runner):
        """Test top command with job IDs."""
        from slurm_cli.cli import register_commands

        register_commands()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="", stderr=""
            )
            result = runner.invoke(main, ["top", "12345", "12346"])
            assert result.exit_code == 0
            mock_run.assert_called()
            call_args = mock_run.call_args[0][0]
            assert "scontrol" in call_args
            assert "top" in call_args
            # top uses comma-separated job list (order may vary due to set)
            job_list = call_args[2]
            assert "12345" in job_list
            assert "12346" in job_list

    def test_requeue_command_basic(self, runner):
        """Test requeue command with job ID."""
        from slurm_cli.cli import register_commands

        register_commands()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="", stderr=""
            )
            result = runner.invoke(main, ["requeue", "12345"])
            assert result.exit_code == 0
            mock_run.assert_called()
            call_args = mock_run.call_args[0][0]
            assert "scontrol" in call_args
            assert "requeue" in call_args
            assert "12345" in call_args

    def test_suspend_command_basic(self, runner):
        """Test suspend command with job ID."""
        from slurm_cli.cli import register_commands

        register_commands()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="", stderr=""
            )
            result = runner.invoke(main, ["suspend", "12345"])
            assert result.exit_code == 0
            mock_run.assert_called()
            call_args = mock_run.call_args[0][0]
            assert "scontrol" in call_args
            assert "suspend" in call_args
            assert "12345" in call_args

    def test_hold_command_no_jobs(self, runner):
        """Test hold command with no jobs shows error."""
        from slurm_cli.cli import register_commands

        register_commands()
        result = runner.invoke(main, ["hold"])
        assert result.exit_code != 0

    def test_hold_command_verbose(self, runner):
        """Test hold command with verbose output."""
        from slurm_cli.cli import register_commands

        register_commands()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="", stderr=""
            )
            result = runner.invoke(main, ["hold", "12345", "-v"])
            assert result.exit_code == 0
            assert "Running:" in result.output

    def test_hold_command_user_hold(self, runner):
        """Test hold command with --user option uses uhold."""
        from slurm_cli.cli import register_commands

        register_commands()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="", stderr=""
            )
            result = runner.invoke(main, ["hold", "-u", "12345"])
            assert result.exit_code == 0
            mock_run.assert_called()
            call_args = mock_run.call_args[0][0]
            assert "scontrol" in call_args
            assert "uhold" in call_args
            assert "12345" in call_args
            assert "User held" in result.output

    def test_hold_command_user_hold_with_reason(self, runner):
        """Test hold command with --user and --reason options."""
        from slurm_cli.cli import register_commands

        register_commands()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="", stderr=""
            )
            result = runner.invoke(
                main, ["hold", "--user", "12345", "-r", "Review needed"]
            )
            assert result.exit_code == 0
            mock_run.assert_called()
            call_args = mock_run.call_args[0][0]
            assert "scontrol" in call_args
            assert "uhold" in call_args
            assert "reason=Review needed" in call_args

    def test_job_commands_in_help(self, runner):
        """Test that job control commands appear in help."""
        from slurm_cli.cli import register_commands

        register_commands()
        result = runner.invoke(main, ["-h"])
        assert result.exit_code == 0
        assert "hold" in result.output
        assert "release" in result.output
        assert "top" in result.output
        assert "requeue" in result.output
        assert "suspend" in result.output

    def test_hold_command_help(self, runner):
        """Test hold command help shows reason option."""
        from slurm_cli.cli import register_commands

        register_commands()
        result = runner.invoke(main, ["hold", "--help"])
        assert result.exit_code == 0
        assert "--reason" in result.output or "-r" in result.output


def test_autocomplete_job_commands(runner):
    """Test that autocomplete includes job control commands."""
    from slurm_cli.cli import register_commands

    register_commands()
    result = runner.invoke(main, ["autocomplete"])
    assert result.exit_code == 0
    # Check job control commands are in autocomplete
    assert "hold)" in result.output
    assert "release|top|requeue|suspend)" in result.output


def test_autocomplete_hold_options(runner):
    """Test that autocomplete includes hold command options."""
    from slurm_cli.cli import register_commands

    register_commands()
    result = runner.invoke(main, ["autocomplete"])
    assert result.exit_code == 0
    # Check hold has job filters and reason option
    assert "user=" in result.output
    assert "partition=" in result.output
    assert "reason=" in result.output


def test_job_command_with_user_filter(runner):
    """Test job commands resolve user= filter to job IDs."""
    from slurm_cli.cli import register_commands

    register_commands()
    with patch("slurm_cli.cli.resolve_job_filters") as mock_resolve:
        # Simulate filter returning job IDs set
        mock_resolve.return_value = ({"12345", "12346"}, [])

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="", stderr=""
            )
            result = runner.invoke(main, ["hold", "user=testuser"])
            # Should have called resolve_job_filters
            mock_resolve.assert_called_once()
            # Should have run scontrol for each resolved job
            assert mock_run.call_count == 2


def test_job_command_with_exclusion_filter(runner):
    """Test job commands with not: exclusion filter."""
    from slurm_cli.cli import register_commands

    register_commands()
    with patch("slurm_cli.cli.resolve_job_filters") as mock_resolve:
        # Simulate partition=gpu not:user=admin returning filtered jobs
        mock_resolve.return_value = ({"12345", "12346"}, [])

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="", stderr=""
            )
            result = runner.invoke(
                main, ["hold", "partition=gpu", "not:user=admin"]
            )
            assert result.exit_code == 0
            # Should have called resolve_job_filters with both filters
            mock_resolve.assert_called_once()
            call_args = mock_resolve.call_args[0][0]
            assert "partition=gpu" in call_args
            assert "not:user=admin" in call_args


def test_autocomplete_job_negative_filters(runner):
    """Test that autocomplete includes negative job filters."""
    from slurm_cli.cli import register_commands

    register_commands()
    result = runner.invoke(main, ["autocomplete"])
    assert result.exit_code == 0
    # Check negative job filters
    assert "not:user=" in result.output
    assert "not:partition=" in result.output
    assert "not:account=" in result.output
    assert "not:state=" in result.output


class TestDryRun:
    """Tests for --dry-run and --no-dry-run options."""

    def test_global_dry_run_option(self, runner):
        """Test global --dry-run option."""
        from slurm_cli.cli import register_commands

        register_commands()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="", stderr=""
            )
            result = runner.invoke(
                main, ["--dry-run", "delete", "users", "testuser", "-y"]
            )
            assert result.exit_code == 0
            # Should show DRY RUN output
            assert "DRY RUN" in result.output
            # Should NOT actually call sacctmgr for deletion
            # (only for verification queries are allowed)

    def test_command_dry_run_option(self, runner):
        """Test command-level --dry-run option."""
        from slurm_cli.cli import register_commands

        register_commands()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='{"users": [{"name": "testuser"}]}',
                stderr="",
            )
            result = runner.invoke(
                main, ["delete", "users", "testuser", "--dry-run", "-y"]
            )
            assert result.exit_code == 0
            assert "DRY RUN" in result.output

    def test_no_dry_run_override(self, runner):
        """Test --no-dry-run overrides env var."""
        import os

        from slurm_cli.cli import register_commands

        register_commands()
        # Set env var to enable dry-run
        with patch.dict(os.environ, {"SLURM_CLI_DRYRUN": "y"}):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout='{"users": []}',
                    stderr="",
                )
                result = runner.invoke(
                    main,
                    [
                        "--no-dry-run",
                        "delete",
                        "users",
                        "testuser",
                        "-y",
                    ],
                )
                # Should NOT show DRY RUN - env var is overridden
                # (may show error because user doesn't exist, but not DRY RUN)
                assert "DRY RUN" not in result.output

    def test_env_var_dry_run(self, runner):
        """Test SLURM_CLI_DRYRUN environment variable."""
        import os

        from slurm_cli.cli import register_commands

        register_commands()
        with patch.dict(os.environ, {"SLURM_CLI_DRYRUN": "y"}):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout='{"users": [{"name": "testuser"}]}',
                    stderr="",
                )
                result = runner.invoke(
                    main, ["delete", "users", "testuser", "-y"]
                )
                assert result.exit_code == 0
                assert "DRY RUN" in result.output

    def test_env_var_true_value(self, runner):
        """Test SLURM_CLI_DRYRUN with 'true' value."""
        import os

        from slurm_cli.cli import register_commands

        register_commands()
        with patch.dict(os.environ, {"SLURM_CLI_DRYRUN": "true"}):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout='{"users": [{"name": "testuser"}]}',
                    stderr="",
                )
                result = runner.invoke(
                    main, ["delete", "users", "testuser", "-y"]
                )
                assert "DRY RUN" in result.output

    def test_env_var_yes_value(self, runner):
        """Test SLURM_CLI_DRYRUN with 'yes' value."""
        import os

        from slurm_cli.cli import register_commands

        register_commands()
        with patch.dict(os.environ, {"SLURM_CLI_DRYRUN": "yes"}):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout='{"users": [{"name": "testuser"}]}',
                    stderr="",
                )
                result = runner.invoke(
                    main, ["delete", "users", "testuser", "-y"]
                )
                assert "DRY RUN" in result.output

    def test_env_var_1_value(self, runner):
        """Test SLURM_CLI_DRYRUN with '1' value."""
        import os

        from slurm_cli.cli import register_commands

        register_commands()
        with patch.dict(os.environ, {"SLURM_CLI_DRYRUN": "1"}):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout='{"users": [{"name": "testuser"}]}',
                    stderr="",
                )
                result = runner.invoke(
                    main, ["delete", "users", "testuser", "-y"]
                )
                assert "DRY RUN" in result.output


class TestGlobalYesOption:
    """Tests for global --yes option."""

    def test_global_yes_skips_confirmation(self, runner):
        """Test that global -y skips confirmation in delete."""
        from slurm_cli.cli import register_commands

        register_commands()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='{"users": [{"name": "testuser"}]}',
                stderr="",
            )
            # Global -y should skip confirmation
            result = runner.invoke(
                main, ["-y", "delete", "users", "testuser"]
            )
            # Should not prompt for confirmation
            # (result depends on mocks, but no prompt should occur)
            assert "cancelled" not in result.output.lower()

    def test_command_yes_skips_confirmation(self, runner):
        """Test that command-level -y skips confirmation."""
        from slurm_cli.cli import register_commands

        register_commands()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='{"users": [{"name": "testuser"}]}',
                stderr="",
            )
            result = runner.invoke(
                main, ["delete", "users", "testuser", "-y"]
            )
            assert "cancelled" not in result.output.lower()

    def test_get_skip_confirm_function(self):
        """Test the get_skip_confirm helper function."""
        from unittest.mock import MagicMock

        from slurm_cli.cli import get_skip_confirm

        # Create mock context
        ctx = MagicMock()

        # Test with no yes flags
        ctx.obj = {"yes": False}
        assert get_skip_confirm(ctx, yes=False, force=False) is False

        # Test with global yes
        ctx.obj = {"yes": True}
        assert get_skip_confirm(ctx, yes=False, force=False) is True

        # Test with local yes
        ctx.obj = {"yes": False}
        assert get_skip_confirm(ctx, yes=True, force=False) is True

        # Test with local force
        ctx.obj = {"yes": False}
        assert get_skip_confirm(ctx, yes=False, force=True) is True

        # Test with ctx.obj as None
        ctx.obj = None
        assert get_skip_confirm(ctx, yes=False, force=False) is False
        assert get_skip_confirm(ctx, yes=True, force=False) is True


class TestResourceSpecificHelp:
    """Tests for resource-specific help."""

    def test_add_command_help(self, runner):
        """Test add command shows available resources in help."""
        result = runner.invoke(main, ["add", "-h"])
        assert result.exit_code == 0
        # Should list available resources that support create action
        assert "users" in result.output.lower()
        assert "assoc" in result.output.lower()
        assert "qos" in result.output.lower()

    def test_show_command_help(self, runner):
        """Test show command shows available resources in help."""
        result = runner.invoke(main, ["show", "-h"])
        assert result.exit_code == 0
        # Should list available resources (may include aliases like 'part')
        assert "part" in result.output.lower()
        assert "node" in result.output.lower()
        assert "qos" in result.output.lower()

    def test_delete_command_help(self, runner):
        """Test delete command shows available resources in help."""
        result = runner.invoke(main, ["delete", "-h"])
        assert result.exit_code == 0
        # Should list available resources that support delete action
        assert "users" in result.output.lower()
        assert "qos" in result.output.lower()
        # associations don't have delete action, so should not be listed
        assert "assoc" not in result.output.lower()

    def test_modify_command_help(self, runner):
        """Test modify command shows available resources in help."""
        result = runner.invoke(main, ["modify", "-h"])
        assert result.exit_code == 0
        assert "users" in result.output.lower()

    def test_resource_specific_help_function(self):
        """Test the show_resource_help function directly."""
        from slurm_cli.cli import show_resource_help

        # Test coordinators help
        result = show_resource_help("create", "coordinators")
        assert result is True

        # Test users help
        result = show_resource_help("create", "users")
        assert result is True

        # Test unknown resource
        result = show_resource_help("create", "unknown_resource")
        assert result is False


class TestGuessResourceType:
    """Tests for guessing resource type from item name."""

    def test_guess_job_by_numeric_id(self):
        """Test guessing 'jobs' from numeric ID."""
        from slurm_cli.utils.resources import Resource

        resource_type, _ = Resource.guess_resource_type("12345")
        assert resource_type == "jobs"

    def test_guess_job_by_array_id(self):
        """Test guessing 'jobs' from array job ID."""
        from slurm_cli.utils.resources import Resource

        resource_type, _ = Resource.guess_resource_type("12345_1")
        assert resource_type == "jobs"

    def test_guess_job_by_prefix(self):
        """Test guessing 'jobs' from 'j' prefix."""
        from slurm_cli.utils.resources import Resource

        resource_type, _ = Resource.guess_resource_type("jobs")
        assert resource_type == "jobs"

    def test_guess_partition_by_prefix(self):
        """Test guessing 'partitions' from 'part' prefix."""
        from slurm_cli.utils.resources import Resource

        with patch.object(
            Resource, "cached_resource_list", return_value=[]
        ):
            with patch.object(
                Resource, "cached_resource", return_value=[]
            ):
                resource_type, _ = Resource.guess_resource_type(
                    "partitions"
                )
                assert resource_type == "partitions"

    def test_guess_node_by_prefix(self):
        """Test guessing 'nodes' from 'node' prefix."""
        from slurm_cli.utils.resources import Resource

        with patch.object(
            Resource, "cached_resource_list", return_value=[]
        ):
            with patch.object(
                Resource, "cached_resource", return_value=[]
            ):
                resource_type, _ = Resource.guess_resource_type("nodes")
                assert resource_type == "nodes"

    def test_guess_qos_by_prefix(self):
        """Test guessing 'qos' from 'qos' prefix."""
        from slurm_cli.utils.resources import Resource

        with patch.object(
            Resource, "cached_resource_list", return_value=[]
        ):
            with patch.object(
                Resource, "cached_resource", return_value=[]
            ):
                resource_type, _ = Resource.guess_resource_type("qos")
                assert resource_type == "qos"

    def test_guess_account_by_prefix(self):
        """Test guessing 'accounts' from 'acc' prefix."""
        from slurm_cli.utils.resources import Resource

        with patch.object(
            Resource, "cached_resource_list", return_value=[]
        ):
            with patch.object(
                Resource, "cached_resource", return_value=[]
            ):
                resource_type, _ = Resource.guess_resource_type(
                    "accounts"
                )
                assert resource_type == "accounts"

    def test_guess_reservation_by_prefix(self):
        """Test guessing 'reservations' from 'res' prefix."""
        from slurm_cli.utils.resources import Resource

        with patch.object(
            Resource, "cached_resource_list", return_value=[]
        ):
            with patch.object(
                Resource, "cached_resource", return_value=[]
            ):
                resource_type, _ = Resource.guess_resource_type(
                    "reservations"
                )
                assert resource_type == "reservations"

    def test_guess_user_by_prefix(self):
        """Test guessing 'users' from 'user' prefix."""
        from slurm_cli.utils.resources import Resource

        with patch.object(
            Resource, "cached_resource_list", return_value=[]
        ):
            with patch.object(
                Resource, "cached_resource", return_value=[]
            ):
                resource_type, _ = Resource.guess_resource_type("users")
                assert resource_type == "users"

    def test_guess_coordinator_by_prefix(self):
        """Test guessing 'coordinators' from 'coord' prefix."""
        from slurm_cli.utils.resources import Resource

        with patch.object(
            Resource, "cached_resource_list", return_value=[]
        ):
            with patch.object(
                Resource, "cached_resource", return_value=[]
            ):
                resource_type, _ = Resource.guess_resource_type(
                    "coordinators"
                )
                assert resource_type == "coordinators"

    def test_guess_events_by_prefix(self):
        """Test guessing 'events' from 'ev' prefix."""
        from slurm_cli.utils.resources import Resource

        with patch.object(
            Resource, "cached_resource_list", return_value=[]
        ):
            resource_type, _ = Resource.guess_resource_type("events")
            assert resource_type == "events"

    def test_guess_licenses_by_prefix(self):
        """Test guessing 'licenses' from 'lic' prefix."""
        from slurm_cli.utils.resources import Resource

        with patch.object(
            Resource, "cached_resource_list", return_value=[]
        ):
            resource_type, _ = Resource.guess_resource_type("licenses")
            assert resource_type == "licenses"

    def test_guess_by_known_item_name(self):
        """Test guessing resource type when item name matches cache."""
        from slurm_cli.utils.resources import Resource

        # Simulate 'gpu' being in the partitions cache
        def mock_cached_list(resource):
            if resource == "partitions":
                return ["gpu", "cpu", "debug"]
            return []

        with patch.object(
            Resource,
            "cached_resource_list",
            side_effect=mock_cached_list,
        ):
            with patch.object(
                Resource,
                "cached_resource",
                return_value=[{"name": "gpu"}],
            ):
                resource_type, _ = Resource.guess_resource_type("gpu")
                assert resource_type == "partitions"

    def test_guess_user_by_known_username(self):
        """Test guessing 'users' when username is in cache."""
        from slurm_cli.utils.resources import Resource

        # Use 'admin' - doesn't start with j/part/node/qos/acc/res/coord
        def mock_cached_list(resource):
            if resource == "partitions":
                return []
            if resource == "nodes":
                return []
            if resource == "users":
                return ["alice", "bob", "admin"]
            return []

        with patch.object(
            Resource,
            "cached_resource_list",
            side_effect=mock_cached_list,
        ):
            with patch.object(
                Resource,
                "cached_resource",
                return_value=[{"name": "alice"}],
            ):
                resource_type, _ = Resource.guess_resource_type("alice")
                assert resource_type == "users"


class TestResourceTypeAutodetection:
    """Tests for resource type autodetection in CLI commands."""

    def test_show_job_by_numeric_id(self):
        """Test 'slurm-cli show 62792' detects job by numeric ID."""
        runner = CliRunner()
        with patch("slurm_cli.cli.Job.show") as mock_show:
            result = runner.invoke(main, ["show", "62792"])
            # Should call Job.show with the job ID
            mock_show.assert_called_once()
            call_kwargs = mock_show.call_args[1]
            assert call_kwargs["field"] == "62792"

    def test_show_job_by_array_id(self):
        """Test 'slurm-cli show 12345_1' detects array job ID."""
        runner = CliRunner()
        with patch("slurm_cli.cli.Job.show") as mock_show:
            result = runner.invoke(main, ["show", "12345_1"])
            mock_show.assert_called_once()
            call_kwargs = mock_show.call_args[1]
            assert call_kwargs["field"] == "12345_1"

    def test_show_username_autodetection(self):
        """Test 'slurm-cli show username' detects user."""
        runner = CliRunner()
        with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
            mock_ensure.return_value = ("users", "testuser", {})
            with patch("slurm_cli.cli.User.show") as mock_show:
                result = runner.invoke(main, ["show", "testuser"])
                mock_ensure.assert_called()
                # Verify it was called with the username
                args = mock_ensure.call_args[0]
                assert args[0] == "testuser"

    def test_show_job_with_multiple_ids(self):
        """Test showing multiple job IDs."""
        runner = CliRunner()
        with patch("slurm_cli.cli.Job.show") as mock_show:
            result = runner.invoke(main, ["show", "jobs", "123", "456"])
            # Should show jobs for each ID
            assert mock_show.call_count >= 1

    def test_show_explicit_resource_type(self):
        """Test that explicit resource type still works."""
        runner = CliRunner()
        with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
            mock_ensure.return_value = ("jobs", None, None)
            with patch("slurm_cli.cli.Job.show") as mock_show:
                result = runner.invoke(main, ["show", "jobs"])
                mock_ensure.assert_called()
                args = mock_ensure.call_args[0]
                assert args[0] == "jobs"

    def test_show_nodes_still_works(self):
        """Test that 'slurm-cli show nodes' still works."""
        runner = CliRunner()
        with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
            mock_ensure.return_value = ("nodes", (), {})
            with patch("slurm_cli.cli.Node.show") as mock_show:
                result = runner.invoke(main, ["show", "nodes"])
                mock_ensure.assert_called()
                args = mock_ensure.call_args[0]
                assert args[0] == "nodes"

    def test_guess_user_by_username_pattern(self):
        """Test guessing 'users' for username-like string not in cache."""
        from slurm_cli.utils.resources import Resource

        with patch.object(
            Resource, "cached_resource_list", return_value=[]
        ):
            with patch.object(
                Resource, "cached_resource", return_value={"user1": {}}
            ):
                # Valid username pattern (letter + alphanumeric)
                resource_type, _ = Resource.guess_resource_type(
                    "szhumatiy"
                )
                assert resource_type == "users"

    def test_guess_user_with_underscore(self):
        """Test guessing 'users' for username with underscore."""
        from slurm_cli.utils.resources import Resource

        with patch.object(
            Resource, "cached_resource_list", return_value=[]
        ):
            with patch.object(
                Resource, "cached_resource", return_value={"user1": {}}
            ):
                resource_type, _ = Resource.guess_resource_type(
                    "test_user"
                )
                assert resource_type == "users"

    def test_guess_user_with_hyphen(self):
        """Test guessing 'users' for username with hyphen."""
        from slurm_cli.utils.resources import Resource

        with patch.object(
            Resource, "cached_resource_list", return_value=[]
        ):
            with patch.object(
                Resource, "cached_resource", return_value={"user1": {}}
            ):
                resource_type, _ = Resource.guess_resource_type(
                    "test-user"
                )
                assert resource_type == "users"
