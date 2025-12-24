"""Tests for job_filter module."""

import subprocess
import sys
from unittest import mock

import pytest

# Add src to path for imports
sys.path.insert(0, "src")

from slurm_cli.utils.job_filter import (  # noqa: E402
    JOB_FILTER_PREFIXES,
    is_job_filter,
    parse_job_filter,
    resolve_job_filter,
    resolve_job_ids,
)


class TestIsJobFilter:
    """Tests for is_job_filter function."""

    def test_user_filter(self):
        """Test user= filter is recognized."""
        assert is_job_filter("user=john")
        assert is_job_filter("USER=john")
        assert is_job_filter("User=John")

    def test_account_filter(self):
        """Test account= filter is recognized."""
        assert is_job_filter("account=research")
        assert is_job_filter("ACCOUNT=research")

    def test_partition_filter(self):
        """Test partition= filter is recognized."""
        assert is_job_filter("partition=gpu")
        assert is_job_filter("PARTITION=gpu")

    def test_state_filter(self):
        """Test state= filter is recognized."""
        assert is_job_filter("state=running")
        assert is_job_filter("STATE=pending")

    def test_name_filter(self):
        """Test name= filter is recognized."""
        assert is_job_filter("name=myjob")
        assert is_job_filter("NAME=test")

    def test_nodes_filter(self):
        """Test nodes= filter is recognized."""
        assert is_job_filter("nodes=node001")
        assert is_job_filter("NODES=node[001-010]")

    def test_reservation_filter(self):
        """Test reservation= filter is recognized."""
        assert is_job_filter("reservation=maint")
        assert is_job_filter("RESERVATION=test")

    def test_not_filter_job_id(self):
        """Test job IDs are not recognized as filters."""
        assert not is_job_filter("12345")
        assert not is_job_filter("123_4")

    def test_not_filter_empty(self):
        """Test empty string is not a filter."""
        assert not is_job_filter("")
        assert not is_job_filter(None)

    def test_not_filter_random(self):
        """Test random strings are not filters."""
        assert not is_job_filter("randomstring")
        assert not is_job_filter("myjob")


class TestParseJobFilter:
    """Tests for parse_job_filter function."""

    def test_parse_user_filter(self):
        """Test parsing user filter."""
        result = parse_job_filter("user=john")
        assert result == {"user": "john"}

    def test_parse_state_filter(self):
        """Test parsing state filter."""
        result = parse_job_filter("STATE=RUNNING")
        assert result == {"state": "RUNNING"}

    def test_parse_empty(self):
        """Test parsing empty string."""
        assert parse_job_filter("") == {}
        assert parse_job_filter(None) == {}

    def test_parse_no_equals(self):
        """Test parsing string without equals."""
        assert parse_job_filter("randomstring") == {}


