"""Tests for the Event resource class."""

import io
import subprocess
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

import pytest

from slurm_cli.utils.events import (
    EVENT_FILTER_OPTIONS,
    EVENTS_NO_JSON_FLAG,
    Event,
    expand_node_ranges,
)

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


class TestExpandNodeRanges:
    """Tests for expand_node_ranges function."""

    def test_simple_range(self):
        """Test expanding simple node range."""
        result = expand_node_ranges("node[1-3]")
        assert result == {"node1", "node2", "node3"}

    def test_range_with_leading_zeros(self):
        """Test expanding range with leading zeros."""
        result = expand_node_ranges("node[01-03]")
        assert result == {"node01", "node02", "node03"}

    def test_comma_separated_nodes(self):
        """Test expanding comma-separated nodes."""
        result = expand_node_ranges("node1,node2,node3")
        assert result == {"node1", "node2", "node3"}

    def test_mixed_ranges(self):
        """Test expanding mixed ranges."""
        result = expand_node_ranges("a[1-2],b[1-2]")
        assert result == {"a1", "a2", "b1", "b2"}

    def test_range_with_suffix(self):
        """Test expanding range with suffix."""
        result = expand_node_ranges("node[1-2]-gpu")
        assert result == {"node1-gpu", "node2-gpu"}

    def test_single_value_in_brackets(self):
        """Test single value in brackets (no range)."""
        result = expand_node_ranges("node[5]")
        assert result == {"node5"}

    def test_empty_string(self):
        """Test expanding empty string."""
        result = expand_node_ranges("")
        assert result == set()

    def test_single_node(self):
        """Test single node without range."""
        result = expand_node_ranges("node1")
        assert result == {"node1"}

    def test_empty_part(self):
        """Test empty part in comma-separated list."""
        result = expand_node_ranges("node1,,node2")
        assert result == {"node1", "node2"}


