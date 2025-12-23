"""Tests for the Event resource class."""

import io
import subprocess
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

import pytest

from slurm_cli.utils.events import EVENT_FILTER_OPTIONS, Event

MOCK_EVENTS_DATA = """Cluster|Cluster Nodes|Duration|TimeStart|TimeEnd|Event|EventRaw|NodeName|State|StateRaw|TRES|User|Reason|
oci-ord-cs-002||07:24:18|2025-12-12T09:31:19|Unknown|Node|2|h100-pool0-0290|DRAIN|512|cpu=224|slurm(450)|Not responding|
oci-ord-cs-002||00:27:07|2025-12-10T23:50:01|2025-12-11T00:17:08|Node|2|h100-pool0-0417|DOWN|1|cpu=224|slurm(450)|Not responding|
oci-ord-cs-002||00:19:51|2025-12-11T00:55:41|2025-12-11T01:15:32|Node|2|h100-pool0-0364|DRAIN|514|cpu=224|root(0)|[HC] temp issue|
"""


class TestEventInit:
    """Tests for Event initialization."""

    def test_event_init(self):
        """Test Event initialization."""
        event = Event(cluster="test", node="node1")
        assert event.kwargs["cluster"] == "test"
        assert event.kwargs["node"] == "node1"


class TestEventParseEvents:
    """Tests for Event._parse_events method."""

    def test_parse_events_valid_data(self):
        """Test parsing valid event data."""
        events = Event._parse_events(MOCK_EVENTS_DATA)
        assert len(events) == 3
        assert events[0]["node"] == "h100-pool0-0290"
        assert events[0]["state"] == "DRAIN"
        assert events[1]["node"] == "h100-pool0-0417"
        assert events[1]["state"] == "DOWN"

    def test_parse_events_empty_data(self):
        """Test parsing empty data."""
        events = Event._parse_events("")
        assert len(events) == 0

    def test_parse_events_header_only(self):
        """Test parsing header only."""
        events = Event._parse_events(
            "Cluster|Duration|NodeName|State|\n"
        )
        assert len(events) == 0


class TestEventFilters:
    """Tests for Event filtering."""

    def test_apply_filters_by_state(self):
        """Test filtering by state."""
        events = Event._parse_events(MOCK_EVENTS_DATA)
        filtered = Event._apply_filters(events, {"States": "DRAIN"})
        assert len(filtered) == 2
        assert all("DRAIN" in e["state"] for e in filtered)

    def test_apply_filters_by_node(self):
        """Test filtering by node."""
        events = Event._parse_events(MOCK_EVENTS_DATA)
        filtered = Event._apply_filters(events, {"Nodes": "0290"})
        assert len(filtered) == 1
        assert "0290" in filtered[0]["node"]

    def test_apply_filters_by_user(self):
        """Test filtering by user."""
        events = Event._parse_events(MOCK_EVENTS_DATA)
        filtered = Event._apply_filters(events, {"User": "root"})
        assert len(filtered) == 1
        assert "root" in filtered[0]["user"]

    def test_extract_cpus(self):
        """Test extracting CPU count from TRES."""
        assert Event._extract_cpus("cpu=224,mem=1024M") == 224
        assert Event._extract_cpus("mem=1024M") == 0
        assert Event._extract_cpus("") == 0

    def test_extract_nodes(self):
        """Test extracting node count from TRES."""
        assert Event._extract_nodes("cpu=224,node=10") == 10
        assert Event._extract_nodes("cpu=224") == 0
        assert Event._extract_nodes("") == 0


def mock_exists_with_no_json_flag(path):
    """Mock os.path.exists to return True for the no-JSON flag file."""
    from slurm_cli.utils.events import EVENTS_NO_JSON_FLAG

    if path == EVENTS_NO_JSON_FLAG:
        return True  # Skip JSON attempt
    return False  # No cache files


