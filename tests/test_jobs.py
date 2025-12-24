"""Tests for jobs module."""

import json
import subprocess
import sys
from unittest import mock

import pytest

# Add src to path for imports
sys.path.insert(0, "src")

from slurm_cli.utils.jobs import Job  # noqa: E402


def create_sample_job_data():
    """Create sample job data for testing."""
    return {
        "jobs": [
            {
                "job_id": 12345,
                "name": "test_job",
                "user_name": "testuser",
                "account": "test_account",
                "partition": "gpu",
                "job_state": ["RUNNING"],
                "time_limit": {
                    "set": True,
                    "infinite": False,
                    "number": 1440,
                },
                "node_count": {
                    "set": True,
                    "infinite": False,
                    "number": 1,
                },
                "nodes": "node001",
                "cpus": {"set": True, "infinite": False, "number": 8},
                "submit_time": {
                    "set": True,
                    "infinite": False,
                    "number": 1700000000,
                },
                "start_time": {
                    "set": True,
                    "infinite": False,
                    "number": 1700000100,
                },
                "end_time": {
                    "set": True,
                    "infinite": False,
                    "number": 0,
                },
                "priority": {
                    "set": True,
                    "infinite": False,
                    "number": 100,
                },
                "state_reason": "None",
                "command": "/path/to/script.sh",
                "current_working_directory": "/home/testuser",
                "standard_output": "/home/testuser/job.out",
                "standard_error": "/home/testuser/job.err",
            },
            {
                "job_id": 12346,
                "name": "pending_job",
                "user_name": "otheruser",
                "account": "other_account",
                "partition": "cpu",
                "job_state": ["PENDING"],
                "time_limit": {
                    "set": True,
                    "infinite": True,
                    "number": 0,
                },
                "node_count": {
                    "set": True,
                    "infinite": False,
                    "number": 2,
                },
                "nodes": "",
                "cpus": {"set": True, "infinite": False, "number": 16},
                "submit_time": {
                    "set": True,
                    "infinite": False,
                    "number": 1700000200,
                },
                "start_time": {
                    "set": True,
                    "infinite": False,
                    "number": 0,
                },
                "end_time": {
                    "set": True,
                    "infinite": False,
                    "number": 0,
                },
                "priority": {
                    "set": True,
                    "infinite": False,
                    "number": 50,
                },
                "state_reason": "Resources",
                "command": "/path/to/other_script.sh",
                "current_working_directory": "/home/otheruser",
                "standard_output": "/home/otheruser/job.out",
                "standard_error": "/home/otheruser/job.err",
            },
        ]
    }