class TestParseJsonEvents:
    """Tests for Event._parse_json_events method."""

    def test_parse_valid_json(self):
        """Test parsing valid JSON events."""
        json_data = (
            '{"events": [{"NodeName": "node1", "State": "DRAIN"}]}'
        )
        events = Event._parse_json_events(json_data)
        assert len(events) == 1
        assert events[0]["node"] == "node1"
        assert events[0]["state"] == "DRAIN"

    def test_parse_empty_events(self):
        """Test parsing JSON with empty events array."""
        json_data = '{"events": []}'
        events = Event._parse_json_events(json_data)
        assert len(events) == 0

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns empty list."""
        events = Event._parse_json_events("not valid json")
        assert events == []

    def test_parse_json_with_multiple_events(self):
        """Test parsing JSON with multiple events."""
        json_data = """{"events": [
            {"NodeName": "node1", "State": "DOWN", "User": "admin"},
            {"NodeName": "node2", "State": "DRAIN", "Reason": "maint"}
        ]}"""
        events = Event._parse_json_events(json_data)
        assert len(events) == 2
        assert events[0]["node"] == "node1"
        assert events[1]["node"] == "node2"
        assert events[1]["reason"] == "maint"


class TestFetchEvents:
    """Tests for Event._fetch_events method."""

    @patch("slurm_cli.utils.events.subprocess.run")
    @patch("slurm_cli.utils.events.os.path.exists")
    def test_fetch_events_json_success(self, mock_exists, mock_run):
        """Test fetching events with JSON format success."""
        mock_exists.return_value = False  # No flag file
        json_response = (
            '{"events": [{"NodeName": "node1", "State": "DRAIN"}]}'
        )
        mock_run.return_value = MagicMock(
            stdout=json_response, stderr=""
        )

        events = Event._fetch_events()

        assert len(events) == 1
        assert events[0]["node"] == "node1"
        # Should have used --json
        call_args = mock_run.call_args[0][0]
        assert "--json" in call_args

    @patch("slurm_cli.utils.events.subprocess.run")
    @patch("slurm_cli.utils.events.os.path.exists")
    @patch("builtins.open", create=True)
    def test_fetch_events_json_fails_sets_flag(
        self, mock_open, mock_exists, mock_run
    ):
        """Test JSON failure sets flag and falls back to text."""
        mock_exists.return_value = False  # No flag file initially

        # First call (JSON) fails with unparseable output
        # Second call (text) succeeds
        mock_run.side_effect = [
            MagicMock(stdout="not json", stderr=""),  # JSON attempt
            MagicMock(
                stdout=MOCK_EVENTS_DATA, stderr=""
            ),  # Text fallback
        ]

        events = Event._fetch_events()

        # Should have two calls - JSON then text
        assert mock_run.call_count == 2
        # Should have opened flag file to write
        mock_open.assert_called()

    @patch("slurm_cli.utils.events.subprocess.run")
    @patch("slurm_cli.utils.events.os.path.exists")
    def test_fetch_events_skips_json_with_flag(
        self, mock_exists, mock_run
    ):
        """Test fetch events skips JSON when flag file exists."""

        def exists_side_effect(path):
            return path == EVENTS_NO_JSON_FLAG

        mock_exists.side_effect = exists_side_effect
        mock_run.return_value = MagicMock(
            stdout=MOCK_EVENTS_DATA, stderr=""
        )

        events = Event._fetch_events()

        assert len(events) == 3  # From MOCK_EVENTS_DATA
        # Should NOT have used --json
        call_args = mock_run.call_args[0][0]
        assert "--json" not in call_args

    @patch("slurm_cli.utils.events.subprocess.run")
    @patch("slurm_cli.utils.events.os.path.exists")
    @patch("builtins.open", create=True)
    def test_fetch_events_json_exception_sets_flag(
        self, mock_open, mock_exists, mock_run
    ):
        """Test JSON subprocess error sets flag and falls back."""
        mock_exists.return_value = False  # No flag file

        # First call (JSON) raises exception
        # Second call (text) succeeds
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "sacctmgr"),  # JSON fails
            MagicMock(stdout=MOCK_EVENTS_DATA, stderr=""),  # Text works
        ]

        events = Event._fetch_events()

        assert len(events) == 3
        assert mock_run.call_count == 2
        mock_open.assert_called()


class TestShowWithNodeFilter:
    """Tests for Event.show with node filter resolution."""

    @patch("slurm_cli.utils.events.subprocess.run")
    @patch("slurm_cli.utils.events.os.path.exists")
    @patch("slurm_cli.utils.events.resolve_node_filter")
    @patch("slurm_cli.utils.events.is_node_filter")
    def test_show_resolves_node_filter(
        self, mock_is_filter, mock_resolve, mock_exists, mock_run
    ):
        """Test show resolves node filter expressions."""
        mock_exists.side_effect = mock_exists_with_no_json_flag
        mock_is_filter.return_value = True
        mock_resolve.return_value = "node1,node2"
        mock_run.return_value = MagicMock(
            stdout=MOCK_EVENTS_DATA, stderr=""
        )

        Event.show(field="Nodes=partition=gpu")

        mock_resolve.assert_called_once_with("partition=gpu")

    @patch("slurm_cli.utils.events.subprocess.run")
    @patch("slurm_cli.utils.events.os.path.exists")
    @patch("slurm_cli.utils.events.resolve_node_filter")
    @patch("slurm_cli.utils.events.is_node_filter")
    def test_show_updates_nodes_filter(
        self, mock_is_filter, mock_resolve, mock_exists, mock_run
    ):
        """Test show updates nodes filter with resolved value."""
        mock_exists.side_effect = mock_exists_with_no_json_flag
        mock_is_filter.return_value = True
        mock_resolve.return_value = "resolved-node1,resolved-node2"
        mock_run.return_value = MagicMock(
            stdout=MOCK_EVENTS_DATA, stderr=""
        )

        Event.show(field="nodes=partition=defq")

        mock_resolve.assert_called_once()
        # The sacctmgr call should include the resolved nodes
        call_args = mock_run.call_args[0][0]
        assert any("resolved-node" in str(arg) for arg in call_args)

    @patch("slurm_cli.utils.events.os.path.exists")
    @patch("slurm_cli.utils.events.resolve_node_filter")
    @patch("slurm_cli.utils.events.is_node_filter")
    @patch("slurm_cli.utils.events.console.print")
    def test_show_no_nodes_matching_filter(
        self, mock_print, mock_is_filter, mock_resolve, mock_exists
    ):
        """Test show prints warning when no nodes match filter."""
        mock_exists.side_effect = mock_exists_with_no_json_flag
        mock_is_filter.return_value = True
        mock_resolve.return_value = None  # No nodes matched

        Event.show(field="Nodes=partition=nonexistent")

        # Should print warning and return early
        mock_print.assert_called()
        call_args = str(mock_print.call_args)
        assert "No nodes found" in call_args

    @patch("slurm_cli.utils.events.subprocess.run")
    @patch("slurm_cli.utils.events.os.path.exists")
    def test_show_with_condflags_open_skips_cache(
        self, mock_exists, mock_run
    ):
        """Test show with CondFlags=Open skips cache."""
        mock_exists.side_effect = mock_exists_with_no_json_flag
        mock_run.return_value = MagicMock(
            stdout=MOCK_EVENTS_DATA, stderr=""
        )

        Event.show(field="CondFlags=Open")

        # Should have called sacctmgr (no cache used)
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "CondFlags=Open" in call_args
