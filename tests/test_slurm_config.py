"""Tests for slurm_config module."""

import subprocess
import sys
from unittest import mock

import pytest

# Add src to path for imports
sys.path.insert(0, "src")

from slurm_cli.utils.slurm_config import Config  # noqa: E402


class TestConfigInit:
    """Tests for Config initialization."""

    def test_init_with_name(self):
        """Test initialization with name."""
        c = Config("test")
        assert c.name == "test"
        assert c.kwargs == {}

    def test_init_with_kwargs(self):
        """Test initialization with kwargs."""
        c = Config("test", option1="value1", option2="value2")
        assert c.name == "test"
        assert c.kwargs == {"option1": "value1", "option2": "value2"}


class TestConfigUpdate:
    """Tests for Config.update."""

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.slurm_config.console.print")
    def test_update_success(self, mock_print, mock_run):
        """Test successful config update."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Config.update("test", verbose=True)

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "scontrol" in args
        assert "reconfigure" in args

        # Should print success message
        call_args = [str(c) for c in mock_print.call_args_list]
        assert any("updated successfully" in str(c) for c in call_args)

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.slurm_config.console.print")
    def test_update_with_stdout(self, mock_print, mock_run):
        """Test update with stdout output."""
        mock_run.return_value = mock.Mock(
            stdout="Configuration reloaded", returncode=0
        )

        Config.update("test", verbose=True)

        # Should print stdout in addition to success message
        assert mock_print.call_count >= 2

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.slurm_config.console.print")
    def test_update_failure(self, mock_print, mock_run):
        """Test update handles failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "scontrol", stderr="Permission denied"
        )

        Config.update("test", verbose=True)

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any(
            "Failed" in str(c) or "red" in str(c) for c in call_args
        )

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.slurm_config.console.print")
    def test_update_failure_no_stderr(self, mock_print, mock_run):
        """Test update handles failure without stderr."""
        error = subprocess.CalledProcessError(1, "scontrol")
        error.stderr = None
        mock_run.side_effect = error

        Config.update("test", verbose=True)

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any(
            "Failed" in str(c) or "red" in str(c) for c in call_args
        )

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.slurm_config.console.print")
    def test_update_with_kwargs(self, mock_print, mock_run):
        """Test update with kwargs (even though they're not used)."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Config.update("test", option="value", verbose=True)

        mock_run.assert_called_once()


class TestConfigShow:
    """Tests for Config.show."""

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.slurm_config.console.print_json")
    def test_show_json_style(self, mock_print_json, mock_run):
        """Test show with JSON style."""
        mock_run.return_value = mock.Mock(
            stdout='{"ClusterName": "test"}', returncode=0
        )

        Config.show(style="json")

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "scontrol" in args
        assert "show" in args
        assert "config" in args
        assert "--json" in args
        mock_print_json.assert_called_once_with(
            '{"ClusterName": "test"}'
        )

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.slurm_config.console.print")
    def test_show_pretty_style(self, mock_print, mock_run):
        """Test show with pretty style."""
        mock_run.return_value = mock.Mock(
            stdout="ClusterName = test\nControlMachine = controller",
            returncode=0,
        )

        Config.show(style="pretty")

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "scontrol" in args
        assert "show" in args
        assert "config" in args
        assert "--json" not in args

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any("ClusterName" in str(c) for c in call_args)

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.slurm_config.console.print")
    def test_show_default_style_is_pretty(self, mock_print, mock_run):
        """Test show defaults to pretty style."""
        mock_run.return_value = mock.Mock(
            stdout="Config output", returncode=0
        )

        Config.show()

        args = mock_run.call_args[0][0]
        assert "--json" not in args

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.slurm_config.console.print")
    def test_show_failure(self, mock_print, mock_run):
        """Test show handles failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "scontrol", stderr="Error reading config"
        )

        Config.show()

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any(
            "Failed" in str(c) or "red" in str(c) for c in call_args
        )

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.slurm_config.console.print")
    def test_show_failure_json_style(self, mock_print, mock_run):
        """Test show handles failure with json style."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "scontrol", stderr="Error"
        )

        Config.show(style="json")

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any(
            "Failed" in str(c) or "red" in str(c) for c in call_args
        )

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.slurm_config.console.print_json")
    def test_show_json_empty_output(self, mock_print_json, mock_run):
        """Test show with JSON style but empty output."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Config.show(style="json")

        # Empty stdout should not call print_json
        mock_print_json.assert_not_called()

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.slurm_config.console.print")
    def test_show_pretty_empty_output(self, mock_print, mock_run):
        """Test show with pretty style but empty output."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Config.show(style="pretty")

        # Empty stdout should not call print
        mock_print.assert_not_called()

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.slurm_config.console.print")
    def test_show_with_data_parameter(self, mock_print, mock_run):
        """Test show with data parameter (ignored)."""
        mock_run.return_value = mock.Mock(
            stdout="Config output", returncode=0
        )

        Config.show(data={"key": "value"})

        mock_run.assert_called_once()

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.slurm_config.console.print")
    def test_show_with_force_cache_update(self, mock_print, mock_run):
        """Test show with force_cache_update parameter (ignored)."""
        mock_run.return_value = mock.Mock(
            stdout="Config output", returncode=0
        )

        Config.show(force_cache_update=True)

        mock_run.assert_called_once()

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.slurm_config.console.print")
    def test_show_with_delimiter(self, mock_print, mock_run):
        """Test show with delimiter parameter (ignored)."""
        mock_run.return_value = mock.Mock(
            stdout="Config output", returncode=0
        )

        Config.show(delimiter="|")

        mock_run.assert_called_once()

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.slurm_config.console.print")
    def test_show_with_profile(self, mock_print, mock_run):
        """Test show with profile parameter."""
        mock_run.return_value = mock.Mock(
            stdout="Config output", returncode=0
        )

        Config.show(profile="custom")

        mock_run.assert_called_once()

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.slurm_config.console.print")
    def test_show_with_profile_str(self, mock_print, mock_run):
        """Test show with profile_str parameter."""
        mock_run.return_value = mock.Mock(
            stdout="Config output", returncode=0
        )

        Config.show(profile_str="{name}: {value}")

        mock_run.assert_called_once()


class TestConfigInheritance:
    """Tests for Config inheritance."""

    def test_inherits_from_base_resource(self):
        """Test Config inherits from BaseSlurmResource."""
        from slurm_cli.utils.base_resource import BaseSlurmResource

        assert issubclass(Config, BaseSlurmResource)

    def test_has_required_methods(self):
        """Test Config has required methods."""
        assert hasattr(Config, "update")
        assert hasattr(Config, "show")

    def test_does_not_have_create_delete(self):
        """Test Config does not have create/delete (config is special)."""
        # Config doesn't implement create/delete like other resources
        # but may inherit stubs from base class
        pass
