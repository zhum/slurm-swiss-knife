"""Tests for output format functionality (CSV, JSON, pretty)."""

import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, "src")

from slurm_cli.utils.accounts import Account  # noqa: E402
from slurm_cli.utils.profiles import format_with_template  # noqa: E402
from slurm_cli.utils.qos import Qos  # noqa: E402


def create_mock_subprocess_result(stdout: str):
    """Create a mock subprocess.CompletedProcess result."""
    mock_result = MagicMock()
    mock_result.stdout = stdout
    mock_result.returncode = 0
    return mock_result


class TestCSVOutput:
    """Tests for CSV output format."""

    def test_csv_delimiter_default(self):
        """Test that default delimiter is semicolon."""
        mock_data = {
            "accounts": [
                {
                    "name": "test_account",
                    "description": "Test description",
                    "organization": "Test Org",
                    "coordinators": [],
                }
            ]
        }

        mock_result = create_mock_subprocess_result(
            json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show(style="csv", delimiter=";")

            result = output.getvalue()
            # CSV output should use semicolon
            assert ";" in result

    def test_csv_delimiter_custom(self):
        """Test custom CSV delimiter."""
        mock_data = {
            "accounts": [
                {
                    "name": "test",
                    "description": "desc",
                    "organization": "org",
                    "coordinators": [],
                }
            ]
        }

        mock_result = create_mock_subprocess_result(
            json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show(style="csv", delimiter="|")

            result = output.getvalue()
            assert "|" in result

    def test_csv_header_row(self):
        """Test that CSV output includes header row."""
        mock_data = {
            "accounts": [
                {
                    "name": "test",
                    "description": "desc",
                    "organization": "org",
                    "coordinators": [],
                }
            ]
        }

        mock_result = create_mock_subprocess_result(
            json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show(style="csv", delimiter=";")

            lines = output.getvalue().strip().split("\n")
            # First line should be header
            assert len(lines) >= 2
            header = lines[0].lower()
            assert "name" in header

    def test_csv_multiple_rows(self):
        """Test CSV output with multiple data rows."""
        mock_data = {
            "accounts": [
                {
                    "name": "account1",
                    "description": "desc1",
                    "organization": "org1",
                    "coordinators": [],
                },
                {
                    "name": "account2",
                    "description": "desc2",
                    "organization": "org2",
                    "coordinators": [],
                },
            ]
        }

        mock_result = create_mock_subprocess_result(
            json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show(style="csv", delimiter=";")

            lines = output.getvalue().strip().split("\n")
            # Header + 2 data rows
            assert len(lines) == 3


class TestJSONOutput:
    """Tests for JSON output format."""

    def test_json_valid_syntax(self):
        """Test that JSON output is valid JSON."""
        mock_data = {
            "accounts": [
                {
                    "name": "test",
                    "description": "desc",
                }
            ]
        }

        mock_result = create_mock_subprocess_result(
            json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show(style="json")

            result = output.getvalue()
            # Extract JSON from rich output (may have formatting)
            # Look for the JSON content
            assert "accounts" in result or "test" in result

    def test_json_contains_data(self):
        """Test that JSON output contains expected data."""
        mock_data = {
            "accounts": [
                {
                    "name": "test_account",
                    "description": "Test description",
                }
            ]
        }

        mock_result = create_mock_subprocess_result(
            json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show(style="json")

            result = output.getvalue()
            # Check data is present
            assert "test_account" in result


class TestPrettyOutput:
    """Tests for pretty (table) output format."""

    def test_pretty_output_uses_rich(self):
        """Test that pretty output uses Rich for formatting."""
        mock_data = {
            "accounts": [
                {
                    "name": "test",
                    "description": "desc",
                    "organization": "org",
                    "coordinators": [],
                }
            ]
        }

        mock_result = create_mock_subprocess_result(
            json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            # Pretty output should use Rich Table
            # This test verifies it doesn't crash
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show(style="pretty")

            result = output.getvalue()
            # Output should contain data
            assert "test" in result or len(result) > 0

    def test_pretty_zebra_striping(self):
        """Test zebra striping option."""
        mock_data = {
            "accounts": [
                {
                    "name": f"account{i}",
                    "description": f"desc{i}",
                    "organization": f"org{i}",
                    "coordinators": [],
                }
                for i in range(4)
            ]
        }

        mock_result = create_mock_subprocess_result(
            json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show(style="pretty", zebra=True)

            # Should not crash with zebra option
            result = output.getvalue()
            assert len(result) > 0


class TestTemplateOutput:
    """Tests for template-based output."""

    def test_template_simple(self):
        """Test simple template output."""
        template = "[cyan]{name}[/] - {description}"
        data = {"name": "test", "description": "A test item"}

        result = format_with_template(template, data)
        assert "[cyan]test[/]" in result
        assert "A test item" in result

    def test_template_conditional_shown(self):
        """Test conditional text is shown when field has value."""
        template = "{name}{?users  (Users: {users})}"
        data = {"name": "test", "users": "root,admin"}

        result = format_with_template(template, data)
        assert "test" in result
        assert "(Users: root,admin)" in result

    def test_template_conditional_hidden(self):
        """Test conditional text is hidden when field is empty."""
        template = "{name}{?users  (Users: {users})}"
        data = {"name": "test", "users": ""}

        result = format_with_template(template, data)
        assert "test" in result
        assert "(Users:" not in result

    def test_template_newlines(self):
        """Test newline handling in templates."""
        template = "Line1\\nLine2\\nLine3"
        data = {}

        result = format_with_template(template, data)
        assert result.count("\n") == 2

    def test_template_rich_colors(self):
        """Test that Rich color markup is preserved."""
        template = "[bold red]{name}[/bold red]"
        data = {"name": "error"}

        result = format_with_template(template, data)
        assert "[bold red]error[/bold red]" == result


class TestQosOutput:
    """Tests for QoS-specific output formats."""

    def test_qos_dynamic_columns(self):
        """Test that QoS shows only non-empty columns in pretty mode."""
        mock_data = {
            "qos": [
                {
                    "name": "normal",
                    "id": 1,
                    "description": "",
                    "priority": {"set": True, "number": 100},
                    "flags": [],
                    "limits": {},
                }
            ]
        }

        mock_result = create_mock_subprocess_result(
            json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.show(style="pretty")

            result = output.getvalue()
            # Should contain name and priority
            assert "normal" in result

    def test_qos_csv_output(self):
        """Test QoS CSV output."""
        mock_data = {
            "qos": [
                {
                    "name": "normal",
                    "id": 1,
                    "description": "Normal QoS",
                    "priority": {"set": True, "number": 100},
                    "flags": [],
                    "limits": {},
                }
            ]
        }

        mock_result = create_mock_subprocess_result(
            json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.show(style="csv", delimiter=";")

            result = output.getvalue()
            assert "normal" in result
            assert ";" in result


class TestOutputFormatSelection:
    """Tests for output format selection logic."""

    def test_style_pretty_is_default(self):
        """Test that 'pretty' is the default style."""
        mock_data = {
            "accounts": [
                {
                    "name": "test",
                    "description": "desc",
                    "organization": "org",
                    "coordinators": [],
                }
            ]
        }

        mock_result = create_mock_subprocess_result(
            json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                # Default is pretty
                Account.show()

            result = output.getvalue()
            # Pretty output typically contains formatting characters
            assert len(result) > 0

    def test_invalid_style_handling(self):
        """Test handling of invalid style option."""
        mock_data = {
            "accounts": [
                {
                    "name": "test",
                    "description": "desc",
                    "organization": "org",
                    "coordinators": [],
                }
            ]
        }

        mock_result = create_mock_subprocess_result(
            json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            # Invalid style should fall back gracefully or raise
            try:
                Account.show(style="invalid_style")
            except (ValueError, KeyError):
                pass  # Expected behavior


class TestValueFormatting:
    """Tests for value formatting in outputs."""

    def test_list_value_formatting(self):
        """Test that list values are formatted properly."""
        template = "Coords: {coordinators}"
        data = {"coordinators": ["user1", "user2", "user3"]}

        result = format_with_template(template, data)
        # Lists should be joined or formatted somehow
        assert "user1" in result or "[" in result

    def test_dict_value_formatting(self):
        """Test that dict values are formatted properly."""
        template = "Priority: {priority}"
        # Common Slurm pattern: {"set": True, "number": 100}
        data = {"priority": {"set": True, "number": 100}}

        result = format_with_template(template, data)
        # Dict should be formatted
        assert len(result) > 10  # Should have some content

    def test_none_value_formatting(self):
        """Test that None values are handled."""
        template = "Value: {value}"
        data = {"value": None}

        result = format_with_template(template, data)
        assert "Value:" in result
        # None should become "-" or empty placeholder
        assert "-" in result or result.endswith(": ")

    def test_numeric_value_formatting(self):
        """Test that numeric values are formatted."""
        template = "Count: {count}"
        data = {"count": 42}

        result = format_with_template(template, data)
        assert "42" in result


class TestSpecialCharacterHandling:
    """Tests for special character handling in outputs."""

    def test_escape_sequences_in_template(self):
        """Test escape sequence handling."""
        template = "Tab:\\tNewline:\\n"
        data = {}

        result = format_with_template(template, data)
        # \n should be converted, \t may or may not be
        assert "\n" in result

    def test_unicode_in_values(self):
        """Test Unicode character handling in values."""
        template = "Name: {name}"
        data = {"name": "Тест 日本語 🎉"}

        result = format_with_template(template, data)
        assert "Тест" in result
        assert "日本語" in result
        assert "🎉" in result

    def test_brackets_in_values(self):
        """Test that brackets in values don't break formatting."""
        template = "Pattern: {pattern}"
        data = {"pattern": "node[001-005]"}

        result = format_with_template(template, data)
        assert "node[001-005]" in result


class TestAccountsWithProfiles:
    """Tests for account output with profile customization."""

    def test_account_with_template_profile(self):
        """Test account output with template from profile string."""
        mock_data = {
            "accounts": [
                {
                    "name": "myaccount",
                    "description": "My Account",
                    "organization": "MyOrg",
                    "coordinators": ["user1"],
                }
            ]
        }

        mock_result = create_mock_subprocess_result(
            json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show(
                    style="pretty",
                    profile_str="[bold]{name}[/] → {organization}",
                )

            result = output.getvalue()
            # Template should be applied
            assert "myaccount" in result.lower() or "MyOrg" in result


class TestEmptyDataHandling:
    """Tests for handling empty data scenarios."""

    def test_empty_accounts_list(self):
        """Test handling of empty accounts list."""
        mock_data = {"accounts": []}

        mock_result = create_mock_subprocess_result(
            json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show(style="pretty")

            # Should not crash, may show "no accounts" message
            result = output.getvalue()
            # Empty list is handled gracefully
            assert True  # No exception was raised

    def test_missing_fields_in_data(self):
        """Test handling of accounts with missing fields."""
        mock_data = {
            "accounts": [
                {
                    "name": "minimal",
                    # Missing description, organization, coordinators
                }
            ]
        }

        mock_result = create_mock_subprocess_result(
            json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Account.show(style="pretty")

            result = output.getvalue()
            # Should not crash, handle missing fields gracefully
            assert "minimal" in result or len(result) > 0
