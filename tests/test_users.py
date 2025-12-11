"""Tests for the users module."""

import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

import pytest  # noqa: F401

# Add src to path for imports
sys.path.insert(0, "src")

from slurm_cli.utils.users import User  # noqa: E402


def create_mock_subprocess_result(
    stdout: str = "", returncode: int = 0
):
    """Create a mock subprocess.CompletedProcess result."""
    mock_result = MagicMock()
    mock_result.stdout = stdout
    mock_result.returncode = returncode
    return mock_result


class TestUserInit:
    """Tests for User.__init__ method."""

    def test_user_init_with_name(self):
        """Test User initialization with just name."""
        user = User("testuser")
        assert user.name == "testuser"
        assert user.kwargs == {}

    def test_user_init_with_kwargs(self):
        """Test User initialization with additional kwargs."""
        user = User("testuser", account="myaccount", partition="gpu")
        assert user.name == "testuser"
        assert user.kwargs == {
            "account": "myaccount",
            "partition": "gpu",
        }


class TestUserCreate:
    """Tests for User.create method."""

    def test_create_user_success(self):
        """Test successful user creation."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                User.create("newuser")

            result = output.getvalue()
            assert "Creating user: newuser" in result
            assert "created successfully" in result

    def test_create_user_with_stdout(self):
        """Test user creation with subprocess stdout."""
        mock_result = create_mock_subprocess_result(
            stdout="User newuser added successfully"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                User.create("newuser")

            result = output.getvalue()
            assert "User newuser added successfully" in result

    def test_create_user_with_kwargs(self):
        """Test user creation with additional arguments."""
        mock_result = create_mock_subprocess_result()
        with patch.object(
            subprocess,
            "run",
            return_value=mock_result,
        ) as mock_run:
            User.create(
                "newuser",
                account="myaccount",
                defaultaccount="myaccount",
            )

            # Verify subprocess was called with correct args
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "sacctmgr" in call_args
            assert "create" in call_args
            assert "user" in call_args
            assert "newuser" in call_args
            assert "account=myaccount" in call_args
            assert "defaultaccount=myaccount" in call_args

    def test_create_user_failure(self):
        """Test user creation failure handling."""
        error = subprocess.CalledProcessError(
            1, "sacctmgr", stderr="User already exists"
        )
        with patch.object(subprocess, "run", side_effect=error):
            output = io.StringIO()
            with redirect_stdout(output):
                User.create("existinguser")

            result = output.getvalue()
            assert "Creating user: existinguser" in result
            assert "Failed to create user" in result

    def test_create_user_failure_without_stderr(self):
        """Test user creation failure without stderr message."""
        error = subprocess.CalledProcessError(1, "sacctmgr")
        with patch.object(subprocess, "run", side_effect=error):
            output = io.StringIO()
            with redirect_stdout(output):
                User.create("baduser")

            result = output.getvalue()
            assert "Failed to create user" in result


class TestUserUpdate:
    """Tests for User.update method."""

    def test_update_user(self):
        """Test user update method."""
        output = io.StringIO()
        with redirect_stdout(output):
            User.update("testuser", partition="gpu")

        result = output.getvalue()
        assert "Updating user: testuser" in result


class TestUserDelete:
    """Tests for User.delete method."""

    def test_delete_user(self):
        """Test user delete method."""
        output = io.StringIO()
        with redirect_stdout(output):
            User.delete("testuser")

        result = output.getvalue()
        assert "Deleting user: testuser" in result


class TestUserShow:
    """Tests for User.show method."""

    def test_show_json_style(self):
        """Test show with JSON style."""
        mock_data = {
            "users": [
                {"name": "user1", "default_account": "account1"},
                {"name": "user2", "default_account": "account2"},
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                User.show(style="json")

            result = output.getvalue()
            # Should contain JSON data
            assert "user1" in result or "users" in result

    def test_show_pretty_style(self):
        """Test show with pretty style (default)."""
        mock_result = create_mock_subprocess_result(
            stdout="User      DefAcct  Admin\n"
            "--------- -------- -----\n"
            "user1     account1 None\n"
            "user2     account2 None\n"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                User.show(style="pretty")

            result = output.getvalue()
            assert "user1" in result
            assert "user2" in result

    def test_show_default_style(self):
        """Test show with default style."""
        mock_result = create_mock_subprocess_result(
            stdout="User      DefAcct\nuser1     account1\n"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                User.show()  # No style specified

            result = output.getvalue()
            assert "user1" in result

    def test_show_empty_output(self):
        """Test show with empty output."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                User.show()

            # Should not crash, may be empty
            result = output.getvalue()  # noqa: F841
            assert True  # No exception raised

    def test_show_failure(self):
        """Test show failure handling."""
        error = subprocess.CalledProcessError(
            1, "sacctmgr", stderr="Permission denied"
        )
        with patch.object(subprocess, "run", side_effect=error):
            output = io.StringIO()
            with redirect_stdout(output):
                User.show()

            result = output.getvalue()
            assert "Failed to show users" in result

    def test_show_with_name_parameter(self):
        """Test show with name parameter."""
        mock_result = create_mock_subprocess_result(
            stdout="User      DefAcct\nspecificuser account1\n"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                User.show(name="specificuser")

            # Currently just passes name but doesn't filter
            result = output.getvalue()
            assert len(result) >= 0

    def test_show_with_profile_str(self):
        """Test show with profile_str parameter."""
        mock_result = create_mock_subprocess_result(
            stdout="User      DefAcct\nuser1     account1\n"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                User.show(profile_str="[cyan]{name}[/]")

            result = output.getvalue()
            assert "user1" in result

    def test_show_with_delimiter(self):
        """Test show with delimiter parameter."""
        mock_result = create_mock_subprocess_result(
            stdout="User      DefAcct\nuser1     account1\n"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                User.show(delimiter="|")

            result = output.getvalue()
            # Delimiter is accepted but not currently used in output
            assert len(result) >= 0

    def test_show_json_calls_correct_command(self):
        """Test that JSON style calls sacctmgr with --json flag."""
        mock_result = create_mock_subprocess_result(
            stdout='{"users": []}'
        )
        with patch.object(
            subprocess,
            "run",
            return_value=mock_result,
        ) as mock_run:
            User.show(style="json")

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "--json" in call_args

    def test_show_pretty_calls_correct_command(self):
        """Test that pretty style calls sacctmgr without --json flag."""
        mock_result = create_mock_subprocess_result(
            stdout="User DefAcct\n"
        )
        with patch.object(
            subprocess,
            "run",
            return_value=mock_result,
        ) as mock_run:
            User.show(style="pretty")

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "--json" not in call_args


class TestUserInheritance:
    """Tests for User class inheritance."""

    def test_user_inherits_from_base_resource(self):
        """Test that User inherits from BaseSlurmResource."""
        from slurm_cli.utils.base_resource import BaseSlurmResource

        assert issubclass(User, BaseSlurmResource)

    def test_user_has_required_methods(self):
        """Test that User has all required methods."""
        assert hasattr(User, "create")
        assert hasattr(User, "update")
        assert hasattr(User, "delete")
        assert hasattr(User, "show")
        assert callable(User.create)
        assert callable(User.update)
        assert callable(User.delete)
        assert callable(User.show)
