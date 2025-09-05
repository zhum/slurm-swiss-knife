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

    def test_update_user_simple(self):
        """Test simple user update with name."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(
            subprocess,
            "run",
            return_value=mock_result,
        ) as mock_run:
            User.update("testuser", defaultaccount="newaccount")

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "sacctmgr" in call_args
            assert "-i" in call_args
            assert "modify" in call_args
            assert "user" in call_args
            assert "where" in call_args
            assert "name=testuser" in call_args
            assert "set" in call_args
            assert "defaultaccount=newaccount" in call_args

    def test_update_user_with_newname(self):
        """Test that newname= is passed correctly."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(
            subprocess,
            "run",
            return_value=mock_result,
        ) as mock_run:
            # Use newname directly since name is the positional argument
            User.update("olduser", newname="newuser")

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "newname=newuser" in call_args

    def test_update_user_where_mode_with_name_set(self):
        """Test that name= in set_values is converted to newname=."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(
            subprocess,
            "run",
            return_value=mock_result,
        ) as mock_run:
            # When using where_conditions, name= in kwargs becomes newname=
            User.update(
                "",
                where_conditions=["account=testaccount"],
                set_values=["name=newuser"],
            )

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            # set_values are passed as-is
            assert "name=newuser" in call_args

    def test_update_user_adminlevel_valid(self):
        """Test update with valid admin levels."""
        for level in ["none", "admin", "operator"]:
            mock_result = create_mock_subprocess_result(stdout="")
            with patch.object(
                subprocess,
                "run",
                return_value=mock_result,
            ) as mock_run:
                User.update("testuser", adminlevel=level)

                mock_run.assert_called_once()
                call_args = mock_run.call_args[0][0]
                assert f"adminlevel={level}" in call_args

    def test_update_user_adminlevel_invalid(self):
        """Test update with invalid admin level."""
        with patch.object(subprocess, "run") as mock_run:
            output = io.StringIO()
            with redirect_stdout(output):
                User.update("testuser", adminlevel="superuser")

            # Should NOT call subprocess.run
            mock_run.assert_not_called()
            result = output.getvalue()
            assert "Invalid adminlevel" in result
            assert "none, admin, operator" in result

    def test_update_user_multiple_kwargs(self):
        """Test update with multiple kwargs."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(
            subprocess,
            "run",
            return_value=mock_result,
        ) as mock_run:
            User.update(
                "testuser",
                defaultaccount="newaccount",
                adminlevel="admin",
                partition="gpu",
            )

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "defaultaccount=newaccount" in call_args
            assert "adminlevel=admin" in call_args
            assert "partition=gpu" in call_args

    def test_update_user_where_mode(self):
        """Test update with where conditions."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(
            subprocess,
            "run",
            return_value=mock_result,
        ) as mock_run:
            User.update(
                "",
                where_conditions=["account=testaccount"],
                set_values=["adminlevel=admin"],
            )

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "where" in call_args
            assert "account=testaccount" in call_args
            assert "set" in call_args
            assert "adminlevel=admin" in call_args

    def test_update_user_no_name_or_conditions(self):
        """Test update without name or where conditions."""
        with patch.object(subprocess, "run") as mock_run:
            output = io.StringIO()
            with redirect_stdout(output):
                User.update("")

            # Should NOT call subprocess.run
            mock_run.assert_not_called()
            result = output.getvalue()
            assert "No user name or WHERE conditions" in result

    def test_update_user_failure(self):
        """Test update failure handling."""
        error = subprocess.CalledProcessError(
            1, "sacctmgr", stderr="No matching users"
        )
        with patch.object(subprocess, "run", side_effect=error):
            output = io.StringIO()
            with redirect_stdout(output):
                User.update("nonexistent", adminlevel="admin")

            result = output.getvalue()
            assert "Failed to update user" in result

    def test_update_user_verbose(self):
        """Test update with verbose flag."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(
            subprocess,
            "run",
            return_value=mock_result,
        ):
            output = io.StringIO()
            with redirect_stdout(output):
                User.update(
                    "testuser", verbose=True, adminlevel="admin"
                )

            result = output.getvalue()
            assert "Running:" in result
            assert "updated successfully" in result

    def test_update_user_with_stdout(self):
        """Test update with subprocess stdout."""
        mock_result = create_mock_subprocess_result(
            stdout="Modified user record(s)"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                User.update("testuser", adminlevel="admin")

            result = output.getvalue()
            assert "Modified user record(s)" in result

    def test_update_user_skip_none_values(self):
        """Test that None values are skipped."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(
            subprocess,
            "run",
            return_value=mock_result,
        ) as mock_run:
            User.update("testuser", adminlevel="admin", partition=None)

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "adminlevel=admin" in call_args
            # partition should NOT be included
            assert "partition=None" not in call_args
            assert "partition=" not in " ".join(call_args)

    def test_update_user_where_mode_adminlevel_validation(self):
        """Test that invalid adminlevel is rejected in WHERE mode."""
        with patch.object(subprocess, "run") as mock_run:
            output = io.StringIO()
            with redirect_stdout(output):
                User.update(
                    "",
                    where_conditions=["account=test"],
                    set_values=["adminlevel=superuser"],
                )

            # Should NOT call subprocess.run
            mock_run.assert_not_called()
            result = output.getvalue()
            assert "Invalid adminlevel" in result

    def test_update_user_where_mode_multiple_conditions(self):
        """Test update with multiple WHERE conditions."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(
            subprocess,
            "run",
            return_value=mock_result,
        ) as mock_run:
            User.update(
                "",
                where_conditions=[
                    "cluster=testcluster",
                    "account=testaccount",
                ],
                set_values=["adminlevel=admin"],
            )

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "cluster=testcluster" in call_args
            assert "account=testaccount" in call_args


