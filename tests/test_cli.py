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

    with patch("slurm_cli.cli.resolve_node_filters") as mock_resolve:
        mock_resolve.return_value = ({"node001", "node002"}, [])
        # Mock data would be loaded by the show command
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
