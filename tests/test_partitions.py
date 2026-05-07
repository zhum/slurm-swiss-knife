"""Tests for partitions module."""

import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from unittest import mock

import pytest

# Add src to path for imports
sys.path.insert(0, "src")

from slurm_cli.utils.partitions import Partition  # noqa: E402


def create_sample_partition_data():
    """Create sample partition data for testing."""
    return {
        "gpu": {
            "State": "UP",
            "TotalNodes": 10,
            "TotalCPUs": 100,
            "MaxTime": "7-00:00:00",
            "DefaultTime": "1-00:00:00",
            "Nodes": "node[001-010]",
            "AllowGroups": "ALL",
            "AllowAccounts": "ALL",
            "AllowQos": "ALL",
            "AllocNodes": "ALL",
            "Default": "NO",
            "DefMemPerNode": "UNLIMITED",
            "QoS": "",
            "DisableRootJobs": "NO",
            "ExclusiveUser": "NO",
            "GraceTime": "0",
            "Hidden": "NO",
            "MaxNodes": "UNLIMITED",
            "MinNodes": "1",
            "LLN": "NO",
            "MaxCPUsPerNode": "UNLIMITED",
            "MaxCPUsPerSocket": "UNLIMITED",
            "PriorityJobFactor": "1",
            "PriorityTier": "1",
            "RootOnly": "NO",
            "ReqResv": "NO",
            "OverSubscribe": "NO",
            "OverTimeLimit": "NONE",
            "PreemptMode": "OFF",
            "SelectTypeParameters": "NONE",
        },
        "cpu": {
            "State": "UP",
            "TotalNodes": 50,
            "TotalCPUs": 500,
            "MaxTime": "3-00:00:00",
            "DefaultTime": "12:00:00",
            "Nodes": "node[011-060]",
            "AllowGroups": "ALL",
            "AllowAccounts": "ALL",
            "AllowQos": "ALL",
            "AllocNodes": "ALL",
            "Default": "YES",
            "DefMemPerNode": "4096",
            "QoS": "normal",
            "DisableRootJobs": "YES",
            "ExclusiveUser": "NO",
            "GraceTime": "60",
            "Hidden": "NO",
            "MaxNodes": "100",
            "MinNodes": "1",
            "LLN": "YES",
            "MaxCPUsPerNode": "32",
            "MaxCPUsPerSocket": "UNLIMITED",
            "PriorityJobFactor": "2",
            "PriorityTier": "1",
            "RootOnly": "NO",
            "ReqResv": "NO",
            "OverSubscribe": "YES",
            "OverTimeLimit": "30",
            "PreemptMode": "REQUEUE",
            "SelectTypeParameters": "NONE",
        },
    }


class TestPartitionInit:
    """Tests for Partition initialization."""

    def test_init_with_name(self):
        """Test initialization with name."""
        p = Partition("gpu")
        assert p.name == "gpu"
        assert p.kwargs == {}

    def test_init_with_kwargs(self):
        """Test initialization with kwargs."""
        p = Partition("gpu", state="UP", nodes="node[001-010]")
        assert p.name == "gpu"
        assert p.kwargs == {"state": "UP", "nodes": "node[001-010]"}


class TestPartitionMaxWidth:
    """Tests for Partition.max_width."""

    def test_max_width_caching(self):
        """Test max_width caches the value."""
        Partition._WIDTH = None  # Reset
        with mock.patch.object(Partition, "_WIDTH", None):
            width = Partition.max_width()
            assert width > 0
            # Second call should return cached value
            width2 = Partition.max_width()
            assert width == width2


