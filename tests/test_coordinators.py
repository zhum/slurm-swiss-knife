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


def create_mock_subprocess_result(stdout: str = "", returncode: int = 0):
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
                Coordinator.create(user_name="myuser", account="myaccount")

            result = output.getvalue()
            assert "added" in result.lower()
            assert "successfully" in result.lower()

    def test_create_coordinator_with_stdout(self):
        """Test coordinator creation with subprocess stdout."""
        mock_result = create_mock_subprocess_result(
            stdout="Coordinator added successfully"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Coordinator.create(user_name="myuser", account="myaccount")

            result = output.getvalue()
            assert "Coordinator added successfully" in result

    def test_create_coordinator_missing_account(self):
        """Test coordinator creation without account."""
        output = io.StringIO()
        with redirect_stdout(output):
            Coordinator.create(user_name="myuser")

        result = output.getvalue()
        assert "account= is required" in result

    def test_create_coordinator_missing_user(self):
        """Test coordinator creation without user name."""
        output = io.StringIO()
        with redirect_stdout(output):
            Coordinator.create(account="myaccount")

        result = output.getvalue()
        assert "User name is required" in result

    def test_create_coordinator_with_verbose(self):
        """Test coordinator creation with verbose output."""
        mock_result = create_mock_subprocess_result()
        with patch.object(subprocess, "run", return_value=mock_result) as mock_run:
            output = io.StringIO()
            with redirect_stdout(output):
                Coordinator.create(
                    user_name="user1",
                    account="myaccount",
                    verbose=True,
                )

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "sacctmgr" in call_args
            assert "add" in call_args
            assert "coordinator" in call_args
            assert "accounts=myaccount" in call_args
            assert "names=user1" in call_args

            result = output.getvalue()
            assert "Running:" in result

    def test_create_coordinator_failure(self):
        """Test coordinator creation failure handling."""
        error = subprocess.CalledProcessError(1, "sacctmgr", stderr="Permission denied")
        with patch.object(subprocess, "run", side_effect=error):
            output = io.StringIO()
            with redirect_stdout(output):
                Coordinator.create(user_name="myuser", account="myaccount")

            result = output.getvalue()
            assert "Failed to create coordinator" in result

    def test_create_coordinator_failure_without_stderr(self):
        """Test coordinator creation failure without stderr."""
        error = subprocess.CalledProcessError(1, "sacctmgr")
        with patch.object(subprocess, "run", side_effect=error):
            output = io.StringIO()
            with redirect_stdout(output):
                Coordinator.create(user_name="myuser", account="myaccount")

            result = output.getvalue()
            assert "Failed to create coordinator" in result


class TestCoordinatorUpdate:
    """Tests for Coordinator.update method."""

    def test_update_coordinator_not_supported(self):
        """Test coordinator update shows not supported error."""
        output = io.StringIO()
        with redirect_stdout(output):
            Coordinator.update("testaccount", name="testuser")

        result = output.getvalue()
        assert "not supported" in result.lower()
        assert "coordinators" in result.lower()


class TestCoordinatorDelete:
    """Tests for Coordinator.delete method."""

    @patch("slurm_cli.utils.coordinators.subprocess.run")
    def test_delete_coordinator(self, mock_run):
        """Test coordinator delete method."""
        mock_run.return_value = MagicMock(stdout="", stderr="")

        Coordinator.delete("testaccount", names=["testuser"])
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "delete" in call_args
        assert "coordinator" in call_args
        assert "account=testaccount" in call_args
        assert "name=testuser" in call_args

    def test_delete_coordinator_no_names(self):
        """Test coordinator delete without names shows error."""
        output = io.StringIO()
        with redirect_stdout(output):
            Coordinator.delete("testaccount")

        result = output.getvalue()
        assert "No coordinator names specified" in result


def create_mock_coord_json(coordinators=None):
    """Create mock JSON output for coordinators (from accounts)."""
    import json

    if coordinators is None:
        coordinators = []

    accounts = []
    for coord in coordinators:
        accounts.append(
            {
                "name": coord.get("account", "testaccount"),
                "description": "Test account",
                "organization": "test",
                "coordinators": [
                    {
                        "name": coord.get("name", "testuser"),
                        "direct": coord.get("direct", True),
                    }
                ],
                "flags": [],
            }
        )

    return json.dumps({"accounts": accounts})


class TestCoordinatorShow:
    """Tests for Coordinator.show method."""

    def test_show_json_style(self):
        """Test show with JSON style."""
        mock_json = create_mock_coord_json(
            [{"name": "testuser", "account": "testaccount"}]
        )
        mock_result = create_mock_subprocess_result(stdout=mock_json)
        with patch.object(subprocess, "run", return_value=mock_result):
            Coordinator.show(style="json")
            # Should not crash

    def test_show_pretty_style(self):
        """Test show with pretty style (default)."""
        mock_json = create_mock_coord_json([{"name": "myuser", "account": "myaccount"}])
        mock_result = create_mock_subprocess_result(stdout=mock_json)
        with patch.object(subprocess, "run", return_value=mock_result):
            Coordinator.show(style="pretty")
            # Should not crash

    def test_show_default_style(self):
        """Test show with default style."""
        mock_json = create_mock_coord_json(
            [{"name": "testuser", "account": "testaccount"}]
        )
        mock_result = create_mock_subprocess_result(stdout=mock_json)
        with patch.object(subprocess, "run", return_value=mock_result):
            Coordinator.show()
            # Should not crash

    def test_show_with_field(self):
        """Test show with field parameter (filter by name)."""
        mock_json = create_mock_coord_json(
            [
                {"name": "myuser", "account": "myaccount"},
                {"name": "otheruser", "account": "otheraccount"},
            ]
        )
        mock_result = create_mock_subprocess_result(stdout=mock_json)
        with patch.object(subprocess, "run", return_value=mock_result):
            Coordinator.show(field="myuser")
            # Should not crash

    def test_show_with_account_filter(self):
        """Test show with account filter."""
        mock_json = create_mock_coord_json(
            [{"name": "testuser", "account": "myaccount"}]
        )
        mock_result = create_mock_subprocess_result(stdout=mock_json)
        with patch.object(subprocess, "run", return_value=mock_result):
            Coordinator.show(field="account=myaccount")
            # Should not crash

    def test_show_empty_output_json(self):
        """Test show with empty JSON output."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(subprocess, "run", return_value=mock_result):
            Coordinator.show(style="json")
            # Should not crash, prints "No coordinators found"

    def test_show_empty_output_pretty(self):
        """Test show with empty pretty output."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(subprocess, "run", return_value=mock_result):
            Coordinator.show(style="pretty")
            # Should not crash

    def test_show_no_coordinators(self):
        """Test show when accounts have no coordinators."""
        mock_json = '{"accounts": [{"name": "test", "coordinators": []}]}'
        mock_result = create_mock_subprocess_result(stdout=mock_json)
        with patch.object(subprocess, "run", return_value=mock_result):
            Coordinator.show()
            # Should print "No coordinators found"

    def test_show_subprocess_error(self):
        """Test show with subprocess error."""
        error = subprocess.CalledProcessError(1, "sacctmgr", stderr="Permission denied")
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
        mock_json = create_mock_coord_json(
            [{"name": "testuser", "account": "testaccount"}]
        )
        mock_result = create_mock_subprocess_result(stdout=mock_json)
        with patch.object(subprocess, "run", return_value=mock_result):
            Coordinator.show(profile_str="coordinators.columns=name,account")
            # Should not crash

    def test_show_with_delimiter(self):
        """Test show with delimiter parameter (CSV output)."""
        mock_json = create_mock_coord_json(
            [{"name": "testuser", "account": "testaccount"}]
        )
        mock_result = create_mock_subprocess_result(stdout=mock_json)
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Coordinator.show(style="csv", delimiter="|")

            result = output.getvalue()
            assert "|" in result


class TestCoordinatorAutocomplete:
    """Tests for Coordinator.generate_autocomplete_options method."""

    def test_generate_autocomplete_returns_string(self):
        """Test that generate_autocomplete_options returns a string."""
        result = Coordinator.generate_autocomplete_options()
        assert isinstance(result, str)

    def test_autocomplete_contains_function_definition(self):
        """Test autocomplete script contains function definition."""
        result = Coordinator.generate_autocomplete_options()
        assert "_slurm_cli_coordinators_autocomplete()" in result

    def test_autocomplete_contains_options(self):
        """Test autocomplete script includes options."""
        result = Coordinator.generate_autocomplete_options()
        assert "account=" in result
        assert "name=" in result
        assert "user=" in result


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
        assert hasattr(Coordinator, "generate_autocomplete_options")
        assert callable(Coordinator.generate_autocomplete_options)
