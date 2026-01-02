"""Tests for the node_filter module."""

import json
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, "src")

from slurm_cli.utils.node_filter import (  # noqa: E402
    COMPOUND_STATES,
    NODE_FILTER_PREFIXES,
    _get_nodes_by_partition,
    _get_nodes_by_reservation,
    _get_nodes_by_state,
    _get_nodes_by_user,
    _match_compound_state,
    is_node_filter,
    resolve_node_filter,
    resolve_nodes_value,
)


def create_mock_subprocess_result(
    stdout: str = "", returncode: int = 0, stderr: str = ""
):
    """Create a mock subprocess.CompletedProcess result."""
    mock_result = MagicMock()
    mock_result.stdout = stdout
    mock_result.stderr = stderr
    mock_result.returncode = returncode
    return mock_result


class TestIsNodeFilter:
    """Tests for is_node_filter function."""

    def test_empty_value(self):
        """Test is_node_filter with empty string."""
        assert is_node_filter("") is False
        assert is_node_filter(None) is False

    def test_all_keyword(self):
        """Test is_node_filter with ALL keyword."""
        assert is_node_filter("ALL") is True
        assert is_node_filter("all") is True
        assert is_node_filter("All") is True

    def test_partition_filter(self):
        """Test is_node_filter with partition= prefix."""
        assert is_node_filter("partition=gpu") is True
        assert is_node_filter("partition=") is True
        assert is_node_filter("PARTITION=cpu") is True
        assert is_node_filter("Partition=batch") is True

    def test_state_filter(self):
        """Test is_node_filter with state= prefix."""
        assert is_node_filter("state=idle") is True
        assert is_node_filter("state=") is True
        assert is_node_filter("STATE=drain") is True
        assert is_node_filter("State=alloc") is True

    def test_user_filter(self):
        """Test is_node_filter with user= prefix."""
        assert is_node_filter("user=john") is True
        assert is_node_filter("user=") is True
        assert is_node_filter("USER=admin") is True
        assert is_node_filter("User=testuser") is True

    def test_reservation_filter(self):
        """Test is_node_filter with reservation= prefix."""
        assert is_node_filter("reservation=maint") is True
        assert is_node_filter("reservation=") is True
        assert is_node_filter("RESERVATION=backup") is True
        assert is_node_filter("Reservation=test") is True

    def test_not_filter_direct_node_names(self):
        """Test is_node_filter with direct node names."""
        assert is_node_filter("node01") is False
        assert is_node_filter("node[01-10]") is False
        assert is_node_filter("gpu-node-01,gpu-node-02") is False

    def test_not_filter_invalid_prefixes(self):
        """Test is_node_filter with invalid prefixes."""
        assert is_node_filter("nodes=gpu01") is False
        assert is_node_filter("name=node01") is False
        assert is_node_filter("partitions=gpu") is False


class TestResolveNodeFilterAll:
    """Tests for resolve_node_filter with ALL keyword."""

    def test_all_uppercase(self):
        """Test resolve_node_filter with ALL."""
        result = resolve_node_filter("ALL")
        assert result == "ALL"

    def test_all_lowercase(self):
        """Test resolve_node_filter with all."""
        result = resolve_node_filter("all")
        assert result == "ALL"

    def test_all_mixed_case(self):
        """Test resolve_node_filter with mixed case."""
        result = resolve_node_filter("All")
        assert result == "ALL"


class TestResolveNodeFilterEmpty:
    """Tests for resolve_node_filter with empty/None values."""

    def test_empty_string(self):
        """Test resolve_node_filter with empty string."""
        result = resolve_node_filter("")
        assert result is None

    def test_none_value(self):
        """Test resolve_node_filter with None."""
        result = resolve_node_filter(None)
        assert result is None


class TestResolveNodeFilterPassthrough:
    """Tests for resolve_node_filter passthrough behavior."""

    def test_direct_node_name(self):
        """Test resolve_node_filter passes through direct node names."""
        result = resolve_node_filter("node01")
        assert result == "node01"

    def test_node_range(self):
        """Test resolve_node_filter passes through node ranges."""
        result = resolve_node_filter("node[01-10]")
        assert result == "node[01-10]"

    def test_comma_separated_nodes(self):
        """Test resolve_node_filter passes through comma-separated nodes."""
        result = resolve_node_filter("node01,node02,node03")
        assert result == "node01,node02,node03"