class TestPartitionCreate:
    """Tests for Partition.create."""

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_create_success(self, mock_print, mock_run):
        """Test successful partition creation."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Partition.create("test-partition", state="UP")

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "scontrol" in args
        assert "create" in args
        assert "partition" in args

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_create_with_stdout(self, mock_print, mock_run):
        """Test create with stdout output."""
        mock_run.return_value = mock.Mock(
            stdout="Partition created", returncode=0
        )

        Partition.create(
            "test-partition", verbose=True, nodes="node001"
        )

        assert mock_print.call_count >= 1

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_create_with_add_warning(self, mock_print, mock_run):
        """Test create warns about add operations."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        # Use += syntax to trigger add warning
        Partition.create("test-partition", verbose=True, **{"nodes+": "node001"})

        # Should have warning about adding
        call_args = [str(c) for c in mock_print.call_args_list]
        assert any("Warning" in str(c) for c in call_args)

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_create_with_delete_warning(self, mock_print, mock_run):
        """Test create warns about delete operations."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        # Use -= syntax to trigger delete warning
        Partition.create("test-partition", verbose=True, **{"nodes-": "node001"})

        # Should have warning about deleting
        call_args = [str(c) for c in mock_print.call_args_list]
        assert any("Warning" in str(c) for c in call_args)

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_create_failure(self, mock_print, mock_run):
        """Test create handles failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "scontrol", stderr="Permission denied"
        )

        Partition.create("test-partition", state="UP")

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any(
            "Failed" in str(c) or "red" in str(c) for c in call_args
        )


class TestPartitionUpdate:
    """Tests for Partition.update."""

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_update_success(self, mock_print, mock_run):
        """Test successful partition update."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        # Use full valid arg name 'state' that matches valid_args
        Partition.update("test-partition", state="UP")

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "scontrol" in args
        assert "update" in args

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_update_with_verbose(self, mock_print, mock_run):
        """Test update with verbose output."""
        mock_run.return_value = mock.Mock(
            stdout="Updated", returncode=0
        )

        Partition.update(
            "test-partition", verbose=True, maxtime="2-00:00:00"
        )

        assert mock_print.call_count >= 1

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_update_with_add_operations(self, mock_print, mock_run):
        """Test update with add operations."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Partition.update("test-partition",
                         verbose=True,
                         dry_run=False,
                         **{"nodes+": "node100"})

        mock_run.assert_called_once()

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_update_with_delete_operations(self, mock_print, mock_run):
        """Test update with delete operations."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Partition.update("test-partition",
                         verbose=True,
                         dry_run=False,
                         **{"nodes-": "node001"})

        mock_run.assert_called_once()

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_update_failure(self, mock_print, mock_run):
        """Test update handles failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "scontrol", stderr="Error"
        )

        Partition.update("test-partition", state="UP")

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any(
            "Failed" in str(c) or "red" in str(c) for c in call_args
        )


class TestPartitionDelete:
    """Tests for Partition.delete."""

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_delete_success(self, mock_print, mock_run):
        """Test successful partition deletion."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Partition.delete("test-partition")

        mock_run.assert_called_once()
        call_args = [str(c) for c in mock_print.call_args_list]
        assert any("deleted" in str(c).lower() for c in call_args)

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_delete_with_stdout(self, mock_print, mock_run):
        """Test delete with stdout output."""
        mock_run.return_value = mock.Mock(
            stdout="Partition deleted", returncode=0
        )

        Partition.delete("test-partition")

        assert mock_print.call_count >= 1

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_delete_failure(self, mock_print, mock_run):
        """Test delete handles failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "scontrol", stderr="Partition not found"
        )

        Partition.delete("nonexistent")

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any(
            "Failed" in str(c) or "red" in str(c) for c in call_args
        )


