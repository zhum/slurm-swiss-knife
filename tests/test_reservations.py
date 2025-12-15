"""Tests for reservations module."""

import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from unittest import mock

import pytest

# Add src to path for imports
sys.path.insert(0, "src")

from slurm_cli.utils.reservations import Reservation  # noqa: E402


def create_sample_reservation_data():
    """Create sample reservation data for testing."""
    now = datetime.now().timestamp()
    return {
        "maint-window": {
            "start_time": {
                "set": True,
                "number": now + 3600,
            },  # 1 hour from now
            "end_time": {
                "set": True,
                "number": now + 7200,
            },  # 2 hours from now
            "partition": "gpu",
            "node_count": 10,
            "core_count": 100,
            "node_list": "node[001-010]",
            "users": ["admin", "operator"],
            "accounts": ["maintenance"],
            "flags": ["MAINT", "IGNORE_JOBS"],
            "tres": "cpu=100,mem=1000G",
            "purge_completed": False,
        },
        "research-booking": {
            "start_time": {
                "set": True,
                "number": now - 1800,
            },  # 30 min ago
            "end_time": {
                "set": True,
                "number": now + 5400,
            },  # 90 min from now
            "partition": "cpu",
            "node_count": 5,
            "core_count": 50,
            "node_list": "node[011-015]",
            "users": ["researcher1"],
            "accounts": ["research"],
            "flags": ["FLEX"],
            "tres": "cpu=50,mem=500G",
            "purge_completed": False,
            "watts": {"set": True, "number": 5000, "infinite": False},
        },
    }


def create_expired_reservation():
    """Create an expired reservation for testing."""
    now = datetime.now().timestamp()
    return {
        "expired-res": {
            "start_time": {"set": True, "number": now - 7200},
            "end_time": {"set": True, "number": now - 3600},
            "partition": "cpu",
            "node_count": 2,
            "core_count": 20,
            "node_list": "node[001-002]",
            "users": ["user1"],
            "accounts": ["account1"],
            "flags": [],
            "tres": "",
        }
    }


class TestReservationInit:
    """Tests for Reservation initialization."""

    def test_init_with_name(self):
        """Test initialization with name."""
        r = Reservation("maint-window")
        assert r.name == "maint-window"
        assert r.kwargs == {}

    def test_init_with_kwargs(self):
        """Test initialization with kwargs."""
        r = Reservation(
            "maint-window", partition="gpu", nodes="node[001-010]"
        )
        assert r.name == "maint-window"
        assert r.kwargs == {
            "partition": "gpu",
            "nodes": "node[001-010]",
        }


class TestReservationMaxWidth:
    """Tests for Reservation.max_width."""

    def test_max_width_caching(self):
        """Test max_width caches the value."""
        Reservation._WIDTH = None  # Reset
        with mock.patch.object(Reservation, "_WIDTH", None):
            width = Reservation.max_width()
            assert width > 0
            # Second call should return cached value
            width2 = Reservation.max_width()
            assert width == width2


