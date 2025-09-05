"""Tests for the Association resource class."""

import json
from unittest.mock import MagicMock, patch

import pytest

from slurm_cli.utils.associations import (
    ASSOCIATION_FILTER_OPTIONS,
    ASSOCIATION_OPTIONS,
    ASSOCIATION_QOSLEVEL_OPTIONS,
    ASSOCIATION_SET_OPTIONS,
    Association,
)


class TestAssociationInit:
    """Tests for Association initialization."""

    def test_association_init_with_account(self):
        """Test Association can be initialized with account name."""
        assoc = Association(account="nvidia")
        assert assoc.account == "nvidia"

    def test_association_init_with_kwargs(self):
        """Test Association can be initialized with additional kwargs."""
        assoc = Association(
            account="nvidia", user="testuser", cluster="test"
        )
        assert assoc.account == "nvidia"
        assert assoc.kwargs == {"user": "testuser", "cluster": "test"}


class TestAssociationShow:
    """Tests for Association.show method."""

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_show_json_style(self, mock_run):
        """Test show with JSON output style."""
        mock_result = MagicMock()
        mock_result.stdout = json.dumps(
            {
                "associations": [
                    {
                        "account": "nvidia",
                        "user": "testuser",
                        "cluster": "test-cluster",
                        "partition": "",
                        "shares_raw": 100,
                        "qos": ["normal"],
                    }
                ]
            }
        )
        mock_run.return_value = mock_result

        # Should not raise
        Association.show(style="json")
        mock_run.assert_called_once()

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_show_with_filter(self, mock_run):
        """Test show with account filter."""
        mock_result = MagicMock()
        mock_result.stdout = json.dumps(
            {
                "associations": [
                    {
                        "account": "nvidia",
                        "user": "",
                        "cluster": "test",
                        "partition": "",
                        "shares_raw": 1,
                        "qos": [],
                    },
                    {
                        "account": "root",
                        "user": "",
                        "cluster": "test",
                        "partition": "",
                        "shares_raw": 1,
                        "qos": [],
                    },
                ]
            }
        )
        mock_run.return_value = mock_result

        Association.show(field="account=nvidia", style="json")
        mock_run.assert_called_once()

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_show_empty_associations(self, mock_run):
        """Test show with no associations."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        # Should not raise, just print message
        Association.show()


class TestAssociationUpdate:
    """Tests for Association.update method."""

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_update_simple_mode(self, mock_run):
        """Test update in simple mode."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        Association.update("nvidia", False, shares="100")
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "modify" in call_args
        assert "user" in call_args
        assert "name=nvidia" in call_args

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_update_where_mode(self, mock_run):
        """Test update with WHERE/SET syntax."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        Association.update(
            "",
            False,
            where_conditions=["account=nvidia"],
            set_values=["shares=200"],
        )
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "where" in call_args
        assert "set" in call_args

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_update_failure(self, mock_run):
        """Test update handles errors gracefully."""
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(
            1, "cmd", stderr="error"
        )

        # Should not raise, just print error
        Association.update("nvidia", False, shares="100")


class TestAssociationDelete:
    """Tests for Association.delete method."""

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_delete_with_single_condition(self, mock_run):
        """Test delete with a single condition."""
        mock_run.return_value = MagicMock(stdout="", stderr="")

        Association.delete(["user=szhumatiy"])
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "delete" in call_args
        assert "association" in call_args
        assert "where" in call_args
        assert "user=szhumatiy" in call_args

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_delete_with_multiple_conditions(self, mock_run):
        """Test delete with multiple conditions."""
        mock_run.return_value = MagicMock(stdout="", stderr="")

        Association.delete(["user=szhumatiy", "partition=backfill"])
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "user=szhumatiy" in call_args
        assert "partition=backfill" in call_args

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_delete_dry_run(self, mock_run):
        """Test delete in dry run mode does not call subprocess."""
        Association.delete(["user=szhumatiy"], dry_run=True)
        mock_run.assert_not_called()


class TestAssociationFormatValue:
    """Tests for Association._format_value method."""

    def test_format_string_value(self):
        """Test formatting a string value."""
        assoc = {"account": "nvidia"}
        result = Association._format_value(assoc, "account")
        assert result == "nvidia"

    def test_format_missing_value(self):
        """Test formatting a missing value."""
        assoc = {"account": "nvidia"}
        result = Association._format_value(assoc, "user")
        assert result == "-"

    def test_format_qos_list(self):
        """Test formatting QOS list."""
        assoc = {"qos": ["normal", "high", "low"]}
        result = Association._format_value(assoc, "qos")
        assert result == "normal,high,low"

    def test_format_empty_qos_list(self):
        """Test formatting empty QOS list."""
        assoc = {"qos": []}
        result = Association._format_value(assoc, "qos")
        assert result == "-"


class TestAssociationFilters:
    """Tests for Association filter parsing and application."""

    def test_parse_filter_valid(self):
        """Test parsing a valid filter string."""
        result = Association._parse_filter("account=nvidia")
        assert result == ("account", "nvidia")

    def test_parse_filter_no_equals(self):
        """Test parsing string without = returns None."""
        result = Association._parse_filter("nvidia")
        assert result is None

    def test_apply_filters_single(self):
        """Test applying a single filter."""
        associations = [
            {"account": "nvidia", "user": "user1"},
            {"account": "root", "user": "user2"},
            {"account": "nvidia", "user": "user3"},
        ]
        result = Association._apply_filters(
            associations, [("account", "nvidia")]
        )
        assert len(result) == 2
        assert all(a["account"] == "nvidia" for a in result)


class TestAssociationOptions:
    """Tests for ASSOCIATION_*_OPTIONS constants."""

    def test_association_options_defined(self):
        """Test that ASSOCIATION_OPTIONS is defined and not empty."""
        assert ASSOCIATION_OPTIONS is not None
        assert len(ASSOCIATION_OPTIONS) > 0

    def test_association_options_contains_expected_fields(self):
        """Test ASSOCIATION_OPTIONS contains expected fields."""
        expected_fields = ["Account", "User", "Cluster", "Partition"]
        for field in expected_fields:
            assert field in ASSOCIATION_OPTIONS

    def test_filter_options_defined(self):
        """Test that ASSOCIATION_FILTER_OPTIONS is defined."""
        assert ASSOCIATION_FILTER_OPTIONS is not None
        expected = ["Account", "Cluster", "Partition", "User"]
        for field in expected:
            assert field in ASSOCIATION_FILTER_OPTIONS

    def test_set_options_defined(self):
        """Test that ASSOCIATION_SET_OPTIONS is defined."""
        assert ASSOCIATION_SET_OPTIONS is not None
        expected = [
            "DefaultQOS",
            "Fairshare",
            "MaxJobs",
            "MaxTRES",
            "Priority",
        ]
        for field in expected:
            assert field in ASSOCIATION_SET_OPTIONS

    def test_qoslevel_options_defined(self):
        """Test that ASSOCIATION_QOSLEVEL_OPTIONS is defined."""
        assert ASSOCIATION_QOSLEVEL_OPTIONS is not None
        assert "QosLevel=" in ASSOCIATION_QOSLEVEL_OPTIONS
        assert "QosLevel+=" in ASSOCIATION_QOSLEVEL_OPTIONS
        assert "QosLevel-=" in ASSOCIATION_QOSLEVEL_OPTIONS


class TestAssociationProfileFields:
    """Tests for Association.get_profile_fields method."""

    def test_get_profile_fields_returns_dict(self):
        """Test that get_profile_fields returns a dict."""
        result = Association.get_profile_fields()
        assert isinstance(result, dict)

    def test_get_profile_fields_contains_expected_keys(self):
        """Test that get_profile_fields contains expected keys."""
        result = Association.get_profile_fields()
        expected_keys = ["account", "user", "cluster", "partition"]
        for key in expected_keys:
            assert key in result


class TestAssociationAutocomplete:
    """Tests for Association.generate_autocomplete_options method."""

    def test_generate_autocomplete_returns_string(self):
        """Test that generate_autocomplete_options returns a string."""
        result = Association.generate_autocomplete_options()
        assert isinstance(result, str)

    def test_autocomplete_contains_function_definition(self):
        """Test autocomplete script contains function definition."""
        result = Association.generate_autocomplete_options()
        assert "_slurm_cli_associations_autocomplete()" in result

    def test_autocomplete_contains_filter_options(self):
        """Test autocomplete script includes filter options."""
        result = Association.generate_autocomplete_options()
        assert "account=" in result
        assert "user=" in result
        assert "cluster=" in result
        assert "partition=" in result

    def test_autocomplete_contains_set_options(self):
        """Test autocomplete script includes set options."""
        result = Association.generate_autocomplete_options()
        assert "defaultqos=" in result
        assert "fairshare=" in result
        assert "maxjobs=" in result
        assert "priority=" in result

    def test_autocomplete_contains_qoslevel_options(self):
        """Test autocomplete script includes QosLevel with =, +=, -=."""
        result = Association.generate_autocomplete_options()
        assert "qoslevel=" in result
        assert "qoslevel+=" in result
        assert "qoslevel-=" in result

    def test_autocomplete_contains_set_keyword(self):
        """Test autocomplete script includes 'set' keyword for update."""
        result = Association.generate_autocomplete_options()
        assert 'set"' in result or "set " in result


class TestAssociationConstants:
    """Tests for Association class constants."""

    def test_default_columns_defined(self):
        """Test DEFAULT_COLUMNS is defined."""
        assert Association.DEFAULT_COLUMNS is not None
        assert len(Association.DEFAULT_COLUMNS) > 0
        assert "account" in Association.DEFAULT_COLUMNS

    def test_default_styles_defined(self):
        """Test DEFAULT_STYLES is defined."""
        assert Association.DEFAULT_STYLES is not None
        assert "account" in Association.DEFAULT_STYLES


class TestAssociationFormatValueEdgeCases:
    """Tests for Association._format_value edge cases."""

    def test_format_id_dict(self):
        """Test formatting nested id field."""
        assoc = {"id": {"id": 12345}}
        result = Association._format_value(assoc, "id")
        assert result == "12345"

    def test_format_priority_set(self):
        """Test formatting priority when set is True."""
        assoc = {"priority": {"set": True, "number": 100}}
        result = Association._format_value(assoc, "priority")
        assert result == "100"

    def test_format_priority_not_set(self):
        """Test formatting priority when set is False."""
        assoc = {"priority": {"set": False, "number": 0}}
        result = Association._format_value(assoc, "priority")
        assert result == "-"

    def test_format_default_qos(self):
        """Test formatting default field with qos."""
        assoc = {"default": {"qos": "normal"}}
        result = Association._format_value(assoc, "default")
        assert result == "normal"

    def test_format_default_empty(self):
        """Test formatting default field with empty qos."""
        assoc = {"default": {"qos": ""}}
        result = Association._format_value(assoc, "default")
        assert result == "-"

    def test_format_max_with_jobs(self):
        """Test formatting max field with jobs limit."""
        assoc = {
            "max": {"jobs": {"active": {"set": True, "number": 10}}}
        }
        result = Association._format_value(assoc, "max")
        assert "jobs=10" in result

    def test_format_max_with_tres(self):
        """Test formatting max field with tres limits."""
        assoc = {
            "max": {
                "tres": {"per": {"cpu": {"set": True, "number": 100}}}
            }
        }
        result = Association._format_value(assoc, "max")
        assert "cpu=100" in result

    def test_format_min_empty(self):
        """Test formatting min field with empty structure."""
        assoc = {"min": {}}
        result = Association._format_value(assoc, "min")
        assert result == "-"

    def test_format_flags_list(self):
        """Test formatting flags as list."""
        assoc = {"flags": ["admin", "nolimit"]}
        result = Association._format_value(assoc, "flags")
        assert result == "admin,nolimit"

    def test_format_accounting_list(self):
        """Test formatting accounting as list."""
        assoc = {"accounting": ["item1", "item2"]}
        result = Association._format_value(assoc, "accounting")
        assert result == "item1,item2"


class TestAssociationSortHierarchically:
    """Tests for Association._sort_hierarchically method."""

    def test_sort_single_account(self):
        """Test sorting with single account and no users."""
        associations = [
            {"account": "root", "user": "", "parent_account": ""}
        ]
        result = Association._sort_hierarchically(associations)
        assert len(result) == 1
        assert result[0]["_depth"] == 0
        assert result[0]["_indent"] == ""

    def test_sort_account_with_users(self):
        """Test sorting account with users."""
        associations = [
            {"account": "nvidia", "user": "", "parent_account": "root"},
            {
                "account": "nvidia",
                "user": "john",
                "parent_account": "root",
            },
            {
                "account": "nvidia",
                "user": "alice",
                "parent_account": "root",
            },
        ]
        result = Association._sort_hierarchically(associations)
        # Should have account + 2 users
        assert len(result) == 3
        # Account first
        assert result[0]["user"] == ""
        assert result[0]["_depth"] == 0
        # Users sorted alphabetically
        assert result[1]["user"] == "alice"
        assert result[1]["_depth"] == 1
        assert result[2]["user"] == "john"
        assert result[2]["_depth"] == 1

    def test_sort_nested_hierarchy(self):
        """Test sorting with nested account hierarchy."""
        associations = [
            {"account": "root", "user": "", "parent_account": ""},
            {"account": "nvidia", "user": "", "parent_account": "root"},
            {
                "account": "research",
                "user": "",
                "parent_account": "nvidia",
            },
        ]
        result = Association._sort_hierarchically(associations)
        assert len(result) == 3
        assert result[0]["account"] == "root"
        assert result[0]["_depth"] == 0
        assert result[1]["account"] == "nvidia"
        assert result[1]["_depth"] == 1
        assert result[2]["account"] == "research"
        assert result[2]["_depth"] == 2

    def test_sort_custom_indent(self):
        """Test sorting with custom indentation."""
        associations = [
            {"account": "root", "user": "", "parent_account": ""},
            {"account": "nvidia", "user": "", "parent_account": "root"},
        ]
        result = Association._sort_hierarchically(
            associations, indent="    "
        )
        assert result[0]["_indent"] == ""
        assert result[1]["_indent"] == "    "


class TestAssociationShowTree:
    """Tests for Association._show_tree method."""

    @patch("slurm_cli.utils.associations.console")
    def test_show_tree_basic(self, mock_console):
        """Test _show_tree with basic hierarchy."""
        associations = [
            {
                "account": "root",
                "user": "",
                "parent_account": "",
                "partition": "",
                "qos": [],
            },
            {
                "account": "nvidia",
                "user": "",
                "parent_account": "root",
                "partition": "gpu",
                "qos": ["normal"],
            },
            {
                "account": "nvidia",
                "user": "john",
                "parent_account": "root",
                "partition": "gpu",
                "qos": ["high"],
            },
        ]
        # Should not raise
        Association._show_tree(associations)
        mock_console.print.assert_called()

    @patch("slurm_cli.utils.associations.console")
    def test_show_tree_with_qos(self, mock_console):
        """Test _show_tree shows QOS information."""
        associations = [
            {
                "account": "nvidia",
                "user": "",
                "parent_account": "",
                "partition": "",
                "qos": ["normal", "high"],
            },
        ]
        Association._show_tree(associations)
        mock_console.print.assert_called()


class TestAssociationShowStyles:
    """Tests for Association.show with different styles."""

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_show_csv_style(self, mock_run):
        """Test show with CSV output style."""
        mock_result = MagicMock()
        mock_result.stdout = json.dumps(
            {
                "associations": [
                    {
                        "account": "nvidia",
                        "user": "testuser",
                        "cluster": "test",
                        "partition": "gpu",
                        "shares_raw": 100,
                        "qos": ["normal"],
                    }
                ]
            }
        )
        mock_run.return_value = mock_result

        # Should not raise
        Association.show(style="csv")
        mock_run.assert_called_once()

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_show_pretty_style(self, mock_run):
        """Test show with pretty (table) output style."""
        mock_result = MagicMock()
        mock_result.stdout = json.dumps(
            {
                "associations": [
                    {
                        "account": "nvidia",
                        "user": "testuser",
                        "cluster": "test",
                        "partition": "",
                        "shares_raw": 100,
                        "qos": [],
                    }
                ]
            }
        )
        mock_run.return_value = mock_result

        # Should not raise
        Association.show(style="pretty")
        mock_run.assert_called_once()

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_show_tree_mode(self, mock_run):
        """Test show with tree mode."""
        mock_result = MagicMock()
        mock_result.stdout = json.dumps(
            {
                "associations": [
                    {
                        "account": "root",
                        "user": "",
                        "parent_account": "",
                        "cluster": "test",
                        "partition": "",
                        "shares_raw": 1,
                        "qos": [],
                    },
                    {
                        "account": "nvidia",
                        "user": "",
                        "parent_account": "root",
                        "cluster": "test",
                        "partition": "",
                        "shares_raw": 100,
                        "qos": [],
                    },
                ]
            }
        )
        mock_run.return_value = mock_result

        # Should not raise
        Association.show(tree=True)
        mock_run.assert_called_once()

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_show_with_account_name_filter(self, mock_run):
        """Test show filtering by account name (not key=value format)."""
        mock_result = MagicMock()
        mock_result.stdout = json.dumps(
            {
                "associations": [
                    {
                        "account": "nvidia",
                        "user": "",
                        "cluster": "test",
                        "partition": "",
                        "shares_raw": 100,
                        "qos": [],
                    },
                    {
                        "account": "root",
                        "user": "",
                        "cluster": "test",
                        "partition": "",
                        "shares_raw": 1,
                        "qos": [],
                    },
                ]
            }
        )
        mock_run.return_value = mock_result

        # Filter by account name (not account=nvidia, just nvidia)
        Association.show(field="nvidia", style="json")
        mock_run.assert_called_once()

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_show_no_match_filter(self, mock_run):
        """Test show with filter that matches nothing."""
        mock_result = MagicMock()
        mock_result.stdout = json.dumps(
            {
                "associations": [
                    {
                        "account": "nvidia",
                        "user": "",
                        "cluster": "test",
                        "partition": "",
                        "shares_raw": 100,
                        "qos": [],
                    }
                ]
            }
        )
        mock_run.return_value = mock_result

        # Filter that matches nothing
        Association.show(field="account=nonexistent")
        mock_run.assert_called_once()

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_show_no_match_account_name(self, mock_run):
        """Test show with account name that doesn't exist."""
        mock_result = MagicMock()
        mock_result.stdout = json.dumps(
            {
                "associations": [
                    {
                        "account": "nvidia",
                        "user": "",
                        "cluster": "test",
                        "partition": "",
                        "shares_raw": 100,
                        "qos": [],
                    }
                ]
            }
        )
        mock_run.return_value = mock_result

        # Account name that doesn't exist
        Association.show(field="nonexistent")
        mock_run.assert_called_once()

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_show_json_decode_error(self, mock_run):
        """Test show handles JSON decode errors."""
        mock_result = MagicMock()
        mock_result.stdout = "invalid json{"
        mock_run.return_value = mock_result

        # Should not raise, just print error
        Association.show()

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_show_subprocess_error(self, mock_run):
        """Test show handles subprocess errors."""
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(
            1, "cmd", stderr="sacctmgr error"
        )

        # Should not raise, just print error
        Association.show()