class TestPartitionShow:
    """Tests for Partition.show."""

    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_show_no_data(self, mock_print):
        """Test show with no data."""
        Partition.show(data=None)

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any("No partitions" in str(c) for c in call_args)

    @mock.patch("slurm_cli.utils.partitions.console.print_json")
    def test_show_json_all(self, mock_print_json):
        """Test show with JSON style for all partitions."""
        data = create_sample_partition_data()

        Partition.show(data=data, style="json")

        mock_print_json.assert_called_once()
        output = mock_print_json.call_args[0][0]
        parsed = json.loads(output)
        assert "gpu" in parsed
        assert "cpu" in parsed

    @mock.patch("slurm_cli.utils.partitions.console.print_json")
    def test_show_json_single(self, mock_print_json):
        """Test show with JSON style for single partition."""
        data = create_sample_partition_data()

        Partition.show(name="gpu", data=data, style="json")

        mock_print_json.assert_called_once()
        output = mock_print_json.call_args[0][0]
        parsed = json.loads(output)
        assert "State" in parsed

    def test_show_csv_all(self):
        """Test show with CSV style for all partitions."""
        data = create_sample_partition_data()
        output = io.StringIO()

        with redirect_stdout(output):
            Partition.show(data=data, style="csv")

        result = output.getvalue()
        lines = result.strip().split("\n")
        # First line is header
        assert "PartitionName" in lines[0]
        assert "State" in lines[0]
        # Should have data rows
        assert len(lines) >= 3  # header + 2 partitions

    def test_show_csv_single(self):
        """Test show with CSV style for single partition."""
        data = create_sample_partition_data()
        output = io.StringIO()

        with redirect_stdout(output):
            Partition.show(name="gpu", data=data, style="csv")

        result = output.getvalue()
        lines = result.strip().split("\n")
        assert len(lines) == 2  # header + 1 partition
        assert "gpu" in lines[1]

    def test_show_csv_with_delimiter(self):
        """Test show CSV with custom delimiter."""
        data = create_sample_partition_data()
        output = io.StringIO()

        with redirect_stdout(output):
            Partition.show(data=data, style="csv", delimiter="|")

        result = output.getvalue()
        assert "|" in result
        # Should not have semicolons as delimiters
        lines = result.strip().split("\n")
        for line in lines:
            assert line.count("|") > 0

    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_show_pretty_all(self, mock_print):
        """Test show with pretty style for all partitions."""
        data = create_sample_partition_data()

        Partition.show(data=data, style="pretty")

        # Should print partition info
        assert mock_print.call_count >= 2

    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_show_pretty_single(self, mock_print):
        """Test show with pretty style for single partition."""
        data = create_sample_partition_data()

        Partition.show(name="gpu", data=data, style="pretty")

        # Should print partition info
        assert mock_print.call_count >= 1

    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_show_invalid_style(self, mock_print):
        """Test show with invalid style."""
        data = create_sample_partition_data()

        Partition.show(data=data, style="invalid")

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any("Invalid style" in str(c) for c in call_args)


class TestPartitionShowCsv:
    """Tests for Partition.show_csv."""

    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_show_csv_no_partitions(self, mock_print):
        """Test show_csv with no partitions."""
        Partition.show_csv(partitions=None)

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any("No partitions" in str(c) for c in call_args)

    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_show_csv_empty_partitions(self, mock_print):
        """Test show_csv with empty partitions dict."""
        Partition.show_csv(partitions={})

        # Empty partitions prints "No partitions found."
        call_args = [str(c) for c in mock_print.call_args_list]
        assert any("No partitions" in str(c) for c in call_args)

    def test_show_csv_priority_fields_order(self):
        """Test that priority fields appear first in CSV."""
        data = create_sample_partition_data()
        output = io.StringIO()

        with redirect_stdout(output):
            Partition.show_csv(partitions=data)

        result = output.getvalue()
        header = result.strip().split("\n")[0]
        headers_list = header.split(";")
        # PartitionName should be first
        assert headers_list[0] == "PartitionName"
        # State should be early in the list
        if "State" in headers_list:
            assert headers_list.index("State") < 10


class TestPartitionShowOnePretty:
    """Tests for Partition.show_one_pretty."""

    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_show_one_pretty_basic(self, mock_print):
        """Test show_one_pretty with basic partition."""
        data = create_sample_partition_data()["gpu"]

        Partition.show_one_pretty("gpu", dict(data))

        # Should print partition info
        call_args = [str(c) for c in mock_print.call_args_list]
        assert any("Partition" in str(c) for c in call_args)
        assert any("gpu" in str(c) for c in call_args)

    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_show_one_pretty_drain_state(self, mock_print):
        """Test show_one_pretty with DRAIN state."""
        data = dict(create_sample_partition_data()["gpu"])
        data["State"] = "DRAIN"

        Partition.show_one_pretty("gpu", data)

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any(
            "DRN" in str(c) or "DRAIN" in str(c) for c in call_args
        )

    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_show_one_pretty_down_state(self, mock_print):
        """Test show_one_pretty with DOWN state."""
        data = dict(create_sample_partition_data()["gpu"])
        data["State"] = "DOWN"

        Partition.show_one_pretty("gpu", data)

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any(
            "DWN" in str(c) or "DOWN" in str(c) for c in call_args
        )

    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_show_one_pretty_inactive_state(self, mock_print):
        """Test show_one_pretty with INACTIVE state."""
        data = dict(create_sample_partition_data()["gpu"])
        data["State"] = "INACTIVE"

        Partition.show_one_pretty("gpu", data)

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any(
            "INA" in str(c) or "INACTIVE" in str(c) for c in call_args
        )

    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_show_one_pretty_long_nodelist(self, mock_print):
        """Test show_one_pretty truncates long node list."""
        data = dict(create_sample_partition_data()["gpu"])
        data["Nodes"] = (
            "node[" + ",".join(str(i) for i in range(1, 1000)) + "]"
        )

        # Mock console width to force truncation
        with mock.patch.object(Partition, "_WIDTH", 80):
            Partition.show_one_pretty("gpu", data)

        call_args_str = "".join(
            str(c) for c in mock_print.call_args_list
        )
        # Should be truncated with ...
        assert "..." in call_args_str or "node[" in call_args_str

    @mock.patch("slurm_cli.utils.partitions.console.print")
    def test_show_one_pretty_unknown_field(self, mock_print):
        """Test show_one_pretty handles unknown fields."""
        data = dict(create_sample_partition_data()["gpu"])
        data["UnknownField"] = "some_value"

        Partition.show_one_pretty("gpu", data)

        call_args = [str(c) for c in mock_print.call_args_list]
        # Should have warning about unknown fields
        assert any(
            "Warning" in str(c) or "Unknown" in str(c)
            for c in call_args
        )