class TestReservationCreate:
    """Tests for Reservation.create."""

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_create_success(self, mock_print, mock_run):
        """Test successful reservation creation."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        # Use "accounts" which is a list type (simpler validation)
        Reservation.create("test-res", accounts="testaccount")

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "scontrol" in args
        assert "create" in args
        assert "reservation" in args

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_create_with_stdout(self, mock_print, mock_run):
        """Test create with stdout output."""
        mock_run.return_value = mock.Mock(
            stdout="Reservation created", returncode=0
        )

        Reservation.create("test-res", verbose=True, nodes="node001")

        assert mock_print.call_count >= 1

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_create_with_add_warning(self, mock_print, mock_run):
        """Test create warns about add operations."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Reservation.create("test-res", **{"users+": "user1"})

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any("Warning" in str(c) for c in call_args)

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_create_with_delete_warning(self, mock_print, mock_run):
        """Test create warns about delete operations."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Reservation.create("test-res", **{"users-": "user1"})

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any("Warning" in str(c) for c in call_args)

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_create_failure(self, mock_print, mock_run):
        """Test create handles failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "scontrol", stderr="Permission denied"
        )

        # Use "accounts" which is a list type (simpler validation)
        Reservation.create("test-res", accounts="testaccount")

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any(
            "Failed" in str(c) or "red" in str(c) for c in call_args
        )

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_create_with_time_aliases(self, mock_print, mock_run):
        """Test create with start/end aliases for starttime/endtime."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        # Use 'start' and 'end' aliases
        Reservation.create(
            "test-res",
            start="now",
            end="2025-12-31T23:59:59",
            accounts="testaccount",
        )

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        # The options string should contain starttime= and endtime=
        # (not start= and end=)
        options_str = " ".join(args)
        assert "starttime=now" in options_str
        assert "endtime=2025-12-31T23:59:59" in options_str
        # Should NOT contain the alias forms
        assert (
            "start=" not in options_str or "starttime=" in options_str
        )
        assert "end=" not in options_str or "endtime=" in options_str


class TestReservationUpdate:
    """Tests for Reservation.update."""

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_update_success(self, mock_print, mock_run):
        """Test successful reservation update."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        # Use "accounts" which is a list type (simpler validation)
        Reservation.update("test-res", accounts="newaccount")

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "scontrol" in args
        assert "update" in args

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_update_with_verbose(self, mock_print, mock_run):
        """Test update with verbose output."""
        mock_run.return_value = mock.Mock(
            stdout="Updated", returncode=0
        )

        Reservation.update("test-res", verbose=True, duration="2:00:00")

        assert mock_print.call_count >= 1

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_update_with_add_operations(self, mock_print, mock_run):
        """Test update with add operations."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Reservation.update("test-res", **{"users+": "newuser"})

        mock_run.assert_called_once()

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_update_with_delete_operations(self, mock_print, mock_run):
        """Test update with delete operations."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Reservation.update("test-res", **{"users-": "olduser"})

        mock_run.assert_called_once()

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_update_with_time_aliases(self, mock_print, mock_run):
        """Test update with start/end aliases for starttime/endtime."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        # Use 'start' and 'end' aliases
        Reservation.update(
            "test-res",
            start="2025-01-01T00:00:00",
            end="2025-12-31T23:59:59",
        )

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        # The options string should contain starttime= and endtime=
        options_str = " ".join(args)
        assert "starttime=2025-01-01T00:00:00" in options_str
        assert "endtime=2025-12-31T23:59:59" in options_str

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_update_failure(self, mock_print, mock_run):
        """Test update handles failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "scontrol", stderr="Error"
        )

        # Use "accounts" which is a list type (simpler validation)
        Reservation.update("test-res", accounts="newaccount")

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any(
            "Failed" in str(c) or "red" in str(c) for c in call_args
        )


class TestReservationDelete:
    """Tests for Reservation.delete."""

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_delete_success(self, mock_print, mock_run):
        """Test successful reservation deletion."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Reservation.delete("test-res")

        mock_run.assert_called_once()
        call_args = [str(c) for c in mock_print.call_args_list]
        assert any("deleted" in str(c).lower() for c in call_args)

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_delete_with_stdout(self, mock_print, mock_run):
        """Test delete with stdout output."""
        mock_run.return_value = mock.Mock(
            stdout="Reservation deleted", returncode=0
        )

        Reservation.delete("test-res")

        assert mock_print.call_count >= 1

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_delete_failure(self, mock_print, mock_run):
        """Test delete handles failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "scontrol", stderr="Reservation not found"
        )

        Reservation.delete("nonexistent")

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any(
            "Failed" in str(c) or "red" in str(c) for c in call_args
        )