class TestGetNodesByPartition:
    """Tests for _get_nodes_by_partition function."""

    def test_partition_json_success(self):
        """Test _get_nodes_by_partition with JSON response."""
        json_response = json.dumps(
            {
                "partitions": [
                    {
                        "name": "gpu",
                        "nodes": {"nodes": "gpu-node[01-04]"},
                    }
                ]
            }
        )
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = _get_nodes_by_partition("gpu")
            assert result == "gpu-node[01-04]"

    def test_partition_json_string_nodes(self):
        """Test _get_nodes_by_partition with string nodes format."""
        json_response = json.dumps(
            {
                "partitions": [
                    {"name": "cpu", "nodes": "cpu-node[01-10]"}
                ]
            }
        )
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = _get_nodes_by_partition("cpu")
            assert result == "cpu-node[01-10]"

    def test_partition_not_found(self):
        """Test _get_nodes_by_partition when partition not found."""
        json_response = json.dumps({"partitions": []})
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = _get_nodes_by_partition("nonexistent")
            assert result == ""

    def test_partition_subprocess_error(self):
        """Test _get_nodes_by_partition with subprocess error."""
        error = subprocess.CalledProcessError(
            1, "scontrol", stderr="error"
        )

        with patch.object(subprocess, "run", side_effect=error):
            result = _get_nodes_by_partition("gpu")
            assert result == ""


class TestGetNodesByState:
    """Tests for _get_nodes_by_state function."""

    def test_state_idle_nodes(self):
        """Test _get_nodes_by_state for idle nodes."""
        json_response = json.dumps(
            {
                "nodes": [
                    {"name": "node01", "state": ["IDLE"]},
                    {"name": "node02", "state": ["ALLOCATED"]},
                    {"name": "node03", "state": ["IDLE"]},
                ]
            }
        )
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = _get_nodes_by_state("idle")
            assert "node01" in result
            assert "node03" in result
            assert "node02" not in result

    def test_state_drain_nodes(self):
        """Test _get_nodes_by_state for drain nodes."""
        json_response = json.dumps(
            {
                "nodes": [
                    {"name": "node01", "state": ["IDLE", "DRAIN"]},
                    {"name": "node02", "state": ["ALLOCATED"]},
                    {"name": "node03", "state": ["DRAINED"]},
                ]
            }
        )
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = _get_nodes_by_state("drain")
            assert "node01" in result
            assert "node03" in result
            assert "node02" not in result

    def test_state_case_insensitive(self):
        """Test _get_nodes_by_state is case insensitive."""
        json_response = json.dumps(
            {
                "nodes": [
                    {"name": "node01", "state": ["IDLE"]},
                ]
            }
        )
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = _get_nodes_by_state("IDLE")
            assert "node01" in result

    def test_state_no_matching_nodes(self):
        """Test _get_nodes_by_state with no matching nodes."""
        json_response = json.dumps(
            {
                "nodes": [
                    {"name": "node01", "state": ["ALLOCATED"]},
                    {"name": "node02", "state": ["ALLOCATED"]},
                ]
            }
        )
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = _get_nodes_by_state("idle")
            assert result == ""

    def test_state_subprocess_error(self):
        """Test _get_nodes_by_state with subprocess error."""
        error = subprocess.CalledProcessError(
            1, "scontrol", stderr="error"
        )

        with patch.object(subprocess, "run", side_effect=error):
            result = _get_nodes_by_state("idle")
            assert result == ""


class TestGetNodesByUser:
    """Tests for _get_nodes_by_user function."""

    def test_user_with_jobs(self):
        """Test _get_nodes_by_user for user with running jobs."""
        json_response = json.dumps(
            {
                "jobs": [
                    {
                        "job_id": 1,
                        "user_name": "john",
                        "nodes": "node01",
                    },
                    {
                        "job_id": 2,
                        "user_name": "john",
                        "nodes": "node02",
                    },
                    {
                        "job_id": 3,
                        "user_name": "john",
                        "nodes": "node01",
                    },
                ]
            }
        )
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = _get_nodes_by_user("john")
            # Should deduplicate nodes
            assert "node01" in result
            assert "node02" in result

    def test_user_with_comma_separated_nodes(self):
        """Test _get_nodes_by_user with comma-separated nodes in job."""
        json_response = json.dumps(
            {
                "jobs": [
                    {"job_id": 1, "nodes": "node01,node02,node03"},
                ]
            }
        )
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = _get_nodes_by_user("john")
            assert "node01" in result
            assert "node02" in result
            assert "node03" in result

    def test_user_no_jobs(self):
        """Test _get_nodes_by_user for user with no jobs."""
        json_response = json.dumps({"jobs": []})
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = _get_nodes_by_user("nobody")
            assert result == ""

    def test_user_subprocess_error(self):
        """Test _get_nodes_by_user with subprocess error."""
        error = subprocess.CalledProcessError(
            1, "squeue", stderr="error"
        )

        with patch.object(subprocess, "run", side_effect=error):
            result = _get_nodes_by_user("john")
            assert result == ""