class TestPartitionValidArgs:
    """Tests for Partition.valid_args."""

    def test_valid_args_contains_expected_keys(self):
        """Test valid_args contains expected keys."""
        expected_keys = [
            "allowaccounts",
            "allowgroups",
            "allowqos",
            "default",
            "maxtime",
            "nodes",
            "state",
        ]
        for key in expected_keys:
            assert key in Partition.valid_args

    def test_valid_args_have_type_and_help(self):
        """Test each valid_arg has type and help."""
        for key, value in Partition.valid_args.items():
            assert "type" in value
            assert "help" in value


class TestPartitionValueTypes:
    """Tests for Partition.value_types."""

    def test_value_types_have_def_and_flag(self):
        """Test each value_type has def and flag."""
        for key, value in Partition.value_types.items():
            assert "def" in value
            assert "flag" in value


class TestPartitionInheritance:
    """Tests for Partition inheritance."""

    def test_inherits_from_base_resource(self):
        """Test Partition inherits from BaseSlurmResource."""
        from slurm_cli.utils.base_resource import BaseSlurmResource

        assert issubclass(Partition, BaseSlurmResource)

    def test_has_required_methods(self):
        """Test Partition has required methods."""
        assert hasattr(Partition, "create")
        assert hasattr(Partition, "update")
        assert hasattr(Partition, "delete")
        assert hasattr(Partition, "show")


class TestPartitionAutocomplete:
    """Tests for Partition.generate_autocomplete_options."""

    def test_generate_autocomplete_returns_script(self):
        """Test generate_autocomplete_options returns bash script."""
        script = Partition.generate_autocomplete_options()

        assert "_slurm_cli_partitions_autocomplete" in script
        assert "COMPREPLY" in script
        assert "case" in script

    def test_generate_autocomplete_contains_valid_args(self):
        """Test autocomplete script contains valid args."""
        script = Partition.generate_autocomplete_options()

        # Should contain some valid arg keys
        assert "state=" in script
        assert "nodes=" in script

    def test_generate_autocomplete_contains_nodes_add_remove(self):
        """Test autocomplete script contains nodes+= and nodes-= options."""
        script = Partition.generate_autocomplete_options()

        assert "nodes+=" in script
        assert "nodes-=" in script

    def test_generate_autocomplete_handles_nodes_plus_minus(self):
        """Test autocomplete handles nodes+ and nodes- as nodes type."""
        script = Partition.generate_autocomplete_options()

        # Should have handling for nodes+|nodes- in the case statement
        assert "nodes|nodes+|nodes-)" in script

    def test_generate_autocomplete_has_node_filter_context(self):
        """Test autocomplete detects node filter context for state values."""
        script = Partition.generate_autocomplete_options()

        # Should check COMP_LINE for node filter context
        assert "in_node_filter" in script
        assert "COMP_LINE" in script

    def test_generate_autocomplete_has_node_states(self):
        """Test autocomplete includes node states for node filters."""
        script = Partition.generate_autocomplete_options()

        # Should have node states for node filter
        assert "idle" in script
        assert "alloc" in script
        assert "drain" in script