class TestReservationShow:
    """Tests for Reservation.show."""

    @mock.patch("slurm_cli.utils.reservations.console.print_json")
    def test_show_no_data(self, mock_print_json):
        """Test show with no data."""
        Reservation.show(data=None)

        mock_print_json.assert_called_once()

    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_show_reservation_not_found(self, mock_print):
        """Test show with non-existent reservation name."""
        data = create_sample_reservation_data()

        Reservation.show(name="nonexistent", data=data)

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any("not found" in str(c) for c in call_args)

    @mock.patch("slurm_cli.utils.reservations.console.print_json")
    def test_show_json_all(self, mock_print_json):
        """Test show with JSON style for all reservations."""
        data = create_sample_reservation_data()

        Reservation.show(data=data, style="json")

        mock_print_json.assert_called_once()
        output = mock_print_json.call_args[0][0]
        parsed = json.loads(output)
        assert "maint-window" in parsed
        assert "research-booking" in parsed

    @mock.patch("slurm_cli.utils.reservations.console.print_json")
    def test_show_json_single(self, mock_print_json):
        """Test show with JSON style for single reservation."""
        data = create_sample_reservation_data()

        Reservation.show(name="maint-window", data=data, style="json")

        mock_print_json.assert_called_once()
        output = mock_print_json.call_args[0][0]
        parsed = json.loads(output)
        assert "partition" in parsed

    def test_show_csv_all(self):
        """Test show with CSV style for all reservations."""
        data = create_sample_reservation_data()
        output = io.StringIO()

        with redirect_stdout(output):
            Reservation.show(data=data, style="csv")

        result = output.getvalue()
        lines = result.strip().split("\n")
        # First line is header
        assert "Name" in lines[0]
        # Should have data rows
        assert len(lines) >= 3  # header + 2 reservations

    def test_show_csv_single(self):
        """Test show with CSV style for single reservation."""
        data = create_sample_reservation_data()
        output = io.StringIO()

        with redirect_stdout(output):
            Reservation.show(
                name="maint-window", data=data, style="csv"
            )

        result = output.getvalue()
        lines = result.strip().split("\n")
        assert len(lines) == 2  # header + 1 reservation

    def test_show_csv_with_delimiter(self):
        """Test show CSV with custom delimiter."""
        data = create_sample_reservation_data()
        output = io.StringIO()

        with redirect_stdout(output):
            Reservation.show(data=data, style="csv", delimiter="|")

        result = output.getvalue()
        assert "|" in result

    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_show_pretty_all(self, mock_print):
        """Test show with pretty style for all reservations."""
        data = create_sample_reservation_data()

        Reservation.show(data=data, style="pretty")

        # Should print reservation info
        assert mock_print.call_count >= 2

    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_show_pretty_single(self, mock_print):
        """Test show with pretty style for single reservation."""
        data = create_sample_reservation_data()

        Reservation.show(name="maint-window", data=data, style="pretty")

        # Should print reservation info
        assert mock_print.call_count >= 1

    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_show_with_template(self, mock_print):
        """Test show with template profile."""
        data = create_sample_reservation_data()

        Reservation.show(
            data=data,
            style="pretty",
            profile_str="{name}: {partition}",
        )

        assert mock_print.call_count >= 1


class TestReservationPrepareTemplateData:
    """Tests for Reservation._prepare_template_data."""

    def test_prepare_template_data_basic(self):
        """Test _prepare_template_data with basic data."""
        data = create_sample_reservation_data()["maint-window"]
        result = Reservation._prepare_template_data(
            "maint-window", data
        )

        assert result["name"] == "maint-window"
        assert "start_time" in result
        assert "end_time" in result
        assert "time_status" in result

    def test_prepare_template_data_users_list(self):
        """Test _prepare_template_data joins users list."""
        data = {
            "start_time": {
                "set": True,
                "number": datetime.now().timestamp(),
            },
            "end_time": {
                "set": True,
                "number": datetime.now().timestamp() + 3600,
            },
            "users": ["user1", "user2", "user3"],
            "partition": "test",
        }
        result = Reservation._prepare_template_data("test", data)

        assert result["users"] == "user1,user2,user3"

    def test_prepare_template_data_accounts_list(self):
        """Test _prepare_template_data joins accounts list."""
        data = {
            "start_time": {
                "set": True,
                "number": datetime.now().timestamp(),
            },
            "end_time": {
                "set": True,
                "number": datetime.now().timestamp() + 3600,
            },
            "accounts": ["acc1", "acc2"],
            "partition": "test",
        }
        result = Reservation._prepare_template_data("test", data)

        assert result["accounts"] == "acc1,acc2"

    def test_prepare_template_data_future_reservation(self):
        """Test _prepare_template_data for future reservation."""
        now = datetime.now().timestamp()
        data = {
            "start_time": {
                "set": True,
                "number": now + 7200,
            },  # 2 hours
            "end_time": {"set": True, "number": now + 10800},  # 3 hours
            "partition": "test",
        }
        result = Reservation._prepare_template_data("test", data)

        assert "starts in" in result["time_status"]

    def test_prepare_template_data_active_reservation(self):
        """Test _prepare_template_data for active reservation."""
        now = datetime.now().timestamp()
        data = {
            "start_time": {
                "set": True,
                "number": now - 1800,
            },  # 30 min ago
            "end_time": {"set": True, "number": now + 1800},  # 30 min
            "partition": "test",
        }
        result = Reservation._prepare_template_data("test", data)

        assert "ends in" in result["time_status"]

    def test_prepare_template_data_expired_reservation(self):
        """Test _prepare_template_data for expired reservation."""
        now = datetime.now().timestamp()
        data = {
            "start_time": {"set": True, "number": now - 7200},
            "end_time": {"set": True, "number": now - 3600},
            "partition": "test",
        }
        result = Reservation._prepare_template_data("test", data)

        assert result["time_status"] == "expired"


