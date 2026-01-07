"""Tests for job_filter module."""

import subprocess
import sys
from unittest import mock

import pytest

# Add src to path for imports
sys.path.insert(0, "src")

from slurm_cli.utils.job_filter import (  # noqa: E402
    JOB_FILTER_PREFIXES,
    _get_all_jobs,
    is_job_filter,
    parse_job_filter,
    resolve_job_filter,
    resolve_job_filters,
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


class TestIsJobFilterNotPrefix:
    """Tests for is_job_filter with not: prefix."""

    def test_not_user_filter(self):
        """Test not:user= filter is recognized."""
        assert is_job_filter("not:user=john")
        assert is_job_filter("NOT:user=john")
        assert is_job_filter("Not:User=John")

    def test_not_partition_filter(self):
        """Test not:partition= filter is recognized."""
        assert is_job_filter("not:partition=gpu")

    def test_not_state_filter(self):
        """Test not:state= filter is recognized."""
        assert is_job_filter("not:state=running")

    def test_not_account_filter(self):
        """Test not:account= filter is recognized."""
        assert is_job_filter("not:account=research")


class TestGetAllJobs:
    """Tests for _get_all_jobs function."""

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_get_all_jobs_success(self, mock_run):
        """Test _get_all_jobs returns all job IDs."""
        mock_run.return_value = mock.Mock(
            stdout="12345\n12346\n12347\n", returncode=0
        )

        result = _get_all_jobs()

        assert result == ["12345", "12346", "12347"]

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_get_all_jobs_empty(self, mock_run):
        """Test _get_all_jobs with no jobs."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        result = _get_all_jobs()

        assert result == []

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_get_all_jobs_verbose(self, mock_run):
        """Test _get_all_jobs with verbose output."""
        mock_run.return_value = mock.Mock(
            stdout="12345\n", returncode=0
        )

        with mock.patch(
            "slurm_cli.utils.job_filter.console.print"
        ) as mock_print:
            result = _get_all_jobs(verbose=True)

            assert result == ["12345"]
            mock_print.assert_called_once()

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_get_all_jobs_error(self, mock_run):
        """Test _get_all_jobs with subprocess error."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "squeue", stderr="error"
        )

        result = _get_all_jobs()

        assert result == []

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_get_all_jobs_error_verbose(self, mock_run):
        """Test _get_all_jobs error with verbose output."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "squeue", stderr="error"
        )

        with mock.patch(
            "slurm_cli.utils.job_filter.console.print"
        ) as mock_print:
            result = _get_all_jobs(verbose=True)

            assert result == []
            mock_print.assert_called_once()


class TestResolveJobFilters:
    """Tests for resolve_job_filters function with exclusion support."""

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_exclusion_filter(self, mock_run):
        """Test resolve_job_filters with not: exclusion filter."""
        mock_run.return_value = mock.Mock(
            stdout="12345\n", returncode=0
        )

        result_jobs, other_args = resolve_job_filters(
            ["12345", "12346", "not:user=john"]
        )

        # 12345 is excluded by user=john filter
        assert "12346" in result_jobs
        assert "12345" not in result_jobs
        assert other_args == []

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_exclusion_with_verbose(self, mock_run):
        """Test resolve_job_filters exclusion with verbose output."""
        mock_run.return_value = mock.Mock(
            stdout="12345\n", returncode=0
        )

        with mock.patch(
            "slurm_cli.utils.job_filter.console.print"
        ) as mock_print:
            result_jobs, _ = resolve_job_filters(
                ["12345", "12346", "not:user=john"], verbose=True
            )

            assert mock_print.called
            assert "12346" in result_jobs

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_only_exclusions_gets_all_jobs(self, mock_run):
        """Test exclusion-only resolves all jobs first."""

        def mock_squeue(cmd, **kwargs):
            if "-u" in cmd:
                # user filter
                return mock.Mock(stdout="12345\n", returncode=0)
            else:
                # all jobs
                return mock.Mock(
                    stdout="12345\n12346\n12347\n", returncode=0
                )

        mock_run.side_effect = mock_squeue

        result_jobs, _ = resolve_job_filters(["not:user=john"])

        # All jobs minus excluded user's jobs
        assert "12346" in result_jobs
        assert "12347" in result_jobs
        assert "12345" not in result_jobs

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_positive_filter(self, mock_run):
        """Test resolve_job_filters with positive filter."""
        mock_run.return_value = mock.Mock(
            stdout="12345\n12346\n", returncode=0
        )

        result_jobs, _ = resolve_job_filters(["partition=gpu"])

        assert "12345" in result_jobs
        assert "12346" in result_jobs

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_positive_filter_verbose(self, mock_run):
        """Test resolve_job_filters positive filter with verbose."""
        mock_run.return_value = mock.Mock(
            stdout="12345\n", returncode=0
        )

        with mock.patch(
            "slurm_cli.utils.job_filter.console.print"
        ) as mock_print:
            result_jobs, _ = resolve_job_filters(
                ["partition=gpu"], verbose=True
            )

            assert mock_print.called
            assert "12345" in result_jobs

    def test_direct_job_ids(self):
        """Test resolve_job_filters with direct job IDs."""
        result_jobs, _ = resolve_job_filters(["12345", "12346"])

        assert "12345" in result_jobs
        assert "12346" in result_jobs

    def test_array_job_ids(self):
        """Test resolve_job_filters with array job IDs."""
        result_jobs, _ = resolve_job_filters(["123_4", "123_5"])

        assert "123_4" in result_jobs
        assert "123_5" in result_jobs

    def test_other_args_passed_through(self):
        """Test non-job args are returned as other_args."""
        result_jobs, other_args = resolve_job_filters(
            ["12345", "reason=test"]
        )

        assert "12345" in result_jobs
        assert "reason=test" in other_args

    def test_empty_args(self):
        """Test resolve_job_filters with empty args."""
        result_jobs, other_args = resolve_job_filters([])

        assert len(result_jobs) == 0
        assert other_args == []

    def test_empty_string_args_skipped(self):
        """Test empty string args are skipped."""
        result_jobs, _ = resolve_job_filters(["12345", "", "12346"])

        assert "12345" in result_jobs
        assert "12346" in result_jobs
        assert len(result_jobs) == 2

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_exclusion_not_filter_passed_through(self, mock_run):
        """Test not: prefix on non-filter is passed through."""
        result_jobs, other_args = resolve_job_filters(
            ["12345", "not:randomstring"]
        )

        assert "12345" in result_jobs
        assert "not:randomstring" in other_args


class TestResolveJobFilterVerbose:
    """Tests for resolve_job_filter verbose output."""

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_user_filter_verbose(self, mock_run):
        """Test resolve_job_filter user filter with verbose."""
        mock_run.return_value = mock.Mock(
            stdout="12345\n", returncode=0
        )

        with mock.patch(
            "slurm_cli.utils.job_filter.console.print"
        ) as mock_print:
            result = resolve_job_filter("user=john", verbose=True)

            assert result == ["12345"]
            mock_print.assert_called_once()

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_account_filter_verbose(self, mock_run):
        """Test resolve_job_filter account filter with verbose."""
        mock_run.return_value = mock.Mock(
            stdout="12345\n", returncode=0
        )

        with mock.patch(
            "slurm_cli.utils.job_filter.console.print"
        ) as mock_print:
            result = resolve_job_filter(
                "account=research", verbose=True
            )

            assert result == ["12345"]
            mock_print.assert_called_once()

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_partition_filter_verbose(self, mock_run):
        """Test resolve_job_filter partition filter with verbose."""
        mock_run.return_value = mock.Mock(
            stdout="12345\n", returncode=0
        )

        with mock.patch(
            "slurm_cli.utils.job_filter.console.print"
        ) as mock_print:
            result = resolve_job_filter("partition=gpu", verbose=True)

            assert result == ["12345"]
            mock_print.assert_called_once()

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_state_filter_verbose(self, mock_run):
        """Test resolve_job_filter state filter with verbose."""
        mock_run.return_value = mock.Mock(
            stdout="12345\n", returncode=0
        )

        with mock.patch(
            "slurm_cli.utils.job_filter.console.print"
        ) as mock_print:
            result = resolve_job_filter("state=running", verbose=True)

            assert result == ["12345"]
            mock_print.assert_called_once()

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_name_filter_verbose(self, mock_run):
        """Test resolve_job_filter name filter with verbose."""
        mock_run.return_value = mock.Mock(
            stdout="12345\n", returncode=0
        )

        with mock.patch(
            "slurm_cli.utils.job_filter.console.print"
        ) as mock_print:
            result = resolve_job_filter("name=myjob", verbose=True)

            assert result == ["12345"]
            mock_print.assert_called_once()

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_nodes_filter_verbose(self, mock_run):
        """Test resolve_job_filter nodes filter with verbose."""
        mock_run.return_value = mock.Mock(
            stdout="12345\n", returncode=0
        )

        with mock.patch(
            "slurm_cli.utils.job_filter.console.print"
        ) as mock_print:
            result = resolve_job_filter("nodes=node001", verbose=True)

            assert result == ["12345"]
            mock_print.assert_called_once()

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_reservation_filter_verbose(self, mock_run):
        """Test resolve_job_filter reservation filter with verbose."""
        mock_run.return_value = mock.Mock(
            stdout="12345\n", returncode=0
        )

        with mock.patch(
            "slurm_cli.utils.job_filter.console.print"
        ) as mock_print:
            result = resolve_job_filter(
                "reservation=maint", verbose=True
            )

            assert result == ["12345"]
            mock_print.assert_called_once()


class TestResolveJobFilterErrors:
    """Tests for resolve_job_filter error handling."""

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_user_filter_error_verbose(self, mock_run):
        """Test user filter error with verbose output."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "squeue", stderr="error"
        )

        with mock.patch(
            "slurm_cli.utils.job_filter.console.print"
        ) as mock_print:
            result = resolve_job_filter("user=john", verbose=True)

            assert result == []
            mock_print.assert_called_once()

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_account_filter_error_verbose(self, mock_run):
        """Test account filter error with verbose output."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "squeue", stderr="error"
        )

        with mock.patch(
            "slurm_cli.utils.job_filter.console.print"
        ) as mock_print:
            result = resolve_job_filter(
                "account=research", verbose=True
            )

            assert result == []
            mock_print.assert_called_once()

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_partition_filter_error_verbose(self, mock_run):
        """Test partition filter error with verbose output."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "squeue", stderr="error"
        )

        with mock.patch(
            "slurm_cli.utils.job_filter.console.print"
        ) as mock_print:
            result = resolve_job_filter("partition=gpu", verbose=True)

            assert result == []
            mock_print.assert_called_once()

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_state_filter_error_verbose(self, mock_run):
        """Test state filter error with verbose output."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "squeue", stderr="error"
        )

        with mock.patch(
            "slurm_cli.utils.job_filter.console.print"
        ) as mock_print:
            result = resolve_job_filter("state=running", verbose=True)

            assert result == []
            mock_print.assert_called_once()

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_name_filter_error_verbose(self, mock_run):
        """Test name filter error with verbose output."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "squeue", stderr="error"
        )

        with mock.patch(
            "slurm_cli.utils.job_filter.console.print"
        ) as mock_print:
            result = resolve_job_filter("name=myjob", verbose=True)

            assert result == []
            mock_print.assert_called_once()

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_nodes_filter_error_verbose(self, mock_run):
        """Test nodes filter error with verbose output."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "squeue", stderr="error"
        )

        with mock.patch(
            "slurm_cli.utils.job_filter.console.print"
        ) as mock_print:
            result = resolve_job_filter("nodes=node001", verbose=True)

            assert result == []
            mock_print.assert_called_once()

    @mock.patch("slurm_cli.utils.job_filter.subprocess.run")
    def test_reservation_filter_error_verbose(self, mock_run):
        """Test reservation filter error with verbose output."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "squeue", stderr="error"
        )

        with mock.patch(
            "slurm_cli.utils.job_filter.console.print"
        ) as mock_print:
            result = resolve_job_filter(
                "reservation=maint", verbose=True
            )

            assert result == []
            mock_print.assert_called_once()