class TestJobNormalizeJob:
    """Tests for Job._normalize_job."""

    def test_normalize_running_job(self):
        """Test normalizing a running job."""
        job_data = create_sample_job_data()["jobs"][0]
        normalized = Job._normalize_job(job_data)

        assert normalized["job_id"] == "12345"
        assert normalized["name"] == "test_job"
        assert normalized["user_name"] == "testuser"
        assert normalized["partition"] == "gpu"
        assert normalized["job_state"] == "RUNNING"
        assert normalized["nodes"] == "node001"

    def test_normalize_pending_job(self):
        """Test normalizing a pending job."""
        job_data = create_sample_job_data()["jobs"][1]
        normalized = Job._normalize_job(job_data)

        assert normalized["job_id"] == "12346"
        assert normalized["name"] == "pending_job"
        assert normalized["job_state"] == "PENDING"
        assert normalized["time_limit"] == "UNLIMITED"

    def test_normalize_job_state_list(self):
        """Test normalizing job with state as list."""
        job_data = {"job_id": 1, "job_state": ["RUNNING", "COMPLETING"]}
        normalized = Job._normalize_job(job_data)
        assert normalized["job_state"] == "RUNNING,COMPLETING"

    def test_normalize_endlimit_uses_end_time(self):
        """Test endlimit uses end_time when set and valid."""
        job_data = {
            "job_id": 1,
            "time_limit": {
                "set": True,
                "infinite": False,
                "number": 60,
            },
            "end_time": {
                "set": True,
                "infinite": False,
                "number": 1700001000,
            },
        }
        normalized = Job._normalize_job(job_data)
        # end_time formatted as YYYY-MM-DDTHH:MM:SS
        assert normalized["endlimit"] == "2023-11-14T14:30:00"
        assert normalized["end_time"] == "2023-11-14T14:30:00"

    def test_normalize_endlimit_uses_time_limit_when_end_time_not_set(
        self,
    ):
        """Test endlimit falls back to time_limit when end_time not set."""
        job_data = {
            "job_id": 1,
            "time_limit": {
                "set": True,
                "infinite": False,
                "number": 60,
            },
            "end_time": {"set": False, "infinite": False, "number": 0},
        }
        normalized = Job._normalize_job(job_data)
        assert normalized["endlimit"] == "1:00:00"
        assert normalized["end_time"] == "-"

    def test_normalize_endlimit_uses_time_limit_when_end_time_zero(
        self,
    ):
        """Test endlimit falls back to time_limit when end_time is zero."""
        job_data = {
            "job_id": 1,
            "time_limit": {
                "set": True,
                "infinite": False,
                "number": 1440,
            },
            "end_time": {"set": True, "infinite": False, "number": 0},
        }
        normalized = Job._normalize_job(job_data)
        # time_limit 1440 mins = 24 hours = 1 day
        assert normalized["endlimit"] == "1-00:00:00"
        assert normalized["end_time"] == "-"


class TestJobApplyFilters:
    """Tests for Job._apply_filters."""

    def test_filter_by_user(self):
        """Test filtering jobs by user."""
        jobs = [
            {
                "job_id": "1",
                "user_name": "testuser",
                "job_state": "RUNNING",
            },
            {
                "job_id": "2",
                "user_name": "otheruser",
                "job_state": "PENDING",
            },
        ]
        result = Job._apply_filters(jobs, {"user": "testuser"})
        assert len(result) == 1
        assert result[0]["job_id"] == "1"

    def test_filter_by_state(self):
        """Test filtering jobs by state."""
        jobs = [
            {
                "job_id": "1",
                "user_name": "testuser",
                "job_state": "RUNNING",
            },
            {
                "job_id": "2",
                "user_name": "otheruser",
                "job_state": "PENDING",
            },
        ]
        result = Job._apply_filters(jobs, {"state": "running"})
        assert len(result) == 1
        assert result[0]["job_id"] == "1"

    def test_filter_by_partition(self):
        """Test filtering jobs by partition."""
        jobs = [
            {"job_id": "1", "partition": "gpu", "job_state": "RUNNING"},
            {"job_id": "2", "partition": "cpu", "job_state": "PENDING"},
        ]
        result = Job._apply_filters(jobs, {"partition": "gpu"})
        assert len(result) == 1
        assert result[0]["job_id"] == "1"

    def test_filter_by_job_id(self):
        """Test filtering jobs by job ID."""
        jobs = [
            {"job_id": "12345", "user_name": "testuser"},
            {"job_id": "12346", "user_name": "otheruser"},
        ]
        result = Job._apply_filters(jobs, {"job_id": "12345"})
        assert len(result) == 1
        assert result[0]["job_id"] == "12345"


class TestJobShow:
    """Tests for Job.show."""

    @mock.patch("slurm_cli.utils.jobs.subprocess.run")
    def test_show_all_jobs(self, mock_run, capsys):
        """Test showing all jobs."""
        mock_run.return_value = mock.Mock(
            stdout=json.dumps(create_sample_job_data()),
            returncode=0,
        )

        Job.show(style="csv")

        captured = capsys.readouterr()
        assert "12345" in captured.out
        assert "12346" in captured.out
        assert "testuser" in captured.out

    @mock.patch("slurm_cli.utils.jobs.subprocess.run")
    def test_show_filtered_jobs(self, mock_run, capsys):
        """Test showing filtered jobs."""
        mock_run.return_value = mock.Mock(
            stdout=json.dumps(create_sample_job_data()),
            returncode=0,
        )

        Job.show(field="user=testuser", style="csv")

        captured = capsys.readouterr()
        assert "12345" in captured.out
        assert "12346" not in captured.out