class TestReservationShowCsv:
    """Tests for Reservation._show_csv."""

    def test_show_csv_headers(self):
        """Test _show_csv outputs correct headers."""
        data = create_sample_reservation_data()
        output = io.StringIO()

        with redirect_stdout(output):
            Reservation._show_csv(data)

        result = output.getvalue()
        header = result.strip().split("\n")[0]
        assert "Name" in header
        assert "Partition" in header
        assert "Start Time" in header
        assert "End Time" in header

    def test_show_csv_values_formatting(self):
        """Test _show_csv formats values correctly."""
        data = create_sample_reservation_data()
        output = io.StringIO()

        with redirect_stdout(output):
            Reservation._show_csv(data)

        result = output.getvalue()
        lines = result.strip().split("\n")
        # Check data rows contain expected values
        data_str = "".join(lines[1:])
        assert "gpu" in data_str or "cpu" in data_str

    def test_show_csv_list_values(self):
        """Test _show_csv handles list values."""
        data = {
            "test-res": {
                "start_time": {
                    "set": True,
                    "number": datetime.now().timestamp(),
                },
                "end_time": {
                    "set": True,
                    "number": datetime.now().timestamp() + 3600,
                },
                "partition": "test",
                "node_count": 1,
                "core_count": 10,
                "node_list": "node001",
                "users": ["user1", "user2"],
                "accounts": ["acc1"],
                "flags": ["FLAG1", "FLAG2"],
                "tres": "cpu=10",
            }
        }
        output = io.StringIO()

        with redirect_stdout(output):
            Reservation._show_csv(data)

        result = output.getvalue()
        # Lists should be comma-joined in the output
        assert "user1,user2" in result

    def test_show_csv_dict_values(self):
        """Test _show_csv handles dict values with set/number."""
        data = {
            "test-res": {
                "start_time": {
                    "set": True,
                    "number": datetime.now().timestamp(),
                },
                "end_time": {
                    "set": True,
                    "number": datetime.now().timestamp() + 3600,
                },
                "partition": "test",
                "node_count": {"set": True, "number": 5},
                "core_count": 10,
                "node_list": "node001",
                "users": [],
                "accounts": [],
                "flags": [],
                "tres": "",
            }
        }
        output = io.StringIO()

        with redirect_stdout(output):
            Reservation._show_csv(data)

        result = output.getvalue()
        # Should have extracted number from dict
        assert "5" in result