class TestResolveJobFilter:
    """Tests for resolve_job_filter function."""

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_resolve_user_filter(self, mock_run):
        """Test resolving user filter."""
        mock_run.return_value = mock.Mock(
            stdout="12345\n12346\n", returncode=0
        )

        result = resolve_job_filter("user=john")

        assert result == ["12345", "12346"]
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "-u" in call_args
        assert "john" in call_args

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_resolve_account_filter(self, mock_run):
        """Test resolving account filter."""
        mock_run.return_value = mock.Mock(
            stdout="12345\n", returncode=0
        )

        result = resolve_job_filter("account=research")

        assert result == ["12345"]
        call_args = mock_run.call_args[0][0]
        assert "-A" in call_args
        assert "research" in call_args

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_resolve_partition_filter(self, mock_run):
        """Test resolving partition filter."""
        mock_run.return_value = mock.Mock(
            stdout="12345\n12346\n12347\n", returncode=0
        )

        result = resolve_job_filter("partition=gpu")

        assert len(result) == 3
        call_args = mock_run.call_args[0][0]
        assert "-p" in call_args
        assert "gpu" in call_args

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_resolve_state_filter(self, mock_run):
        """Test resolving state filter."""
        mock_run.return_value = mock.Mock(
            stdout="12345\n", returncode=0
        )

        result = resolve_job_filter("state=running")

        assert result == ["12345"]
        call_args = mock_run.call_args[0][0]
        assert "-t" in call_args
        assert "running" in call_args

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_resolve_name_filter(self, mock_run):
        """Test resolving name filter."""
        mock_run.return_value = mock.Mock(
            stdout="12345\n", returncode=0
        )

        result = resolve_job_filter("name=myjob")

        assert result == ["12345"]
        call_args = mock_run.call_args[0][0]
        assert "-n" in call_args
        assert "myjob" in call_args

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_resolve_nodes_filter(self, mock_run):
        """Test resolving nodes filter."""
        mock_run.return_value = mock.Mock(
            stdout="12345\n", returncode=0
        )

        result = resolve_job_filter("nodes=node001")

        assert result == ["12345"]
        call_args = mock_run.call_args[0][0]
        assert "-w" in call_args
        assert "node001" in call_args

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_resolve_reservation_filter(self, mock_run):
        """Test resolving reservation filter."""
        mock_run.return_value = mock.Mock(
            stdout="12345\n", returncode=0
        )

        result = resolve_job_filter("reservation=maint")

        assert result == ["12345"]
        call_args = mock_run.call_args[0][0]
        assert "-R" in call_args
        assert "maint" in call_args

    def test_resolve_job_id_passthrough(self):
        """Test that job IDs pass through unchanged."""
        result = resolve_job_filter("12345")
        assert result == ["12345"]

    def test_resolve_non_numeric_not_filter(self):
        """Test that non-numeric non-filters return empty."""
        result = resolve_job_filter("randomstring")
        assert result == []

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_resolve_command_error(self, mock_run):
        """Test handling command errors."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "squeue", stderr="error"
        )

        result = resolve_job_filter("user=john")

        assert result == []


class TestResolveJobIds:
    """Tests for resolve_job_ids function."""

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_resolve_mixed_args(self, mock_run):
        """Test resolving mix of job IDs and filters."""
        mock_run.return_value = mock.Mock(
            stdout="99999\n", returncode=0
        )

        job_ids, user_filters = resolve_job_ids(
            ["12345", "user=john", "state=pending"]
        )

        # 12345 is explicit, john is user filter, state resolves to 99999
        assert "12345" in job_ids
        assert "99999" in job_ids
        assert user_filters == ["john"]

    def test_resolve_only_job_ids(self):
        """Test resolving only explicit job IDs."""
        job_ids, user_filters = resolve_job_ids(["12345", "12346"])

        assert job_ids == ["12345", "12346"]
        assert user_filters == []

    def test_resolve_user_filter_separate(self):
        """Test user filters are returned separately."""
        job_ids, user_filters = resolve_job_ids(
            ["user=john", "user=jane"]
        )

        assert job_ids == []
        assert "john" in user_filters
        assert "jane" in user_filters

    def test_resolve_empty_args(self):
        """Test resolving empty arguments."""
        job_ids, user_filters = resolve_job_ids([])

        assert job_ids == []
        assert user_filters == []

    def test_resolve_deduplicates(self):
        """Test duplicate job IDs are removed."""
        job_ids, user_filters = resolve_job_ids(
            ["12345", "12345", "12346"]
        )

        assert job_ids == ["12345", "12346"]

    def test_resolve_array_job_ids(self):
        """Test array job IDs are handled."""
        job_ids, user_filters = resolve_job_ids(["123_4", "123_5"])

        assert "123_4" in job_ids
        assert "123_5" in job_ids


class TestJobFilterPrefixes:
    """Tests for JOB_FILTER_PREFIXES constant."""

    def test_all_prefixes_defined(self):
        """Test all expected prefixes are defined."""
        expected = [
            "user=",
            "account=",
            "partition=",
            "state=",
            "name=",
            "nodes=",
            "reservation=",
        ]
        for prefix in expected:
            assert prefix in JOB_FILTER_PREFIXES