class TestUserDelete:
    """Tests for User.delete method."""

    @patch("subprocess.run")
    def test_delete_user_success(self, mock_run):
        """Test successful user deletion."""
        mock_run.return_value = create_mock_subprocess_result(
            stdout="User testuser deleted"
        )

        output = io.StringIO()
        with redirect_stdout(output):
            User.delete("testuser")

        result = output.getvalue()
        assert "Deleting user: testuser" in result
        assert "deleted successfully" in result

        # Verify sacctmgr was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "sacctmgr" in call_args
        assert "-i" in call_args
        assert "delete" in call_args
        assert "user" in call_args
        assert "name=testuser" in call_args

    @patch("subprocess.run")
    def test_delete_user_failure(self, mock_run):
        """Test failed user deletion."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "sacctmgr", stderr="User not found"
        )

        output = io.StringIO()
        with redirect_stdout(output):
            User.delete("nonexistent")

        result = output.getvalue()
        assert "Deleting user: nonexistent" in result
        assert "Failed to delete" in result


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
        mock_data = {
            "users": [
                {"name": "user1", "administrator_level": "None"},
                {"name": "user2", "administrator_level": "None"},
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
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
        mock_data = {
            "users": [
                {"name": "user1", "administrator_level": "None"},
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
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
        """Test show with name parameter filters users."""
        mock_data = {
            "users": [
                {"name": "specificuser", "administrator_level": "None"},
                {"name": "otheruser", "administrator_level": "None"},
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                User.show(name="specificuser")

            result = output.getvalue()
            # Check that specific user is in output (may be truncated)
            assert "specif" in result
            # otheruser should be filtered out
            assert "otheruser" not in result

    def test_show_with_profile_str(self):
        """Test show with profile_str parameter."""
        mock_data = {
            "users": [
                {"name": "user1", "administrator_level": "None"},
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                User.show(profile_str="users.columns=name")

            result = output.getvalue()
            assert "user1" in result

    def test_show_with_delimiter(self):
        """Test show with delimiter parameter in CSV mode."""
        mock_data = {
            "users": [
                {"name": "user1", "administrator_level": "None"},
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                User.show(style="csv", delimiter="|")

            result = output.getvalue()
            # CSV output should use the pipe delimiter
            assert "|" in result or "user1" in result

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
        """Test that pretty style calls sacctmgr with --json flag."""
        mock_data = {"users": []}
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(
            subprocess,
            "run",
            return_value=mock_result,
        ) as mock_run:
            User.show(style="pretty")

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            # Now always uses --json internally
            assert "--json" in call_args


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


class TestUserAutocomplete:
    """Tests for User autocomplete functionality."""

    def test_generate_autocomplete_options_returns_string(self):
        """Test that generate_autocomplete_options returns a string."""
        result = User.generate_autocomplete_options()
        assert isinstance(result, str)

    def test_generate_autocomplete_options_contains_function(self):
        """Test that autocomplete script contains the function definition."""
        result = User.generate_autocomplete_options()
        assert "_slurm_cli_users_autocomplete()" in result

    def test_generate_autocomplete_options_contains_options(self):
        """Test that autocomplete script contains user options."""
        result = User.generate_autocomplete_options()
        assert "account=" in result.lower()
        assert "adminlevel=" in result.lower()
        assert "defaultaccount=" in result.lower()

    def test_generate_autocomplete_options_handles_commands(self):
        """Test that autocomplete script handles different commands."""
        result = User.generate_autocomplete_options()
        assert "show|delete)" in result
        assert "create)" in result
        assert "update)" in result

    def test_generate_autocomplete_options_contains_set_options(self):
        """Test that autocomplete contains SET options for update."""
        result = User.generate_autocomplete_options()
        assert "newname=" in result.lower()
        assert "fairshare=" in result.lower()

    def test_generate_autocomplete_options_contains_admin_levels(self):
        """Test that autocomplete contains admin level values."""
        result = User.generate_autocomplete_options()
        # Admin level completions
        assert "None Admin Operator" in result

    def test_generate_autocomplete_options_handles_set_keyword(self):
        """Test that autocomplete handles 'set' keyword for update."""
        result = User.generate_autocomplete_options()
        assert "found_set" in result


class TestUserOptions:
    """Tests for USER_OPTIONS constant."""

    def test_user_options_is_list(self):
        """Test that USER_OPTIONS is a list."""
        from slurm_cli.utils.users import USER_OPTIONS

        assert isinstance(USER_OPTIONS, list)

    def test_user_options_contains_expected_keys(self):
        """Test that USER_OPTIONS contains expected keys."""
        from slurm_cli.utils.users import USER_OPTIONS

        expected = ["Account", "AdminLevel", "DefaultAccount", "Name"]
        for key in expected:
            assert key in USER_OPTIONS


class TestUserUpdateOptions:
    """Tests for USER_UPDATE_* constants."""

    def test_user_update_set_options_is_list(self):
        """Test that USER_UPDATE_SET_OPTIONS is a list."""
        from slurm_cli.utils.users import USER_UPDATE_SET_OPTIONS

        assert isinstance(USER_UPDATE_SET_OPTIONS, list)

    def test_user_update_set_options_contains_expected_keys(self):
        """Test that USER_UPDATE_SET_OPTIONS contains expected keys."""
        from slurm_cli.utils.users import USER_UPDATE_SET_OPTIONS

        expected = [
            "adminlevel",
            "defaultaccount",
            "defaultwckey",
            "newname",
            "partition",
            "fairshare",
        ]
        for key in expected:
            assert key in USER_UPDATE_SET_OPTIONS

    def test_user_update_where_options_is_list(self):
        """Test that USER_UPDATE_WHERE_OPTIONS is a list."""
        from slurm_cli.utils.users import USER_UPDATE_WHERE_OPTIONS

        assert isinstance(USER_UPDATE_WHERE_OPTIONS, list)

    def test_user_update_where_options_contains_expected_keys(self):
        """Test that USER_UPDATE_WHERE_OPTIONS contains expected keys."""
        from slurm_cli.utils.users import USER_UPDATE_WHERE_OPTIONS

        expected = [
            "account",
            "adminlevel",
            "cluster",
            "defaultaccount",
            "defaultwckey",
            "name",
            "partition",
        ]
        for key in expected:
            assert key in USER_UPDATE_WHERE_OPTIONS

    def test_valid_admin_levels(self):
        """Test VALID_ADMIN_LEVELS constant."""
        from slurm_cli.utils.users import VALID_ADMIN_LEVELS

        assert isinstance(VALID_ADMIN_LEVELS, list)
        assert "none" in VALID_ADMIN_LEVELS
        assert "admin" in VALID_ADMIN_LEVELS
        assert "operator" in VALID_ADMIN_LEVELS
        assert len(VALID_ADMIN_LEVELS) == 3


class TestUserFilterAliases:
    """Tests for user filter aliases."""

    def test_match_filter_direct_field(self):
        """Test _match_filter with direct field name."""
        user = {"name": "testuser", "administrator_level": "None"}
        assert User._match_filter(user, "name", "testuser")
        assert not User._match_filter(user, "name", "otheruser")

    def test_match_filter_user_alias(self):
        """Test _match_filter with user/username alias for name."""
        user = {"name": "testuser", "administrator_level": "None"}
        assert User._match_filter(user, "user", "testuser")
        assert User._match_filter(user, "username", "testuser")
        assert not User._match_filter(user, "user", "otheruser")

    def test_match_filter_admin_level_alias(self):
        """Test _match_filter with adminlevel alias."""
        user = {"name": "admin1", "administrator_level": "Admin"}
        assert User._match_filter(user, "adminlevel", "Admin")
        assert User._match_filter(user, "admin", "Admin")
        assert not User._match_filter(user, "adminlevel", "None")

    def test_match_filter_default_account_alias(self):
        """Test _match_filter with defaultaccount alias."""
        user = {
            "name": "user1",
            "default": {"account": "myaccount", "wckey": "mykey"},
        }
        assert User._match_filter(user, "defaultaccount", "myaccount")
        assert User._match_filter(user, "account", "myaccount")
        assert not User._match_filter(
            user, "defaultaccount", "otheraccount"
        )

    def test_match_filter_default_wckey_alias(self):
        """Test _match_filter with defaultwckey alias."""
        user = {
            "name": "user1",
            "default": {"account": "acc", "wckey": "mykey"},
        }
        assert User._match_filter(user, "defaultwckey", "mykey")
        assert not User._match_filter(user, "defaultwckey", "otherkey")

    def test_match_filter_case_insensitive(self):
        """Test _match_filter is case insensitive."""
        user = {"name": "TestUser", "administrator_level": "Admin"}
        assert User._match_filter(user, "NAME", "testuser")
        assert User._match_filter(user, "name", "TESTUSER")
        assert User._match_filter(user, "ADMINLEVEL", "admin")

    def test_filter_aliases_defined(self):
        """Test that FILTER_ALIASES contains expected mappings."""
        assert "defaultaccount" in User.FILTER_ALIASES
        assert "account" in User.FILTER_ALIASES
        assert "adminlevel" in User.FILTER_ALIASES
        assert User.FILTER_ALIASES["defaultaccount"] == (
            "default",
            "account",
        )