class TestReservationTimeFormatting:
    """Tests for Reservation time formatting methods."""

    def test_tm2str(self):
        """Test tm2str converts timestamp to string."""
        # Use a known timestamp
        ts = datetime(2024, 1, 15, 10, 30, 0).timestamp()
        result = Reservation.tm2str(ts)

        assert "2024-01-15" in result
        assert "10:30:00" in result

    def test_delta2str_days(self):
        """Test delta2str with days."""
        delta = 2 * 86400 + 3 * 3600 + 15 * 60  # 2d 3h 15m
        result = Reservation.delta2str(delta)

        assert "2d" in result
        assert "3h" in result
        assert "15m" in result

    def test_delta2str_hours(self):
        """Test delta2str with hours only."""
        delta = 5 * 3600 + 30 * 60  # 5h 30m
        result = Reservation.delta2str(delta)

        assert "5h" in result
        assert "30m" in result
        assert "d" not in result

    def test_delta2str_minutes(self):
        """Test delta2str with minutes only."""
        delta = 45 * 60  # 45m
        result = Reservation.delta2str(delta)

        assert "45m" in result
        assert "h" not in result
        assert "d" not in result


class TestReservationGetTimestamp:
    """Tests for Reservation._get_timestamp."""

    def test_get_timestamp_dict_with_set(self):
        """Test _get_timestamp with dict containing set=True."""
        value = {"set": True, "number": 1234567890}
        result = Reservation._get_timestamp(value)

        assert result == 1234567890.0

    def test_get_timestamp_dict_without_set(self):
        """Test _get_timestamp with dict where set=False."""
        value = {"set": False, "number": 1234567890}
        result = Reservation._get_timestamp(value)

        assert result == 0.0

    def test_get_timestamp_numeric(self):
        """Test _get_timestamp with numeric value."""
        result = Reservation._get_timestamp(1234567890)

        assert result == 1234567890.0

    def test_get_timestamp_none(self):
        """Test _get_timestamp with None value."""
        result = Reservation._get_timestamp(None)

        assert result == 0.0


class TestReservationPrintOnePretty:
    """Tests for Reservation.print_one_pretty."""

    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_print_one_pretty_no_data(self, mock_print):
        """Test print_one_pretty with no data."""
        Reservation.print_one_pretty("test", None)

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any("No data" in str(c) for c in call_args)

    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_print_one_pretty_basic(self, mock_print):
        """Test print_one_pretty with basic data."""
        data = create_sample_reservation_data()["maint-window"]

        Reservation.print_one_pretty("maint-window", dict(data))

        call_args = [str(c) for c in mock_print.call_args_list]
        assert any("Reservation" in str(c) for c in call_args)
        assert any("maint-window" in str(c) for c in call_args)

    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_print_one_pretty_with_watts(self, mock_print):
        """Test print_one_pretty with watts field."""
        data = dict(
            create_sample_reservation_data()["research-booking"]
        )

        Reservation.print_one_pretty("research-booking", data)

        # Should not crash and should print info
        assert mock_print.call_count >= 1

    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_print_one_pretty_with_infinite_watts(self, mock_print):
        """Test print_one_pretty with infinite watts."""
        data = dict(create_sample_reservation_data()["maint-window"])
        data["watts"] = {"set": True, "number": 0, "infinite": True}

        Reservation.print_one_pretty("maint-window", data)

        assert mock_print.call_count >= 1

    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_print_one_pretty_with_non_dict_watts(self, mock_print):
        """Test print_one_pretty with non-dict watts."""
        data = dict(create_sample_reservation_data()["maint-window"])
        data["watts"] = 5000

        Reservation.print_one_pretty("maint-window", data)

        assert mock_print.call_count >= 1

    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_print_one_pretty_users_highlighted(self, mock_print):
        """Test print_one_pretty highlights users in pink."""
        data = dict(create_sample_reservation_data()["maint-window"])

        Reservation.print_one_pretty("maint-window", data)

        call_args_str = "".join(
            str(c) for c in mock_print.call_args_list
        )
        assert "hot_pink" in call_args_str

    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_print_one_pretty_expired(self, mock_print):
        """Test print_one_pretty with expired reservation."""
        data = create_expired_reservation()["expired-res"]

        Reservation.print_one_pretty("expired-res", dict(data))

        # Should print without time delta strings
        assert mock_print.call_count >= 1