class TestGetNodesByReservation:
    """Tests for _get_nodes_by_reservation function."""

    def test_reservation_with_nodes(self):
        """Test _get_nodes_by_reservation for reservation with nodes."""
        json_response = json.dumps(
            {
                "reservations": [
                    {"name": "maint", "node_list": "node[01-04]"}
                ]
            }
        )
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = _get_nodes_by_reservation("maint")
            assert result == "node[01-04]"

    def test_reservation_not_found(self):
        """Test _get_nodes_by_reservation when reservation not found."""
        json_response = json.dumps({"reservations": []})
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = _get_nodes_by_reservation("nonexistent")
            assert result == ""

    def test_reservation_subprocess_error(self):
        """Test _get_nodes_by_reservation with subprocess error."""
        error = subprocess.CalledProcessError(
            1, "scontrol", stderr="error"
        )

        with patch.object(subprocess, "run", side_effect=error):
            result = _get_nodes_by_reservation("maint")
            assert result == ""


class TestResolveNodeFilterIntegration:
    """Integration tests for resolve_node_filter with various filters."""

    def test_resolve_partition_filter(self):
        """Test resolve_node_filter with partition= prefix."""
        json_response = json.dumps(
            {
                "partitions": [
                    {
                        "name": "gpu",
                        "nodes": {"nodes": "gpu-node[01-04]"},
                    }
                ]
            }
        )
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = resolve_node_filter("partition=gpu")
            assert result == "gpu-node[01-04]"

    def test_resolve_state_filter(self):
        """Test resolve_node_filter with state= prefix."""
        json_response = json.dumps(
            {
                "nodes": [
                    {"name": "node01", "state": ["IDLE"]},
                    {"name": "node02", "state": ["IDLE"]},
                ]
            }
        )
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = resolve_node_filter("state=idle")
            assert "node01" in result
            assert "node02" in result

    def test_resolve_user_filter(self):
        """Test resolve_node_filter with user= prefix."""
        json_response = json.dumps(
            {
                "jobs": [
                    {"job_id": 1, "nodes": "node01"},
                    {"job_id": 2, "nodes": "node02"},
                ]
            }
        )
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = resolve_node_filter("user=john")
            assert "node01" in result
            assert "node02" in result

    def test_resolve_reservation_filter(self):
        """Test resolve_node_filter with reservation= prefix."""
        json_response = json.dumps(
            {
                "reservations": [
                    {"name": "maint", "node_list": "node[01-10]"}
                ]
            }
        )
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = resolve_node_filter("reservation=maint")
            assert result == "node[01-10]"


class TestResolveNodesValue:
    """Tests for resolve_nodes_value function."""

    def test_resolve_direct_node(self):
        """Test resolve_nodes_value with direct node name."""
        result = resolve_nodes_value("node01")
        assert result == "node01"

    def test_resolve_all_keyword(self):
        """Test resolve_nodes_value with ALL keyword."""
        result = resolve_nodes_value("ALL")
        assert result == "ALL"

    def test_resolve_filter_success(self):
        """Test resolve_nodes_value with successful filter."""
        json_response = json.dumps(
            {
                "partitions": [
                    {
                        "name": "gpu",
                        "nodes": {"nodes": "gpu-node[01-04]"},
                    }
                ]
            }
        )
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = resolve_nodes_value("partition=gpu")
            assert result == "gpu-node[01-04]"

    def test_resolve_filter_no_match(self):
        """Test resolve_nodes_value with filter that matches no nodes."""
        json_response = json.dumps({"partitions": []})
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = resolve_nodes_value("partition=nonexistent")
            assert result == ""


class TestNodeFilterPrefixes:
    """Tests for NODE_FILTER_PREFIXES constant."""

    def test_prefixes_exist(self):
        """Test that NODE_FILTER_PREFIXES contains expected prefixes."""
        assert "partition=" in NODE_FILTER_PREFIXES
        assert "state=" in NODE_FILTER_PREFIXES
        assert "user=" in NODE_FILTER_PREFIXES
        assert "reservation=" in NODE_FILTER_PREFIXES

    def test_prefixes_count(self):
        """Test that NODE_FILTER_PREFIXES has expected count."""
        assert len(NODE_FILTER_PREFIXES) == 4


