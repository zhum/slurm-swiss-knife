"""Tests for the coordinators module."""

import io
import subprocess
import sys
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

import pytest  # noqa: F401

# Add src to path for imports
sys.path.insert(0, "src")

from slurm_cli.utils.coordinators import Coordinator  # noqa: E402


def create_mock_subprocess_result(
    stdout: str = "", returncode: int = 0
):
    """Create a mock subprocess.CompletedProcess result."""
    mock_result = MagicMock()
    mock_result.stdout = stdout
    mock_result.returncode = returncode
    return mock_result


class TestCoordinatorInit:
    """Tests for Coordinator.__init__ method."""

    def test_coordinator_init_with_name(self):
        """Test Coordinator initialization with just name."""
        coordinator = Coordinator("testcoord")
        assert coordinator.name == "testcoord"
        assert coordinator.kwargs == {}

    def test_coordinator_init_with_kwargs(self):
        """Test Coordinator initialization with additional kwargs."""
        coordinator = Coordinator(
            "testcoord",
            account="myaccount",
            user="myuser",
        )
        assert coordinator.name == "testcoord"
        assert coordinator.kwargs["account"] == "myaccount"
        assert coordinator.kwargs["user"] == "myuser"


class TestCoordinatorCreate:
    """Tests for Coordinator.create method."""

    def test_create_coordinator_success(self):
        """Test successful coordinator creation."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Coordinator.create("myaccount", value="myuser")

            result = output.getvalue()
            assert "created successfully" in result

    def test_create_coordinator_with_stdout(self):
        """Test coordinator creation with subprocess stdout."""
        mock_result = create_mock_subprocess_result(
            stdout="Coordinator added successfully"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Coordinator.create("myaccount", value="myuser")

            result = output.getvalue()
            assert "Coordinator added successfully" in result

    def test_create_coordinator_missing_args(self):
        """Test coordinator creation without required args."""
        output = io.StringIO()
        with redirect_stdout(output):
            Coordinator.create("myaccount")  # No value or names

        result = output.getvalue()
        assert "creation failed" in result
        assert "slurm-cli create coordinator" in result

    def test_create_coordinator_with_names(self):
        """Test coordinator creation with names tuple."""
        mock_result = create_mock_subprocess_result()
        with patch.object(
            subprocess, "run", return_value=mock_result
        ) as mock_run:
            Coordinator.create(
                "myaccount", value="user1", names=("extra",)
            )

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "sacctmgr" in call_args
            assert "add" in call_args
            assert "coordinator" in call_args
            assert "accounts=myaccount" in call_args
            assert "names=user1" in call_args

    def test_create_coordinator_failure(self):
        """Test coordinator creation failure handling."""
        error = subprocess.CalledProcessError(
            1, "sacctmgr", stderr="Permission denied"
        )
        with patch.object(subprocess, "run", side_effect=error):
            output = io.StringIO()
            with redirect_stdout(output):
                Coordinator.create("myaccount", value="myuser")

            result = output.getvalue()
            assert "Failed to create coordinator" in result

    def test_create_coordinator_failure_without_stderr(self):
        """Test coordinator creation failure without stderr."""
        error = subprocess.CalledProcessError(1, "sacctmgr")
        with patch.object(subprocess, "run", side_effect=error):
            output = io.StringIO()
            with redirect_stdout(output):
                Coordinator.create("myaccount", value="myuser")

            result = output.getvalue()
            assert "Failed to create coordinator" in result


class TestCoordinatorUpdate:
    """Tests for Coordinator.update method."""

    def test_update_coordinator(self):
        """Test coordinator update method."""
        output = io.StringIO()
        with redirect_stdout(output):
            Coordinator.update("testcoord", account="newaccount")

        result = output.getvalue()
        assert "Updating coordinator: testcoord" in result


class TestCoordinatorDelete:
    """Tests for Coordinator.delete method."""

    def test_delete_coordinator(self):
        """Test coordinator delete method."""
        output = io.StringIO()
        with redirect_stdout(output):
            Coordinator.delete("testcoord")

        result = output.getvalue()
        assert "Deleting coordinator: testcoord" in result


class TestCoordinatorShow:
    """Tests for Coordinator.show method."""

    def test_show_json_style(self):
        """Test show with JSON style."""
        mock_result = create_mock_subprocess_result(
            stdout='{"coordinators": []}'
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Coordinator.show(style="json")

            result = output.getvalue()
            assert "Showing coordinator" in result

    def test_show_pretty_style(self):
        """Test show with pretty style (default)."""
        mock_result = create_mock_subprocess_result(
            stdout="Account      Coordinator\nmyaccount    myuser\n"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Coordinator.show(style="pretty")

            result = output.getvalue()
            assert "Showing coordinator" in result

    def test_show_default_style(self):
        """Test show with default style."""
        mock_result = create_mock_subprocess_result(
            stdout="Account Coordinator\n"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Coordinator.show()

            result = output.getvalue()
            assert "Showing coordinator" in result

    def test_show_with_field(self):
        """Test show with field parameter."""
        mock_result = create_mock_subprocess_result(
            stdout="Account Coordinator\nmyaccount myuser\n"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Coordinator.show(field="myaccount")

            result = output.getvalue()
            assert "myaccount" in result

    def test_show_empty_output_json(self):
        """Test show with empty JSON output."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Coordinator.show(style="json")

            # Should not crash, just no output
            result = output.getvalue()
            assert "Showing coordinator" in result

    def test_show_empty_output_pretty(self):
        """Test show with empty pretty output."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Coordinator.show(style="pretty")

            # Should not crash
            result = output.getvalue()
            assert "Showing coordinator" in result

    def test_show_subprocess_error(self):
        """Test show with subprocess error."""
        error = subprocess.CalledProcessError(
            1, "sacctmgr", stderr="Permission denied"
        )
        with patch.object(subprocess, "run", side_effect=error):
            output = io.StringIO()
            with redirect_stdout(output):
                Coordinator.show()

            result = output.getvalue()
            assert "Failed to show coordinators" in result

    def test_show_subprocess_error_without_stderr(self):
        """Test show with subprocess error without stderr."""
        error = subprocess.CalledProcessError(1, "sacctmgr")
        with patch.object(subprocess, "run", side_effect=error):
            output = io.StringIO()
            with redirect_stdout(output):
                Coordinator.show()

            result = output.getvalue()
            assert "Failed to show coordinators" in result

    def test_show_with_profile_str(self):
        """Test show with profile_str parameter."""
        mock_result = create_mock_subprocess_result(
            stdout="Account Coordinator\n"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Coordinator.show(profile_str="[cyan]{name}[/]")

            result = output.getvalue()
            assert "Showing coordinator" in result

    def test_show_with_delimiter(self):
        """Test show with delimiter parameter."""
        mock_result = create_mock_subprocess_result(
            stdout="Account Coordinator\n"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Coordinator.show(delimiter="|")

            result = output.getvalue()
            assert "Showing coordinator" in result


class TestCoordinatorInheritance:
    """Tests for Coordinator class inheritance."""

    def test_coordinator_inherits_from_base_resource(self):
        """Test that Coordinator inherits from BaseSlurmResource."""
        from slurm_cli.utils.base_resource import BaseSlurmResource

        assert issubclass(Coordinator, BaseSlurmResource)

    def test_coordinator_has_required_methods(self):
        """Test that Coordinator has all required methods."""
        assert hasattr(Coordinator, "create")
        assert hasattr(Coordinator, "update")
        assert hasattr(Coordinator, "delete")
        assert hasattr(Coordinator, "show")
        assert callable(Coordinator.create)
        assert callable(Coordinator.update)
        assert callable(Coordinator.delete)
        assert callable(Coordinator.show)
