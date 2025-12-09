"""Tests for the accounts module."""

import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from unittest.mock import patch, MagicMock

import pytest

# Add src to path for imports
sys.path.insert(0, "src")

from slurm_cli.utils.accounts import Account  # noqa: E402


def create_mock_subprocess_result(stdout: str = "", returncode: int = 0):
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
            assert "newaccount" in call_args
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

    def test_update_account(self):
        """Test account update method."""
        output = io.StringIO()
        with redirect_stdout(output):
            Account.update("testaccount", description="Updated")

        result = output.getvalue()
        assert "Updating account: testaccount" in result


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
        columns, styles, template = Account._get_column_config()
        assert columns == Account.DEFAULT_COLUMNS
        assert "name" in styles
        assert template is None

    def test_custom_profile(self):
        """Test with custom profile string."""
        columns, styles, template = Account._get_column_config(
            profile_str="accounts.columns=name,description"
        )
        assert "name" in columns
        assert "description" in columns


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