class TestCompoundStates:
    """Tests for compound state definitions and matching."""

    def test_compound_states_defined(self):
        """Test that compound states are defined."""
        assert "reserved" in COMPOUND_STATES
        assert "ralloc" in COMPOUND_STATES

    def test_reserved_state_definition(self):
        """Test reserved state requires idle + reserved."""
        reserved = COMPOUND_STATES["reserved"]
        assert "idle" in reserved["required"]
        assert "reserved" in reserved["flags"]

    def test_ralloc_state_definition(self):
        """Test ralloc state requires allocated/completing + reserved."""
        ralloc = COMPOUND_STATES["ralloc"]
        assert "allocated" in ralloc["required"]
        assert "completing" in ralloc["required"]
        assert "reserved" in ralloc["flags"]

    def test_match_reserved_idle_reserved(self):
        """Test matching IDLE+RESERVED nodes."""
        states = ["idle", "reserved"]
        assert _match_compound_state(
            states, COMPOUND_STATES["reserved"]
        )

    def test_match_reserved_not_just_idle(self):
        """Test that just IDLE doesn't match reserved."""
        states = ["idle"]
        assert not _match_compound_state(
            states, COMPOUND_STATES["reserved"]
        )

    def test_match_reserved_not_just_reserved(self):
        """Test that just RESERVED doesn't match reserved."""
        states = ["reserved"]
        assert not _match_compound_state(
            states, COMPOUND_STATES["reserved"]
        )

    def test_match_ralloc_allocated_reserved(self):
        """Test matching ALLOCATED+RESERVED nodes."""
        states = ["allocated", "reserved"]
        assert _match_compound_state(states, COMPOUND_STATES["ralloc"])

    def test_match_ralloc_completing_reserved(self):
        """Test matching COMPLETING+RESERVED nodes."""
        states = ["completing", "reserved"]
        assert _match_compound_state(states, COMPOUND_STATES["ralloc"])

    def test_match_ralloc_not_just_allocated(self):
        """Test that just ALLOCATED doesn't match ralloc."""
        states = ["allocated"]
        assert not _match_compound_state(
            states, COMPOUND_STATES["ralloc"]
        )

    def test_match_ralloc_not_idle_reserved(self):
        """Test that IDLE+RESERVED doesn't match ralloc."""
        states = ["idle", "reserved"]
        assert not _match_compound_state(
            states, COMPOUND_STATES["ralloc"]
        )


class TestGetNodesByStateCompound:
    """Tests for _get_nodes_by_state with compound states."""

    def test_state_reserved_nodes(self):
        """Test _get_nodes_by_state for reserved (IDLE+RESERVED) nodes."""
        json_response = json.dumps(
            {
                "nodes": [
                    {"name": "node01", "state": ["IDLE", "RESERVED"]},
                    {"name": "node02", "state": ["IDLE"]},
                    {
                        "name": "node03",
                        "state": ["ALLOCATED", "RESERVED"],
                    },
                    {"name": "node04", "state": ["RESERVED"]},
                ]
            }
        )
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = _get_nodes_by_state("reserved")
            assert "node01" in result
            assert "node02" not in result
            assert "node03" not in result
            assert "node04" not in result

    def test_state_ralloc_nodes(self):
        """Test _get_nodes_by_state for ralloc nodes."""
        json_response = json.dumps(
            {
                "nodes": [
                    {"name": "node01", "state": ["IDLE", "RESERVED"]},
                    {
                        "name": "node02",
                        "state": ["ALLOCATED", "RESERVED"],
                    },
                    {
                        "name": "node03",
                        "state": ["COMPLETING", "RESERVED"],
                    },
                    {"name": "node04", "state": ["ALLOCATED"]},
                ]
            }
        )
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = _get_nodes_by_state("ralloc")
            assert "node01" not in result
            assert "node02" in result
            assert "node03" in result
            assert "node04" not in result

    def test_state_reserved_case_insensitive(self):
        """Test reserved state matching is case insensitive."""
        json_response = json.dumps(
            {
                "nodes": [
                    {"name": "node01", "state": ["IDLE", "RESERVED"]},
                ]
            }
        )
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = _get_nodes_by_state("RESERVED")
            assert "node01" in result

    def test_state_ralloc_case_insensitive(self):
        """Test ralloc state matching is case insensitive."""
        json_response = json.dumps(
            {
                "nodes": [
                    {
                        "name": "node01",
                        "state": ["ALLOCATED", "RESERVED"],
                    },
                ]
            }
        )
        mock_result = create_mock_subprocess_result(
            stdout=json_response
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = _get_nodes_by_state("RALLOC")
            assert "node01" in result