class TestJobCreate:
    """Tests for Job.create."""

    def test_create_not_supported(self, capsys):
        """Test that create shows appropriate message."""
        Job.create()
        captured = capsys.readouterr()
        assert "sbatch" in captured.out or "srun" in captured.out


class TestJobUpdate:
    """Tests for Job.update."""

    @mock.patch("slurm_cli.utils.jobs.subprocess.run")
    def test_update_job(self, mock_run, capsys):
        """Test updating a job."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Job.update("12345", verbose=True, timelimit="2-00:00:00")

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "scontrol" in call_args
        assert "update" in call_args
        assert "jobid=12345" in call_args

    def test_update_no_job_id(self, capsys):
        """Test update without job ID."""
        Job.update("")
        captured = capsys.readouterr()
        assert "Job ID is required" in captured.out


class TestJobDelete:
    """Tests for Job.delete."""

    @mock.patch("slurm_cli.utils.jobs.subprocess.run")
    def test_delete_job(self, mock_run, capsys):
        """Test cancelling a job."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Job.delete("12345", verbose=True)

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "scancel" in call_args
        assert "12345" in call_args

    def test_delete_no_job_id(self, capsys):
        """Test delete without job ID or filter."""
        Job.delete("")
        captured = capsys.readouterr()
        assert "Job ID or filter is required" in captured.out


