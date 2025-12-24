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
        """Test delete without job ID."""
        Job.delete("")
        captured = capsys.readouterr()
        assert "Job ID is required" in captured.out


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