class TestAssociationCreate:
    """Tests for Association.create method."""

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_create_basic(self, mock_run):
        """Test creating a basic association."""
        mock_run.return_value = MagicMock(stdout="", stderr="")

        Association.create("testuser", verbose=True, account="nvidia")
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "create" in call_args
        assert "user" in call_args
        assert "name=testuser" in call_args
        assert "account=nvidia" in call_args

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_create_with_output(self, mock_run):
        """Test create with output from sacctmgr."""
        mock_run.return_value = MagicMock(
            stdout="Added user: testuser", stderr=""
        )

        Association.create("testuser", account="nvidia")
        mock_run.assert_called_once()

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_create_failure(self, mock_run):
        """Test create handles errors gracefully."""
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(
            1, "cmd", stderr="User already exists"
        )

        # Should not raise, just print error
        Association.create("testuser", account="nvidia")


class TestAssociationUpdateVerbose:
    """Tests for Association.update with verbose output."""

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_update_verbose_success(self, mock_run):
        """Test update with verbose flag shows success message."""
        mock_run.return_value = MagicMock(stdout="", stderr="")

        Association.update("testuser", verbose=True, shares="100")
        mock_run.assert_called_once()


class TestAssociationDeleteEdgeCases:
    """Tests for Association.delete edge cases."""

    def test_delete_empty_conditions(self):
        """Test delete with empty conditions list."""
        # Should not raise, just print error
        Association.delete([])

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_delete_with_output(self, mock_run):
        """Test delete with output from sacctmgr."""
        mock_run.return_value = MagicMock(
            stdout="Deleted 3 associations", stderr=""
        )

        Association.delete(["user=testuser"])
        mock_run.assert_called_once()

    @patch("slurm_cli.utils.associations.subprocess.run")
    def test_delete_failure(self, mock_run):
        """Test delete handles errors gracefully."""
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(
            1, "cmd", stderr="No associations found"
        )

        # Should not raise, just print error
        Association.delete(["user=nonexistent"])