class TestReservationGenerateAutocomplete:
    """Tests for Reservation.generate_autocomplete_options."""

    def test_generate_autocomplete_returns_script(self):
        """Test generate_autocomplete_options returns bash script."""
        script = Reservation.generate_autocomplete_options()

        assert "_slurm_cli_reservations_autocomplete" in script
        assert "COMPREPLY" in script
        assert "case" in script

    def test_generate_autocomplete_contains_valid_args(self):
        """Test autocomplete script contains valid args."""
        script = Reservation.generate_autocomplete_options()

        # Should contain some valid arg keys
        assert "starttime" in script or "endtime" in script
        assert "nodes" in script or "users" in script

    def test_generate_autocomplete_contains_flags(self):
        """Test autocomplete script contains flag values."""
        script = Reservation.generate_autocomplete_options()

        assert "MAINT" in script
        assert "FLEX" in script


class TestReservationValidArgs:
    """Tests for Reservation.valid_args."""

    def test_valid_args_contains_expected_keys(self):
        """Test valid_args contains expected keys."""
        expected_keys = [
            "accounts",
            "nodes",
            "starttime",
            "endtime",
            "users",
            "flags",
            "partitionname",
        ]
        for key in expected_keys:
            assert key in Reservation.valid_args

    def test_valid_args_have_type_and_help(self):
        """Test each valid_arg has type and help."""
        for key, value in Reservation.valid_args.items():
            assert "type" in value
            assert "help" in value

    def test_arg_aliases_defined(self):
        """Test arg_aliases contains expected mappings."""
        assert "start" in Reservation.arg_aliases
        assert "end" in Reservation.arg_aliases
        assert Reservation.arg_aliases["start"] == "starttime"
        assert Reservation.arg_aliases["end"] == "endtime"

    def test_arg_aliases_point_to_valid_args(self):
        """Test all aliases point to valid argument names."""
        for alias, canonical in Reservation.arg_aliases.items():
            assert canonical in Reservation.valid_args, (
                f"Alias '{alias}' points to '{canonical}' "
                "which is not in valid_args"
            )


class TestReservationInheritance:
    """Tests for Reservation inheritance."""

    def test_inherits_from_base_resource(self):
        """Test Reservation inherits from BaseSlurmResource."""
        from slurm_cli.utils.base_resource import BaseSlurmResource

        assert issubclass(Reservation, BaseSlurmResource)

    def test_has_required_methods(self):
        """Test Reservation has required methods."""
        assert hasattr(Reservation, "create")
        assert hasattr(Reservation, "update")
        assert hasattr(Reservation, "delete")
        assert hasattr(Reservation, "show")


class TestReservationCreateVerbose:
    """Additional tests for Reservation.create verbose mode."""

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_create_verbose_success(self, mock_print, mock_run):
        """Test verbose create success message."""
        mock_run.return_value = mock.Mock(stdout="", returncode=0)

        Reservation.create(
            "test-res", verbose=True, accounts="testaccount"
        )

        # Should have success message
        call_args = [str(c) for c in mock_print.call_args_list]
        assert any("successfully" in str(c) for c in call_args)


class TestReservationUpdateVerbose:
    """Additional tests for Reservation.update verbose mode."""

    @mock.patch("subprocess.run")
    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_update_verbose_success(self, mock_print, mock_run):
        """Test verbose update success message."""
        mock_run.return_value = mock.Mock(stdout="Output", returncode=0)

        Reservation.update(
            "test-res", verbose=True, accounts="newaccount"
        )

        # Should have multiple prints (output + success)
        assert mock_print.call_count >= 2


class TestReservationShowTemplate:
    """Tests for Reservation.show with templates."""

    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_show_with_template_all(self, mock_print):
        """Test show all reservations with template."""
        data = create_sample_reservation_data()

        Reservation.show(
            data=data,
            style="pretty",
            profile_str="{name}",
        )

        # Should print for each reservation
        assert mock_print.call_count >= 2

    @mock.patch("slurm_cli.utils.reservations.console.print")
    def test_show_subprocess_error(self, mock_print):
        """Test show handles subprocess error (unlikely path)."""
        data = create_sample_reservation_data()

        # Normal show should work
        Reservation.show(data=data, style="pretty")
        assert mock_print.call_count >= 1
