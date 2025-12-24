"""Tests for the accounts module."""

import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, "src")

from slurm_cli.utils.accounts import Account  # noqa: E402


def create_mock_subprocess_result(
    stdout: str = "", returncode: int = 0
):
    """Create a mock subprocess.CompletedProcess result."""
    mock_result = MagicMock()
    mock_result.stdout = stdout
    mock_result.returncode = returncode
    return mock_result


class TestAccountInit:
    """Tests for Account.__init__ method."""

    def test_account_init_with_name(self):
        """Test Account initialization with just name."""
        account = Account("testaccount")
        assert account.name == "testaccount"
        assert account.kwargs == {}

    def test_account_init_with_kwargs(self):
        """Test Account initialization with additional kwargs."""
        account = Account(
            "testaccount",
            description="Test Account",
            organization="TestOrg",
        )
        assert account.name == "testaccount"
        assert account.kwargs["description"] == "Test Account"
        assert account.kwargs["organization"] == "TestOrg"


class TestAccountCreate:
    """Tests for Account.create method."""

    def test_create_account_success(self):
        """Test successful account creation."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.create("newaccount")

            result = output.getvalue()
            assert "Creating account: newaccount" in result
            assert "created successfully" in result

    def test_create_account_with_stdout(self):
        """Test account creation with subprocess stdout."""
        mock_result = create_mock_subprocess_result(
            stdout="Account newaccount added to cluster"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.create("newaccount")

            result = output.getvalue()
            assert "Account newaccount added to cluster" in result

    def test_create_account_with_kwargs(self):
        """Test account creation with additional arguments."""
        mock_result = create_mock_subprocess_result()
        with patch.object(
            subprocess, "run", return_value=mock_result
        ) as mock_run:
            Account.create(
                "newaccount",
                description="Test Account",
                organization="TestOrg",
            )

            # Verify subprocess was called with correct args
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "sacctmgr" in call_args
            assert "create" in call_args
            assert "account" in call_args
            assert "name=newaccount" in call_args
            assert "description=Test Account" in call_args
            assert "organization=TestOrg" in call_args

    def test_create_account_failure(self):
        """Test account creation failure handling."""
        error = subprocess.CalledProcessError(
            1, "sacctmgr", stderr="Account already exists"
        )
        with patch.object(subprocess, "run", side_effect=error):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.create("existingaccount")

            result = output.getvalue()
            assert "Creating account: existingaccount" in result
            assert "Failed to create account" in result
            assert "Account already exists" in result

    def test_create_account_failure_without_stderr(self):
        """Test account creation failure without stderr message."""
        error = subprocess.CalledProcessError(1, "sacctmgr")
        with patch.object(subprocess, "run", side_effect=error):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.create("badaccount")

            result = output.getvalue()
            assert "Failed to create account" in result


class TestAccountUpdate:
    """Tests for Account.update method."""

    def test_update_account_simple_mode(self):
        """Test account update with simple mode (by name)."""
        mock_result = create_mock_subprocess_result()
        with patch.object(
            subprocess, "run", return_value=mock_result
        ) as mock_run:
            Account.update("testaccount", description="Updated")

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "sacctmgr" in call_args
            assert "-i" in call_args
            assert "modify" in call_args
            assert "account" in call_args
            assert "where" in call_args
            assert "name=testaccount" in call_args
            assert "set" in call_args
            assert "description=Updated" in call_args

    def test_update_account_simple_mode_multiple_values(self):
        """Test account update with multiple values."""
        mock_result = create_mock_subprocess_result()
        with patch.object(
            subprocess, "run", return_value=mock_result
        ) as mock_run:
            Account.update(
                "testaccount",
                description="Updated",
                organization="NewOrg",
            )

            call_args = mock_run.call_args[0][0]
            assert "description=Updated" in call_args
            assert "organization=NewOrg" in call_args

    def test_update_account_where_mode(self):
        """Test account update with WHERE/SET mode."""
        mock_result = create_mock_subprocess_result()
        with patch.object(
            subprocess, "run", return_value=mock_result
        ) as mock_run:
            Account.update(
                "",
                where_conditions=[
                    "cluster=test",
                    "organization=OldOrg",
                ],
                set_values=["description=Updated", "fairshare=100"],
            )

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "sacctmgr" in call_args
            assert "-i" in call_args
            assert "modify" in call_args
            assert "account" in call_args
            assert "where" in call_args
            assert "cluster=test" in call_args
            assert "organization=OldOrg" in call_args
            assert "set" in call_args
            assert "description=Updated" in call_args
            assert "fairshare=100" in call_args

    def test_update_account_failure(self):
        """Test account update failure handling."""
        error = subprocess.CalledProcessError(
            1, "sacctmgr", stderr="Permission denied"
        )
        with patch.object(subprocess, "run", side_effect=error):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.update("testaccount", description="Updated")

            result = output.getvalue()
            assert "Failed to update account" in result

    def test_update_account_verbose(self):
        """Test account update with verbose output."""
        mock_result = create_mock_subprocess_result()
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.update(
                    "testaccount", verbose=True, description="Updated"
                )

            result = output.getvalue()
            assert "updated successfully" in result


class TestAccountDelete:
    """Tests for Account.delete method."""

    def test_delete_account(self):
        """Test account delete method."""
        output = io.StringIO()
        with redirect_stdout(output):
            Account.delete("testaccount")

        result = output.getvalue()
        assert "Deleting account: testaccount" in result


class TestAccountShow:
    """Tests for Account.show method."""

    def test_show_json_style(self):
        """Test show with JSON style."""
        mock_data = {
            "accounts": [
                {
                    "name": "account1",
                    "description": "First Account",
                    "organization": "Org1",
                    "coordinators": ["user1"],
                },
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show(style="json")

            result = output.getvalue()
            assert "account1" in result

    def test_show_pretty_style(self):
        """Test show with pretty style (default)."""
        mock_data = {
            "accounts": [
                {
                    "name": "account1",
                    "description": "First Account",
                    "organization": "Org1",
                    "coordinators": [],
                },
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show(style="pretty")

            result = output.getvalue()
            assert "account1" in result

    def test_show_csv_style(self):
        """Test show with CSV style."""
        mock_data = {
            "accounts": [
                {
                    "name": "account1",
                    "description": "First Account",
                    "organization": "Org1",
                    "coordinators": ["user1", "user2"],
                },
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show(style="csv", delimiter=";")

            result = output.getvalue()
            lines = result.strip().split("\n")
            assert len(lines) >= 2  # Header + data
            assert ";" in lines[0]  # Delimiter in header

    def test_show_csv_with_custom_delimiter(self):
        """Test show CSV with custom delimiter."""
        mock_data = {
            "accounts": [
                {
                    "name": "account1",
                    "description": "Test",
                    "organization": "Org",
                    "coordinators": [],
                },
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show(style="csv", delimiter="|")

            result = output.getvalue()
            assert "|" in result

    def test_show_empty_accounts(self):
        """Test show with no accounts in output."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show()

            result = output.getvalue()
            assert "No accounts found" in result

    def test_show_with_field_filter(self):
        """Test show with field filter."""
        mock_data = {
            "accounts": [
                {"name": "account1", "description": "First"},
                {"name": "account2", "description": "Second"},
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show(field="account1")

            result = output.getvalue()
            assert "account1" in result

    def test_show_with_field_not_found(self):
        """Test show with field filter that doesn't match."""
        mock_data = {
            "accounts": [
                {"name": "account1", "description": "First"},
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show(field="nonexistent")

            result = output.getvalue()
            assert "not found" in result

    def test_show_with_zebra_striping(self):
        """Test show with zebra striping enabled."""
        mock_data = {
            "accounts": [
                {"name": f"account{i}", "description": f"Desc{i}"}
                for i in range(5)
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show(zebra=True)

            # Should not crash with zebra option
            result = output.getvalue()
            assert len(result) > 0

    def test_show_with_template(self):
        """Test show with template-based output."""
        mock_data = {
            "accounts": [
                {"name": "account1", "description": "First Account"},
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show(
                    profile_str="[cyan]{name}[/] - {description}"
                )

            result = output.getvalue()
            # Template output should contain the data
            assert "account1" in result.lower()

    def test_show_subprocess_error(self):
        """Test show with subprocess error."""
        error = subprocess.CalledProcessError(
            1, "sacctmgr", stderr="Permission denied"
        )
        with patch.object(subprocess, "run", side_effect=error):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show()

            result = output.getvalue()
            assert "Failed to show accounts" in result

    def test_show_json_decode_error(self):
        """Test show with invalid JSON response."""
        mock_result = create_mock_subprocess_result(
            stdout="invalid json {"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show()

            result = output.getvalue()
            assert "Failed to parse JSON" in result


class TestAccountGetColumnConfig:
    """Tests for Account._get_column_config method."""

    def test_default_columns(self):
        """Test that default columns are returned when profile is '*'."""
        (
            columns,
            styles,
            template,
            sort_field,
            sort_asc,
        ) = Account._get_column_config()
        assert columns == Account.DEFAULT_COLUMNS
        assert "name" in styles
        assert template is None
        assert sort_field is None
        assert sort_asc is True

    def test_custom_profile(self):
        """Test with custom profile string."""
        (
            columns,
            styles,
            template,
            sort_field,
            sort_asc,
        ) = Account._get_column_config(
            profile_str="accounts.columns=name,description"
        )
        assert "name" in columns
        assert "description" in columns

    def test_with_sort_marker(self):
        """Test with sort marker in profile string."""
        (
            columns,
            styles,
            template,
            sort_field,
            sort_asc,
        ) = Account._get_column_config(
            profile_str="accounts.columns=name+,description"
        )
        assert columns == ["name", "description"]
        assert sort_field == "name"
        assert sort_asc is True


class TestAccountFormatValue:
    """Tests for Account._format_value method."""

    def test_format_string_value(self):
        """Test formatting a string value."""
        account = {"name": "test", "description": "Test Account"}
        result = Account._format_value(account, "name")
        assert result == "test"

    def test_format_missing_value(self):
        """Test formatting a missing value."""
        account = {"name": "test"}
        result = Account._format_value(account, "description")
        assert result == "-"

    def test_format_none_value(self):
        """Test formatting a None value."""
        account = {"name": "test", "description": None}
        result = Account._format_value(account, "description")
        assert result == "-"

    def test_format_empty_string_value(self):
        """Test formatting an empty string value."""
        account = {"name": "test", "description": ""}
        result = Account._format_value(account, "description")
        assert result == "-"

    def test_format_coordinators_list(self):
        """Test formatting coordinators list."""
        account = {"coordinators": ["user1", "user2", "user3"]}
        result = Account._format_value(account, "coordinators")
        assert result == "user1, user2, user3"

    def test_format_empty_coordinators_list(self):
        """Test formatting empty coordinators list."""
        account = {"coordinators": []}
        result = Account._format_value(account, "coordinators")
        assert result == "-"

    def test_format_flags_list(self):
        """Test formatting flags list."""
        account = {"flags": ["FLAG1", "FLAG2"]}
        result = Account._format_value(account, "flags")
        assert result == "FLAG1, FLAG2"

    def test_format_empty_flags_list(self):
        """Test formatting empty flags list."""
        account = {"flags": []}
        result = Account._format_value(account, "flags")
        assert result == "-"

    def test_format_associations_list(self):
        """Test formatting associations list."""
        account = {"associations": ["assoc1", "assoc2"]}
        result = Account._format_value(account, "associations")
        assert result == "assoc1, assoc2"

    def test_format_empty_associations_list(self):
        """Test formatting empty associations list."""
        account = {"associations": []}
        result = Account._format_value(account, "associations")
        assert result == "-"


class TestAccountFilters:
    """Tests for Account filter parsing and application."""

    def test_parse_filter_valid(self):
        """Test parsing a valid filter string."""
        result = Account._parse_filter("organization=nvidia")
        assert result == ("organization", "nvidia")

    def test_parse_filter_with_equals_in_value(self):
        """Test parsing filter with = in value."""
        result = Account._parse_filter("description=a=b")
        assert result == ("description", "a=b")

    def test_parse_filter_no_equals(self):
        """Test parsing string without = returns None."""
        result = Account._parse_filter("nvidia")
        assert result is None

    def test_parse_filter_case_insensitive_key(self):
        """Test that filter key is lowercased."""
        result = Account._parse_filter("Organization=nvidia")
        assert result == ("organization", "nvidia")

    def test_apply_filters_single(self):
        """Test applying a single filter."""
        accounts = [
            {"name": "acc1", "organization": "nvidia"},
            {"name": "acc2", "organization": "amd"},
            {"name": "acc3", "organization": "nvidia"},
        ]
        result = Account._apply_filters(
            accounts, [("organization", "nvidia")]
        )
        assert len(result) == 2
        assert all(a["organization"] == "nvidia" for a in result)

    def test_apply_filters_case_insensitive_value(self):
        """Test filter value matching is case insensitive."""
        accounts = [
            {"name": "acc1", "organization": "NVIDIA"},
            {"name": "acc2", "organization": "nvidia"},
        ]
        result = Account._apply_filters(
            accounts, [("organization", "NVidia")]
        )
        assert len(result) == 2

    def test_apply_filters_no_match(self):
        """Test applying filter with no matches."""
        accounts = [
            {"name": "acc1", "organization": "nvidia"},
        ]
        result = Account._apply_filters(
            accounts, [("organization", "intel")]
        )
        assert len(result) == 0


class TestAccountInheritance:
    """Tests for Account class inheritance."""

    def test_account_inherits_from_base_resource(self):
        """Test that Account inherits from BaseSlurmResource."""
        from slurm_cli.utils.base_resource import BaseSlurmResource

        assert issubclass(Account, BaseSlurmResource)

    def test_account_has_required_methods(self):
        """Test that Account has all required methods."""
        assert hasattr(Account, "create")
        assert hasattr(Account, "update")
        assert hasattr(Account, "delete")
        assert hasattr(Account, "show")
        assert callable(Account.create)
        assert callable(Account.update)
        assert callable(Account.delete)
        assert callable(Account.show)


class TestAccountConstants:
    """Tests for Account class constants."""

    def test_default_columns_defined(self):
        """Test that DEFAULT_COLUMNS is defined."""
        assert hasattr(Account, "DEFAULT_COLUMNS")
        assert "name" in Account.DEFAULT_COLUMNS
        assert "description" in Account.DEFAULT_COLUMNS
        assert "organization" in Account.DEFAULT_COLUMNS
        assert "coordinators" in Account.DEFAULT_COLUMNS

    def test_default_styles_defined(self):
        """Test that DEFAULT_STYLES is defined."""
        assert hasattr(Account, "DEFAULT_STYLES")
        assert "name" in Account.DEFAULT_STYLES
        assert Account.DEFAULT_STYLES["name"] == "cyan"


class TestAccountOptions:
    """Tests for ACCOUNT_OPTIONS constant."""

    def test_account_options_defined(self):
        """Test that ACCOUNT_OPTIONS is defined."""
        from slurm_cli.utils.accounts import ACCOUNT_OPTIONS

        assert isinstance(ACCOUNT_OPTIONS, list)
        assert len(ACCOUNT_OPTIONS) > 0

    def test_account_options_contains_expected_fields(self):
        """Test that ACCOUNT_OPTIONS contains expected fields."""
        from slurm_cli.utils.accounts import ACCOUNT_OPTIONS

        expected = [
            "Description",
            "Organization",
            "Parent",
        ]
        for field in expected:
            assert field in ACCOUNT_OPTIONS


class TestAccountAutocomplete:
    """Tests for Account.generate_autocomplete_options method."""

    def test_generate_autocomplete_returns_string(self):
        """Test that generate_autocomplete_options returns a string."""
        result = Account.generate_autocomplete_options()
        assert isinstance(result, str)

    def test_autocomplete_contains_function_definition(self):
        """Test autocomplete script contains function definition."""
        result = Account.generate_autocomplete_options()
        assert "_slurm_cli_accounts_autocomplete()" in result

    def test_autocomplete_contains_set_keyword(self):
        """Test autocomplete script includes 'set' keyword for WHERE mode."""
        result = Account.generate_autocomplete_options()
        # 'set' appears in account_options string for WHERE/SET syntax
        assert "set)" in result or "set " in result or 'set"' in result

    def test_autocomplete_contains_account_options(self):
        """Test autocomplete script includes account options."""
        from slurm_cli.utils.accounts import ACCOUNT_OPTIONS

        result = Account.generate_autocomplete_options()
        # Check lowercase version of options are in the script
        assert "description=" in result
        assert "organization=" in result
        assert "parent=" in result

    def test_autocomplete_update_shows_cached_accounts_and_options(
        self,
    ):
        """Test autocomplete script for update shows both accounts and opts."""
        result = Account.generate_autocomplete_options()
        # Check that update command case shows both cached accounts and options
        assert "update)" in result
        # Check that it uses helper function for cached accounts
        assert "cached_accounts" in result
        assert "_slurm_cache_accounts" in result
        # Check that update includes update_options
        assert "update_options" in result

    def test_autocomplete_show_includes_filter_options(self):
        """Test autocomplete script for show includes filter options."""
        result = Account.generate_autocomplete_options()
        # Check that show/delete command case exists
        assert "show|delete)" in result
        # Check filter_options variable is defined
        assert "filter_options" in result
        # Check helper functions are used
        assert "_slurm_complete" in result


class TestAccountProfileFields:
    """Tests for Account.get_profile_fields method."""

    def test_get_profile_fields_returns_dict(self):
        """Test that get_profile_fields returns a dict."""
        result = Account.get_profile_fields()
        assert isinstance(result, dict)

    def test_get_profile_fields_contains_expected_keys(self):
        """Test that get_profile_fields contains expected keys."""
        result = Account.get_profile_fields()
        expected_keys = [
            "name",
            "description",
            "organization",
            "coordinators",
        ]
        for key in expected_keys:
            assert key in result