class TestJobCancelMethods:
    """Tests for Job._cancel_jobs and _cancel_by_user."""

    @mock.patch("slurm_cli.utils.jobs.subprocess.run")
    def test_cancel_jobs_single(self, mock_run):
        """Test cancelling a single job."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Job._cancel_jobs(["12345"])

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "scancel" in call_args
        assert "12345" in call_args

    @mock.patch("slurm_cli.utils.jobs.subprocess.run")
    def test_cancel_jobs_multiple(self, mock_run):
        """Test cancelling multiple jobs."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Job._cancel_jobs(["12345", "12346", "12347"])

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "scancel" in call_args
        assert "12345" in call_args
        assert "12346" in call_args
        assert "12347" in call_args

    @mock.patch("slurm_cli.utils.jobs.subprocess.run")
    def test_cancel_jobs_verbose(self, mock_run, capsys):
        """Test cancelling jobs with verbose output."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Job._cancel_jobs(["12345"], verbose=True)

        captured = capsys.readouterr()
        assert "1 job(s) cancelled" in captured.out

    @mock.patch("slurm_cli.utils.jobs.subprocess.run")
    def test_cancel_by_user(self, mock_run):
        """Test cancelling all jobs for a user."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Job._cancel_by_user("testuser")

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "scancel" in call_args
        assert "-u" in call_args
        assert "testuser" in call_args

    @mock.patch("slurm_cli.utils.jobs.subprocess.run")
    def test_cancel_by_user_verbose(self, mock_run, capsys):
        """Test cancelling user jobs with verbose."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Job._cancel_by_user("testuser", verbose=True)

        captured = capsys.readouterr()
        assert "All jobs for user 'testuser' cancelled" in captured.out


class TestJobAutocomplete:
    """Tests for Job.generate_autocomplete_options."""

    def test_generate_autocomplete_returns_script(self):
        """Test generate_autocomplete_options returns bash script."""
        script = Job.generate_autocomplete_options()

        assert "_slurm_cli_jobs_autocomplete" in script
        assert "COMPREPLY" in script

    def test_generate_autocomplete_contains_states(self):
        """Test autocomplete script contains job states."""
        script = Job.generate_autocomplete_options()

        assert "running" in script
        assert "pending" in script
        assert "completed" in script

    def test_generate_autocomplete_contains_filters(self):
        """Test autocomplete script contains filter options."""
        script = Job.generate_autocomplete_options()

        assert "user=" in script
        assert "partition=" in script
        assert "state=" in script

    def test_generate_autocomplete_show_command(self):
        """Test autocomplete script has show command handling."""
        script = Job.generate_autocomplete_options()

        assert "show)" in script
        assert "filter_options" in script

    def test_generate_autocomplete_delete_command(self):
        """Test autocomplete script has delete command handling."""
        script = Job.generate_autocomplete_options()

        assert "delete|del|cancel)" in script
        assert "cached_jobs" in script

    def test_generate_autocomplete_update_command(self):
        """Test autocomplete script has update command with options."""
        script = Job.generate_autocomplete_options()

        assert "update|modify|set)" in script
        assert "update_options" in script

    def test_generate_autocomplete_contains_update_options(self):
        """Test autocomplete script contains job update options."""
        script = Job.generate_autocomplete_options()

        # Time options
        assert "TimeLimit=" in script
        assert "StartTime=" in script
        assert "EndTime=" in script
        assert "Deadline=" in script

        # Resource options
        assert "NumNodes=" in script
        assert "NumCPUs=" in script
        assert "Priority=" in script
        assert "Gres=" in script

        # Node options
        assert "NodeList=" in script
        assert "ExcNodeList=" in script
        assert "Partition=" in script

        # Job configuration
        assert "Account=" in script
        assert "QOS=" in script
        assert "JobName=" in script
        assert "Comment=" in script
        assert "Dependency=" in script

        # I/O options
        assert "StdOut=" in script
        assert "StdErr=" in script
        assert "WorkDir=" in script

        # Boolean options
        assert "Contiguous=" in script
        assert "Requeue=" in script

        # Flags (no =)
        assert "ResetAccrueTime" in script

    def test_generate_autocomplete_yesno_options(self):
        """Test autocomplete handles yes/no options."""
        script = Job.generate_autocomplete_options()

        assert "contiguous|oversubscribe|reboot|shared)" in script
        assert '"yes no"' in script

    def test_generate_autocomplete_binary_options(self):
        """Test autocomplete handles 0/1 options."""
        script = Job.generate_autocomplete_options()

        assert "requeue)" in script
        assert '"0 1"' in script

    def test_generate_autocomplete_mailtype(self):
        """Test autocomplete handles mail type options."""
        script = Job.generate_autocomplete_options()

        assert "mailtype)" in script
        assert "BEGIN" in script
        assert "END" in script
        assert "FAIL" in script
        assert "ALL" in script

    def test_generate_autocomplete_dependency(self):
        """Test autocomplete handles dependency options."""
        script = Job.generate_autocomplete_options()

        assert "dependency)" in script
        assert "after:" in script
        assert "afterok:" in script
        assert "afternotok:" in script
        assert "singleton" in script

    def test_generate_autocomplete_uses_cache_functions(self):
        """Test autocomplete script uses cache functions."""
        script = Job.generate_autocomplete_options()

        assert "_slurm_cache_users" in script
        assert "_slurm_cache_partitions" in script
        assert "_slurm_cache_jobs" in script
        assert "_slurm_cache_qos" in script
        assert "_slurm_cache_reservations" in script


class TestJobUpdateOptions:
    """Tests for JOB_UPDATE_OPTIONS constant."""

    def test_update_options_has_yesno_type(self):
        """Test update options has yes/no type."""
        assert "yesno" in Job.JOB_UPDATE_OPTIONS
        assert "Contiguous" in Job.JOB_UPDATE_OPTIONS["yesno"]
        assert "Reboot" in Job.JOB_UPDATE_OPTIONS["yesno"]

    def test_update_options_has_binary_type(self):
        """Test update options has 0/1 type."""
        assert "binary" in Job.JOB_UPDATE_OPTIONS
        assert "Requeue" in Job.JOB_UPDATE_OPTIONS["binary"]

    def test_update_options_has_count_type(self):
        """Test update options has count type."""
        assert "count" in Job.JOB_UPDATE_OPTIONS
        assert "Priority" in Job.JOB_UPDATE_OPTIONS["count"]
        assert "NumCPUs" in Job.JOB_UPDATE_OPTIONS["count"]
        assert "NumNodes" in Job.JOB_UPDATE_OPTIONS["count"]

    def test_update_options_has_time_type(self):
        """Test update options has time type."""
        assert "time" in Job.JOB_UPDATE_OPTIONS
        assert "TimeLimit" in Job.JOB_UPDATE_OPTIONS["time"]
        assert "StartTime" in Job.JOB_UPDATE_OPTIONS["time"]
        assert "EndTime" in Job.JOB_UPDATE_OPTIONS["time"]
        assert "Deadline" in Job.JOB_UPDATE_OPTIONS["time"]

    def test_update_options_has_nodes_type(self):
        """Test update options has nodes type."""
        assert "nodes" in Job.JOB_UPDATE_OPTIONS
        assert "NodeList" in Job.JOB_UPDATE_OPTIONS["nodes"]
        assert "ExcNodeList" in Job.JOB_UPDATE_OPTIONS["nodes"]

    def test_update_options_has_partition_type(self):
        """Test update options has partition type."""
        assert "partition" in Job.JOB_UPDATE_OPTIONS
        assert "Partition" in Job.JOB_UPDATE_OPTIONS["partition"]

    def test_update_options_has_qos_type(self):
        """Test update options has QOS type."""
        assert "qos" in Job.JOB_UPDATE_OPTIONS
        assert "QOS" in Job.JOB_UPDATE_OPTIONS["qos"]

    def test_update_options_has_string_type(self):
        """Test update options has string type."""
        assert "string" in Job.JOB_UPDATE_OPTIONS
        assert "JobName" in Job.JOB_UPDATE_OPTIONS["string"]
        assert "Comment" in Job.JOB_UPDATE_OPTIONS["string"]
        assert "Dependency" in Job.JOB_UPDATE_OPTIONS["string"]
        assert "Gres" in Job.JOB_UPDATE_OPTIONS["string"]

    def test_update_options_has_flag_type(self):
        """Test update options has flag type (no value)."""
        assert "flag" in Job.JOB_UPDATE_OPTIONS
        assert "ResetAccrueTime" in Job.JOB_UPDATE_OPTIONS["flag"]

    def test_mail_types_defined(self):
        """Test MAIL_TYPES constant is defined."""
        assert hasattr(Job, "MAIL_TYPES")
        assert "BEGIN" in Job.MAIL_TYPES
        assert "END" in Job.MAIL_TYPES
        assert "FAIL" in Job.MAIL_TYPES
        assert "ALL" in Job.MAIL_TYPES

    def test_dependency_types_defined(self):
        """Test DEPENDENCY_TYPES constant is defined."""
        assert hasattr(Job, "DEPENDENCY_TYPES")
        assert "after:" in Job.DEPENDENCY_TYPES
        assert "afterok:" in Job.DEPENDENCY_TYPES
        assert "singleton" in Job.DEPENDENCY_TYPES


class TestJobProfileFields:
    """Tests for Job.get_profile_fields."""

    def test_get_profile_fields(self):
        """Test get_profile_fields returns expected fields."""
        fields = Job.get_profile_fields()

        assert "job_id" in fields
        assert "name" in fields
        assert "user_name" in fields
        assert "partition" in fields
        assert "job_state" in fields
        assert "endlimit" in fields


class TestJobInheritance:
    """Tests for Job inheritance."""

    def test_inherits_from_base_resource(self):
        """Test Job inherits from BaseSlurmResource."""
        from slurm_cli.utils.base_resource import BaseSlurmResource

        assert issubclass(Job, BaseSlurmResource)

    def test_has_required_methods(self):
        """Test Job has required methods."""
        assert hasattr(Job, "create")
        assert hasattr(Job, "update")
        assert hasattr(Job, "delete")
        assert hasattr(Job, "show")