class TestEventShow:
    """Tests for Event.show method."""

    @patch("slurm_cli.utils.events.subprocess.run")
    @patch(
        "slurm_cli.utils.events.os.path.exists",
        side_effect=mock_exists_with_no_json_flag,
    )
    def test_show_pretty_style(self, mock_exists, mock_run):
        """Test show with pretty style."""
        mock_run.return_value = MagicMock(
            stdout=MOCK_EVENTS_DATA, stderr=""
        )
        # Should not crash
        Event.show(style="pretty")
        mock_run.assert_called_once()

    @patch("slurm_cli.utils.events.subprocess.run")
    @patch(
        "slurm_cli.utils.events.os.path.exists",
        side_effect=mock_exists_with_no_json_flag,
    )
    def test_show_json_style(self, mock_exists, mock_run):
        """Test show with json style."""
        mock_run.return_value = MagicMock(
            stdout=MOCK_EVENTS_DATA, stderr=""
        )
        Event.show(style="json")
        mock_run.assert_called_once()

    @patch("slurm_cli.utils.events.subprocess.run")
    @patch(
        "slurm_cli.utils.events.os.path.exists",
        side_effect=mock_exists_with_no_json_flag,
    )
    def test_show_csv_style(self, mock_exists, mock_run):
        """Test show with csv style."""
        mock_run.return_value = MagicMock(
            stdout=MOCK_EVENTS_DATA, stderr=""
        )
        output = io.StringIO()
        with redirect_stdout(output):
            Event.show(style="csv", delimiter="|")
        result = output.getvalue()
        assert "|" in result

    @patch("slurm_cli.utils.events.subprocess.run")
    @patch(
        "slurm_cli.utils.events.os.path.exists",
        side_effect=mock_exists_with_no_json_flag,
    )
    def test_show_with_filter(self, mock_exists, mock_run):
        """Test show with filter."""
        mock_run.return_value = MagicMock(
            stdout=MOCK_EVENTS_DATA, stderr=""
        )
        Event.show(field="States=DRAIN")
        mock_run.assert_called_once()

    @patch(
        "slurm_cli.utils.events.os.path.exists",
        side_effect=mock_exists_with_no_json_flag,
    )
    def test_show_subprocess_error(self, mock_exists):
        """Test show with subprocess error."""
        error = subprocess.CalledProcessError(
            1, "sacctmgr", stderr="Permission denied"
        )
        with patch(
            "slurm_cli.utils.events.subprocess.run", side_effect=error
        ):
            output = io.StringIO()
            with redirect_stdout(output):
                Event.show()
            result = output.getvalue()
            assert "Failed to show events" in result


class TestEventReadOnly:
    """Tests for Event read-only nature."""

    def test_create_not_allowed(self):
        """Test that create prints error message."""
        output = io.StringIO()
        with redirect_stdout(output):
            Event.create()
        assert "cannot be created" in output.getvalue()

    def test_update_not_allowed(self):
        """Test that update prints error message."""
        output = io.StringIO()
        with redirect_stdout(output):
            Event.update()
        assert "cannot be updated" in output.getvalue()

    def test_delete_not_allowed(self):
        """Test that delete prints error message."""
        output = io.StringIO()
        with redirect_stdout(output):
            Event.delete()
        assert "cannot be deleted" in output.getvalue()


class TestEventFilterOptions:
    """Tests for EVENT_FILTER_OPTIONS constant."""

    def test_filter_options_defined(self):
        """Test that EVENT_FILTER_OPTIONS is defined."""
        assert EVENT_FILTER_OPTIONS is not None
        assert len(EVENT_FILTER_OPTIONS) > 0

    def test_filter_options_contains_expected(self):
        """Test expected filter options are present."""
        expected = [
            "Clusters",
            "CondFlags",
            "Nodes",
            "States",
            "User",
        ]
        for opt in expected:
            assert opt in EVENT_FILTER_OPTIONS


class TestEventAutocomplete:
    """Tests for Event.generate_autocomplete_options method."""

    def test_generate_autocomplete_returns_string(self):
        """Test that generate_autocomplete_options returns a string."""
        result = Event.generate_autocomplete_options()
        assert isinstance(result, str)

    def test_autocomplete_contains_function(self):
        """Test autocomplete contains function definition."""
        result = Event.generate_autocomplete_options()
        assert "_slurm_cli_events_autocomplete()" in result

    def test_autocomplete_contains_filter_options(self):
        """Test autocomplete contains filter options."""
        result = Event.generate_autocomplete_options()
        assert "Clusters=" in result
        assert "States=" in result
        assert "Nodes=" in result

    def test_autocomplete_contains_condflags_value(self):
        """Test autocomplete contains CondFlags=Open."""
        result = Event.generate_autocomplete_options()
        assert "Open" in result


class TestEventProfileFields:
    """Tests for Event.get_profile_fields method."""

    def test_get_profile_fields_returns_dict(self):
        """Test that get_profile_fields returns a dict."""
        result = Event.get_profile_fields()
        assert isinstance(result, dict)

    def test_get_profile_fields_contains_expected(self):
        """Test expected fields are present."""
        result = Event.get_profile_fields()
        expected = ["cluster", "node", "state", "user", "reason"]
        for key in expected:
            assert key in result


class TestEventInheritance:
    """Tests for Event class inheritance."""

    def test_inherits_from_base_resource(self):
        """Test that Event inherits from BaseSlurmResource."""
        from slurm_cli.utils.base_resource import BaseSlurmResource

        assert issubclass(Event, BaseSlurmResource)

    def test_has_required_methods(self):
        """Test that Event has required methods."""
        assert hasattr(Event, "show")
        assert hasattr(Event, "create")
        assert hasattr(Event, "update")
        assert hasattr(Event, "delete")
        assert callable(Event.show)
