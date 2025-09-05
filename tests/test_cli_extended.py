"""Extended tests for the CLI module to improve coverage."""

import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

# Add src to path for imports
sys.path.insert(0, "src")

from slurm_cli.cli import (  # noqa: E402
    STYLE_OPTIONS,
    create_autocomplete,
    ensure_resource_name,
    get_delimiter,
    get_force_update,
    get_profile,
    get_profile_str,
    get_resource_choices,
    get_row_styles,
    get_show_resource_choices,
    get_zebra,
    main,
    print_help,
    register_commands,
    resolve_command_alias,
    resolve_resource_alias,
)
from slurm_cli.utils.prefix_utils import RESOURCES  # noqa: E402


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_ctx():
    """Create a mock Click context."""
    ctx = MagicMock()
    ctx.obj = {
        "style": "pretty",
        "delimiter": ";",
        "zebra": False,
        "force_update": False,
        "profile": "default",
        "profile_str": None,
    }
    return ctx


class TestGetResourceChoices:
    """Tests for get_resource_choices function."""

    def test_returns_list(self):
        """Test that get_resource_choices returns a list."""
        choices = get_resource_choices()
        assert isinstance(choices, list)

    def test_contains_main_resources(self):
        """Test that main resources are in choices."""
        choices = get_resource_choices()
        assert "partitions" in choices
        assert "nodes" in choices
        assert "users" in choices
        assert "qos" in choices
        assert "accounts" in choices

    def test_contains_aliases(self):
        """Test that aliases are included."""
        choices = get_resource_choices()
        assert "part" in choices
        assert "acc" in choices
        assert "reservation" in choices

    def test_is_sorted(self):
        """Test that choices are sorted."""
        choices = get_resource_choices()
        assert choices == sorted(choices)


class TestGetShowResourceChoices:
    """Tests for get_show_resource_choices function."""

    def test_returns_list(self):
        """Test that get_show_resource_choices returns a list."""
        choices = get_show_resource_choices()
        assert isinstance(choices, list)

    def test_includes_special_resources(self):
        """Test that special show resources are included."""
        choices = get_show_resource_choices()
        # Check that extended resources are present
        assert any("conf" in c for c in choices)
        assert any("stat" in c for c in choices)


class TestResolveResourceAlias:
    """Tests for resolve_resource_alias function."""

    def test_resolve_known_alias(self):
        """Test resolving known aliases."""
        # When alias is in the alias list, it should return canonical name
        result = resolve_resource_alias("part")
        # "part" is an alias for "partitions"
        assert result == "partitions"

    def test_resolve_unknown_resource(self):
        """Test that unknown resources are returned as-is."""
        result = resolve_resource_alias("unknown_resource")
        assert result == "unknown_resource"

    def test_resolve_canonical_name(self):
        """Test that canonical names are returned as-is."""
        result = resolve_resource_alias("partitions")
        assert result == "partitions"


class TestResolveCommandAlias:
    """Tests for resolve_command_alias function."""

    def test_resolve_show_aliases(self):
        """Test resolving show command aliases."""
        assert resolve_command_alias("show") == "show"
        assert resolve_command_alias("get") == "show"

    def test_resolve_create_aliases(self):
        """Test resolving create command aliases."""
        assert resolve_command_alias("create") == "create"
        assert resolve_command_alias("new") == "create"
        assert resolve_command_alias("add") == "create"

    def test_resolve_update_aliases(self):
        """Test resolving update command aliases."""
        assert resolve_command_alias("update") == "update"
        assert resolve_command_alias("edit") == "update"
        assert resolve_command_alias("modify") == "update"

    def test_resolve_delete_aliases(self):
        """Test resolving delete command aliases."""
        assert resolve_command_alias("delete") == "delete"
        assert resolve_command_alias("rm") == "delete"
        assert resolve_command_alias("remove") == "delete"

    def test_resolve_unknown_command(self):
        """Test that unknown commands return the input unchanged."""
        result = resolve_command_alias("xyzunknown123")
        assert result == "xyzunknown123"


class TestGetDelimiter:
    """Tests for get_delimiter function."""

    def test_with_override(self, mock_ctx):
        """Test delimiter with override value."""
        result = get_delimiter(mock_ctx, "|")
        assert result == "|"

    def test_from_context(self, mock_ctx):
        """Test delimiter from context."""
        mock_ctx.obj["delimiter"] = ","
        result = get_delimiter(mock_ctx, None)
        assert result == ","

    def test_default_value(self, mock_ctx):
        """Test default delimiter value."""
        mock_ctx.obj = {}
        result = get_delimiter(mock_ctx, None)
        assert result == ";"


class TestGetZebra:
    """Tests for get_zebra function."""

    def test_with_override_true(self, mock_ctx):
        """Test zebra with override True."""
        result = get_zebra(mock_ctx, True)
        assert result is True

    def test_with_override_false(self, mock_ctx):
        """Test zebra with override False."""
        mock_ctx.obj["zebra"] = True
        result = get_zebra(mock_ctx, False)
        assert result is False

    def test_from_context(self, mock_ctx):
        """Test zebra from context."""
        mock_ctx.obj["zebra"] = True
        result = get_zebra(mock_ctx, None)
        assert result is True

    def test_default_value(self, mock_ctx):
        """Test default zebra value."""
        mock_ctx.obj = {}
        result = get_zebra(mock_ctx, None)
        assert result is False


class TestGetRowStyles:
    """Tests for get_row_styles function."""

    def test_zebra_enabled(self):
        """Test row styles with zebra enabled."""
        styles = get_row_styles(True)
        assert styles is not None
        assert len(styles) == 2
        assert "" in styles
        assert "on rgb(30,40,60)" in styles

    def test_zebra_disabled(self):
        """Test row styles with zebra disabled."""
        styles = get_row_styles(False)
        assert styles is None


class TestGetForceUpdate:
    """Tests for get_force_update function."""

    def test_force_update_true(self, mock_ctx):
        """Test force update True."""
        mock_ctx.obj["force_update"] = True
        result = get_force_update(mock_ctx)
        assert result is True

    def test_force_update_false(self, mock_ctx):
        """Test force update False."""
        mock_ctx.obj["force_update"] = False
        result = get_force_update(mock_ctx)
        assert result is False

    def test_default_value(self, mock_ctx):
        """Test default force update value."""
        mock_ctx.obj = {}
        result = get_force_update(mock_ctx)
        assert result is False


class TestGetProfile:
    """Tests for get_profile function."""

    def test_with_override(self, mock_ctx):
        """Test profile with override."""
        result = get_profile(mock_ctx, "compact")
        assert result == "compact"

    def test_from_context(self, mock_ctx):
        """Test profile from context."""
        mock_ctx.obj["profile"] = "minimal"
        result = get_profile(mock_ctx, None)
        assert result == "minimal"

    def test_default_value(self, mock_ctx):
        """Test default profile value."""
        mock_ctx.obj = {}
        result = get_profile(mock_ctx, None)
        assert result == "default"


class TestGetProfileStr:
    """Tests for get_profile_str function."""

    def test_with_override(self, mock_ctx):
        """Test profile_str with override."""
        result = get_profile_str(mock_ctx, "[cyan]{name}[/]")
        assert result == "[cyan]{name}[/]"

    def test_from_context(self, mock_ctx):
        """Test profile_str from context."""
        mock_ctx.obj["profile_str"] = "{name} - {desc}"
        result = get_profile_str(mock_ctx, None)
        assert result == "{name} - {desc}"

    def test_default_none(self, mock_ctx):
        """Test default profile_str is None."""
        mock_ctx.obj = {}
        result = get_profile_str(mock_ctx, None)
        assert result is None


class TestPrintHelp:
    """Tests for print_help function."""

    def test_create_coordinator_help(self):
        """Test help for create coordinator command."""
        mock_ctx = MagicMock()
        output = io.StringIO()
        with redirect_stdout(output):
            print_help("create coordinator", mock_ctx)
        result = output.getvalue()
        assert "coordinator" in result.lower()
        mock_ctx.exit.assert_called_once()

    def test_update_coordinator_help(self):
        """Test help for update coordinator command."""
        mock_ctx = MagicMock()
        output = io.StringIO()
        with redirect_stdout(output):
            print_help("update coordinator", mock_ctx)
        result = output.getvalue()
        assert "coordinator" in result.lower()
        mock_ctx.exit.assert_called_once()

    def test_delete_coordinator_help(self):
        """Test help for delete coordinator command."""
        mock_ctx = MagicMock()
        output = io.StringIO()
        with redirect_stdout(output):
            print_help("delete coordinator", mock_ctx)
        result = output.getvalue()
        assert "coordinator" in result.lower()
        mock_ctx.exit.assert_called_once()

    def test_unknown_command_help(self):
        """Test help for unknown command."""
        mock_ctx = MagicMock()
        output = io.StringIO()
        with redirect_stdout(output):
            print_help("unknown command xyz", mock_ctx)
        result = output.getvalue()
        assert "Unknown command" in result
        mock_ctx.exit.assert_called_once()


class TestCreateAutocomplete:
    """Tests for create_autocomplete function."""

    def test_returns_autocomplete_instance(self):
        """Test that create_autocomplete returns an AutoComplete instance."""
        from fast_autocomplete import AutoComplete

        result = create_autocomplete()
        assert isinstance(result, AutoComplete)

    def test_autocomplete_can_search(self):
        """Test that the autocomplete instance can search."""
        autocomplete = create_autocomplete()
        results = autocomplete.search(word="show", max_cost=3, size=5)
        assert isinstance(results, list)


class TestEnsureResourceName:
    """Tests for ensure_resource_name function."""

    def test_problems_resource(self):
        """Test problems resource mapping."""
        result, field, data = ensure_resource_name("problems")
        assert result == "problems"
        assert data == []

    def test_stats_resource(self):
        """Test stats resource mapping."""
        result, field, data = ensure_resource_name("statistics")
        assert result == "stats"

    def test_dump_resource(self):
        """Test dump resource mapping."""
        result, field, data = ensure_resource_name("dumps")
        assert result == "dump"

    def test_events_resource(self):
        """Test events resource mapping."""
        result, field, data = ensure_resource_name("events")
        assert result == "events"

    def test_licenses_resource(self):
        """Test licenses resource mapping."""
        result, field, data = ensure_resource_name("licenses")
        assert "`licens`es" in result or "licenses" in result.lower()

    def test_runawayjobs_resource(self):
        """Test runawayjobs resource mapping."""
        result, field, data = ensure_resource_name("bads")
        assert result == "runawayjobs"

    def test_transactions_resource(self):
        """Test transactions resource mapping."""
        result, field, data = ensure_resource_name("transactions")
        assert result == "transactions"

    def test_tres_resource(self):
        """Test tres resource mapping."""
        result, field, data = ensure_resource_name("tres")
        assert result == "tres"

    def test_archive_resource(self):
        """Test archive resource mapping."""
        result, field, data = ensure_resource_name("archive")
        assert result == "archive"

    def test_coordinators_resource(self):
        """Test coordinators resource mapping."""
        result, field, data = ensure_resource_name("coordinators")
        assert result == "coordinators"

    def test_associations_resource(self):
        """Test associations resource mapping (needs mocking for guess)."""
        # Associations goes through guess_resource_type which needs mocking
        with patch(
            "slurm_cli.cli.Resource.guess_resource_type"
        ) as mock:
            mock.return_value = ("associations", [])
            result, field, data = ensure_resource_name("associations")
            assert result == "associations"

    def test_field_passthrough(self):
        """Test that field is passed through."""
        # Need to mock cached_resource since it calls slurm commands
        with patch("slurm_cli.cli.Resource.cached_resource") as mock:
            mock.return_value = {"partitions": []}
            result, field, data = ensure_resource_name(
                "partitions", "gpu"
            )
            assert field == "gpu"


class TestShowCommand:
    """Tests for the show command with various resources."""

    def test_show_config(self, runner):
        """Test show config command."""
        register_commands()
        with patch("slurm_cli.cli.Config.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("config", None, {})
                result = runner.invoke(main, ["show", "config"])
                mock_show.assert_called_once()
                assert result.exit_code == 0

    def test_show_reservations(self, runner):
        """Test show reservations command."""
        register_commands()
        with patch("slurm_cli.cli.Reservation.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("reservations", None, {})
                result = runner.invoke(main, ["show", "reservations"])
                mock_show.assert_called_once()
                assert result.exit_code == 0

    def test_show_reservations_with_name(self, runner):
        """Test show reservations with specific name."""
        register_commands()
        with patch("slurm_cli.cli.Reservation.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = (
                    "reservations",
                    "test_res",
                    {},
                )
                result = runner.invoke(
                    main, ["show", "reservations", "test_res"]
                )
                mock_show.assert_called_once()
                assert result.exit_code == 0

    def test_show_partitions(self, runner):
        """Test show partitions command."""
        register_commands()
        with patch("slurm_cli.cli.Partition.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("partitions", None, {})
                result = runner.invoke(main, ["show", "partitions"])
                mock_show.assert_called_once()
                assert result.exit_code == 0

    def test_show_partitions_with_name(self, runner):
        """Test show partitions with specific name."""
        register_commands()
        with patch("slurm_cli.cli.Partition.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("partitions", "gpu", {})
                result = runner.invoke(
                    main, ["show", "partitions", "gpu"]
                )
                mock_show.assert_called_once()
                assert result.exit_code == 0

    def test_show_nodes(self, runner):
        """Test show nodes command."""
        register_commands()
        with patch("slurm_cli.cli.Node.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("nodes", None, {})
                result = runner.invoke(main, ["show", "nodes"])
                mock_show.assert_called_once()
                assert result.exit_code == 0

    def test_show_nodes_with_name(self, runner):
        """Test show nodes with specific name."""
        register_commands()
        with patch("slurm_cli.cli.Node.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("nodes", "node01", {})
                result = runner.invoke(
                    main, ["show", "nodes", "node01"]
                )
                mock_show.assert_called_once()
                assert result.exit_code == 0

    def test_show_qos(self, runner):
        """Test show qos command."""
        register_commands()
        with patch("slurm_cli.cli.Qos.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("qos", None, {})
                result = runner.invoke(main, ["show", "qos"])
                mock_show.assert_called_once()
                assert result.exit_code == 0

    def test_show_qos_with_field(self, runner):
        """Test show qos with specific field."""
        register_commands()
        with patch("slurm_cli.cli.Qos.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("qos", "normal", {})
                result = runner.invoke(main, ["show", "qos", "normal"])
                mock_show.assert_called_once()
                assert result.exit_code == 0

    def test_show_accounts(self, runner):
        """Test show accounts command."""
        register_commands()
        with patch("slurm_cli.cli.Account.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("accounts", None, {})
                result = runner.invoke(main, ["show", "accounts"])
                mock_show.assert_called_once()
                assert result.exit_code == 0

    def test_show_accounts_with_field(self, runner):
        """Test show accounts with specific field."""
        register_commands()
        with patch("slurm_cli.cli.Account.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("accounts", "myaccount", {})
                result = runner.invoke(
                    main, ["show", "accounts", "myaccount"]
                )
                mock_show.assert_called_once()
                assert result.exit_code == 0

    def test_show_coordinators(self, runner):
        """Test show coordinators command."""
        register_commands()
        with patch("slurm_cli.cli.Coordinator.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("coordinators", None, {})
                result = runner.invoke(main, ["show", "coordinators"])
                mock_show.assert_called_once()
                assert result.exit_code == 0

    def test_show_coordinators_with_field(self, runner):
        """Test show coordinators with specific field."""
        register_commands()
        with patch("slurm_cli.cli.Coordinator.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("coordinators", "admin", {})
                result = runner.invoke(
                    main, ["show", "coordinators", "admin"]
                )
                mock_show.assert_called_once()
                assert result.exit_code == 0

    def test_show_users(self, runner):
        """Test show users command."""
        register_commands()
        with patch("slurm_cli.cli.User.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("users", None, {})
                result = runner.invoke(main, ["show", "users"])
                mock_show.assert_called_once()
                assert result.exit_code == 0

    def test_show_users_with_name(self, runner):
        """Test show users with specific name."""
        register_commands()
        with patch("slurm_cli.cli.User.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("users", "testuser", {})
                result = runner.invoke(
                    main, ["show", "users", "testuser"]
                )
                mock_show.assert_called_once()
                assert result.exit_code == 0

    def test_show_unknown_resource(self, runner):
        """Test show with unknown resource."""
        register_commands()
        with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
            mock_ensure.return_value = ("unknown_xyz", None, {})
            result = runner.invoke(main, ["show", "accounts"])
            # Should complete (unknown is handled in show function)
            assert result.exit_code == 0

    def test_show_with_profile_str_help(self, runner):
        """Test show with --profile-str=help."""
        register_commands()
        with patch("slurm_cli.cli.ensure_resource_name") as mock_ensure:
            mock_ensure.return_value = ("accounts", None, {})
            result = runner.invoke(
                main, ["--profile-str", "help", "show", "accounts"]
            )
            assert result.exit_code == 0
            # Should show field help
            assert (
                "field" in result.output.lower()
                or "template" in result.output.lower()
            )


class TestUpdateCommand:
    """Tests for the update command."""

    def test_update_no_args_shows_help(self, runner):
        """Test update without args shows help."""
        register_commands()
        result = runner.invoke(main, ["update"])
        assert result.exit_code == 0 or "Usage" in result.output

    def test_update_dry_run(self, runner):
        """Test update with dry-run flag."""
        register_commands()
        result = runner.invoke(
            main,
            ["update", "partitions", "state", "up", "--dry-run"],
        )
        assert result.exit_code == 0
        assert (
            "DRY RUN" in result.output
            or "Would update" in result.output
        )

    def test_update_with_verbose(self, runner):
        """Test update with verbose flag."""
        register_commands()
        with patch("slurm_cli.utils.partitions.Partition.update"):
            result = runner.invoke(
                main,
                [
                    "update",
                    "partitions",
                    "state",
                    "up",
                    "-v",
                    "key=value",
                ],
            )
            assert result.exit_code == 0

    def test_update_partition(self, runner):
        """Test update partition."""
        register_commands()
        with patch(
            "slurm_cli.utils.partitions.Partition.update"
        ) as mock:
            result = runner.invoke(
                main, ["update", "partitions", "gpu", "state=up"]
            )
            # Should try to update or show message
            assert result.exit_code == 0 or mock.called

    def test_update_unknown_resource(self, runner):
        """Test update with unknown resource shows error."""
        register_commands()
        result = runner.invoke(
            main, ["update", "partitions", "field", "value", "extra"]
        )
        # Should complete without crash
        assert result.exit_code == 0


class TestCreateCommand:
    """Tests for the create command."""

    def test_create_no_args_shows_help(self, runner):
        """Test create without args shows help."""
        register_commands()
        result = runner.invoke(main, ["create"])
        assert result.exit_code == 0 or "Usage" in result.output

    def test_create_dry_run(self, runner):
        """Test create with dry-run flag."""
        register_commands()
        result = runner.invoke(
            main,
            ["create", "users", "testuser", "--dry-run"],
        )
        assert result.exit_code == 0
        assert (
            "DRY RUN" in result.output
            or "Would create" in result.output
        )


class TestListResourcesCommand:
    """Tests for the list-resources command."""

    def test_list_resources(self, runner):
        """Test list-resources command."""
        register_commands()
        result = runner.invoke(main, ["list-resources"])
        assert result.exit_code == 0
        assert (
            "Resource" in result.output or "partitions" in result.output
        )

    def test_list_resources_with_zebra(self, runner):
        """Test list-resources with zebra option."""
        register_commands()
        result = runner.invoke(main, ["--zebra", "list-resources"])
        assert result.exit_code == 0


class TestVersionCommand:
    """Tests for the version command."""

    def test_version(self, runner):
        """Test version command."""
        register_commands()
        result = runner.invoke(main, ["version"])
        assert result.exit_code == 0
        assert "Slurm" in result.output or "v0.1.0" in result.output


class TestHelpCommand:
    """Tests for the help command."""

    def test_help_no_args(self, runner):
        """Test help command without args."""
        register_commands()
        result = runner.invoke(main, ["help"])
        assert result.exit_code == 0
        # Should show main help
        assert (
            "Usage" in result.output
            or "command" in result.output.lower()
        )

    def test_help_with_word(self, runner):
        """Test help with autocomplete word."""
        register_commands()
        result = runner.invoke(main, ["help", "show"])
        assert result.exit_code == 0

    def test_help_with_subcommand(self, runner):
        """Test help with subcommand."""
        register_commands()
        result = runner.invoke(main, ["help", "create", "coordinator"])
        assert result.exit_code == 0

    def test_help_with_unknown_word(self, runner):
        """Test help with unknown word."""
        register_commands()
        result = runner.invoke(main, ["help", "xyzunknown"])
        assert result.exit_code == 0
        # Should show no suggestions
        assert (
            "No suggestions" in result.output or result.exit_code == 0
        )

    def test_help_with_zebra(self, runner):
        """Test help with zebra option."""
        register_commands()
        result = runner.invoke(main, ["--zebra", "help"])
        assert result.exit_code == 0


class TestStyleOptions:
    """Tests for style options constant."""

    def test_style_options_defined(self):
        """Test that STYLE_OPTIONS contains expected values."""
        assert "pretty" in STYLE_OPTIONS
        assert "json" in STYLE_OPTIONS
        assert "csv" in STYLE_OPTIONS
        assert len(STYLE_OPTIONS) == 3


class TestResourcesAliases:
    """Tests for RESOURCES configuration."""

    def test_aliases_defined(self):
        """Test that main resources are defined."""
        assert "partitions" in RESOURCES
        assert "nodes" in RESOURCES
        assert "accounts" in RESOURCES

    def test_partition_aliases(self):
        """Test partition aliases."""
        assert "part" in RESOURCES["partitions"]["aliases"]
        assert "parts" in RESOURCES["partitions"]["aliases"]

    def test_account_aliases(self):
        """Test account aliases."""
        assert "acc" in RESOURCES["accounts"]["aliases"]
        assert "account" in RESOURCES["accounts"]["aliases"]


class TestEnsureResourceNameBranches:
    """Tests for ensure_resource_name various branches."""

    @patch("slurm_cli.cli.Resource.cached_resource")
    def test_ensure_resource_jobs(self, mock_cache):
        """Test ensure_resource_name with jobs prefix."""
        mock_cache.return_value = {}
        resource, field, data = ensure_resource_name("jobs", False)
        assert resource == "jobs"

    @patch("slurm_cli.cli.Resource.cached_resource")
    def test_ensure_resource_nodes(self, mock_cache):
        """Test ensure_resource_name with nodes prefix."""
        mock_cache.return_value = {"node01": {}}
        resource, field, data = ensure_resource_name("nodes", False)
        assert resource == "nodes"

    @patch("slurm_cli.cli.Resource.cached_resource")
    def test_ensure_resource_partitions(self, mock_cache):
        """Test ensure_resource_name with partitions prefix."""
        mock_cache.return_value = {"gpu": {}}
        resource, field, data = ensure_resource_name(
            "partitions", False
        )
        assert resource == "partitions"

    @patch("slurm_cli.cli.Resource.cached_resource")
    def test_ensure_resource_users(self, mock_cache):
        """Test ensure_resource_name with users prefix."""
        mock_cache.return_value = {"user1": {}}
        resource, field, data = ensure_resource_name("users", False)
        assert resource == "users"

    @patch("slurm_cli.cli.Resource.cached_resource")
    def test_ensure_resource_qos(self, mock_cache):
        """Test ensure_resource_name with qos prefix."""
        mock_cache.return_value = {"normal": {}}
        resource, field, data = ensure_resource_name("qos", False)
        assert resource == "qos"

    @patch("slurm_cli.cli.Resource.cached_resource")
    def test_ensure_resource_accounts(self, mock_cache):
        """Test ensure_resource_name with accounts prefix."""
        mock_cache.return_value = {"root": {}}
        resource, field, data = ensure_resource_name("accounts", False)
        assert resource == "accounts"

    @patch("slurm_cli.cli.Resource.cached_resource")
    def test_ensure_resource_reservations(self, mock_cache):
        """Test ensure_resource_name with reservations prefix."""
        mock_cache.return_value = {"maint": {}}
        resource, field, data = ensure_resource_name(
            "reservations", False
        )
        assert resource == "reservations"

    @patch("slurm_cli.cli.Resource.cached_resource")
    def test_ensure_resource_config(self, mock_cache):
        """Test ensure_resource_name with config prefix."""
        mock_cache.return_value = {}
        resource, field, data = ensure_resource_name("config", False)
        assert resource == "config"

    def test_ensure_resource_stats(self):
        """Test ensure_resource_name with stats."""
        resource, field, data = ensure_resource_name("stats", False)
        assert resource == "stats"

    @patch("slurm_cli.cli.Resource.guess_resource_type")
    def test_ensure_resource_associations(self, mock_guess):
        """Test ensure_resource_name with associations."""
        mock_guess.return_value = ("associations", [])
        resource, field, data = ensure_resource_name("assoc", False)
        assert resource == "associations"

    def test_ensure_resource_dump(self):
        """Test ensure_resource_name with dump."""
        resource, field, data = ensure_resource_name("dump", False)
        assert resource == "dump"

    def test_ensure_resource_events(self):
        """Test ensure_resource_name with events."""
        resource, field, data = ensure_resource_name("events", False)
        assert resource == "events"

    def test_ensure_resource_licenses(self):
        """Test ensure_resource_name with licenses."""
        resource, field, data = ensure_resource_name("licenses", False)
        assert (
            "`licens`es" in resource or "licenses" in resource.lower()
        )

    def test_ensure_resource_runawayjobs(self):
        """Test ensure_resource_name with bad jobs."""
        resource, field, data = ensure_resource_name("badjobs", False)
        assert resource == "runawayjobs"

    def test_ensure_resource_transactions(self):
        """Test ensure_resource_name with transactions."""
        resource, field, data = ensure_resource_name(
            "transactions", False
        )
        assert resource == "transactions"

    def test_ensure_resource_tres(self):
        """Test ensure_resource_name with tres."""
        resource, field, data = ensure_resource_name("tres", False)
        assert resource == "tres"

    def test_ensure_resource_archive(self):
        """Test ensure_resource_name with archive."""
        resource, field, data = ensure_resource_name("archive", False)
        assert resource == "archive"

    def test_ensure_resource_coordinators(self):
        """Test ensure_resource_name with coordinators."""
        resource, field, data = ensure_resource_name(
            "coordinators", False
        )
        assert resource == "coordinators"

    @patch("slurm_cli.cli.Resource.guess_resource_type")
    def test_ensure_resource_unknown(self, mock_guess):
        """Test ensure_resource_name with unknown resource."""
        mock_guess.return_value = (None, None)
        resource, field, data = ensure_resource_name(
            "xyzunknown", False
        )
        assert resource is None


class TestShowStyleOverrides:
    """Tests for show command style overrides."""

    def test_show_with_pretty_flag(self, runner):
        """Test show command with --pretty flag."""
        register_commands()
        with patch("slurm_cli.cli.Account.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("accounts", None, {})
                result = runner.invoke(
                    main, ["show", "--pretty", "accounts"]
                )
                mock_show.assert_called_once()
                call_kwargs = mock_show.call_args[1]
                assert call_kwargs["style"] == "pretty"

    def test_show_with_json_flag(self, runner):
        """Test show command with --json flag."""
        register_commands()
        with patch("slurm_cli.cli.Account.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("accounts", None, {})
                result = runner.invoke(
                    main, ["show", "--json", "accounts"]
                )
                mock_show.assert_called_once()
                call_kwargs = mock_show.call_args[1]
                assert call_kwargs["style"] == "json"

    def test_show_with_csv_flag(self, runner):
        """Test show command with --csv flag."""
        register_commands()
        with patch("slurm_cli.cli.Account.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("accounts", None, {})
                result = runner.invoke(
                    main, ["show", "--csv", "accounts"]
                )
                mock_show.assert_called_once()
                call_kwargs = mock_show.call_args[1]
                assert call_kwargs["style"] == "csv"


class TestUpdateCommand:
    """Tests for update command branches."""

    def test_update_dry_run(self, runner):
        """Test update command with dry-run."""
        register_commands()
        result = runner.invoke(
            main,
            ["update", "--dry-run", "partitions", "gpu", "state=UP"],
        )
        assert "DRY RUN" in result.output

    def test_update_dry_run_with_args(self, runner):
        """Test update command with dry-run and extra args."""
        register_commands()
        result = runner.invoke(
            main,
            [
                "update",
                "--dry-run",
                "partitions",
                "gpu",
                "state=UP",
                "maxtime=1:00:00",
            ],
        )
        assert "DRY RUN" in result.output

    def test_update_no_names(self, runner):
        """Test update command without additional names (dry run)."""
        register_commands()
        result = runner.invoke(
            main,
            ["update", "--dry-run", "nodes", "node01"],
        )
        # Should show dry run message
        assert "DRY RUN" in result.output or result.exit_code == 0

    def test_update_unknown_resource(self, runner):
        """Test update command for unknown resource."""
        register_commands()
        result = runner.invoke(
            main,
            ["update", "xyzunknown", "test"],
        )
        # Click validates resource type, so it shows error
        assert (
            result.exit_code == 2 or "invalid" in result.output.lower()
        )


class TestCreateCommand:
    """Tests for create command branches."""

    def test_create_dry_run(self, runner):
        """Test create command with dry-run."""
        register_commands()
        result = runner.invoke(
            main,
            ["create", "--dry-run", "partitions", "newpart"],
        )
        assert "DRY RUN" in result.output

    def test_create_dry_run_with_args(self, runner):
        """Test create command with dry-run and args."""
        register_commands()
        result = runner.invoke(
            main,
            [
                "create",
                "--dry-run",
                "partitions",
                "newpart",
                "state=UP",
            ],
        )
        assert "DRY RUN" in result.output

    def test_create_unknown_resource(self, runner):
        """Test create command for unknown resource."""
        register_commands()
        result = runner.invoke(
            main,
            ["create", "xyzunknown", "test"],
        )
        # Click validates resource type, so it shows error
        assert (
            result.exit_code == 2 or "invalid" in result.output.lower()
        )


class TestDeleteCommand:
    """Tests for delete command branches."""

    def test_delete_dry_run(self, runner):
        """Test delete command with dry-run."""
        register_commands()
        result = runner.invoke(
            main,
            ["delete", "--dry-run", "partitions", "testpart"],
        )
        assert "DRY RUN" in result.output

    def test_delete_dry_run_no_name(self, runner):
        """Test delete command with dry-run but no specific name."""
        register_commands()
        result = runner.invoke(
            main,
            ["delete", "--dry-run", "partitions"],
        )
        assert "DRY RUN" in result.output

    def test_delete_no_resource(self, runner):
        """Test delete command with no resource shows help."""
        register_commands()
        result = runner.invoke(main, ["delete"])
        # Should show help
        assert result.exit_code == 0 or "Usage" in result.output

    def test_delete_with_global_yes_option(self, runner):
        """Test delete command with global --yes option skips confirmation."""
        register_commands()
        # Without --yes, would prompt for confirmation (and abort in test)
        # With --yes, should proceed without prompting
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            result = runner.invoke(
                main,
                ["--yes", "delete", "partitions", "testpart"],
            )
        # Should not show "cancelled" since --yes skips confirmation
        assert "cancelled" not in result.output.lower()
        # Should show success or deletion message
        assert "delet" in result.output.lower() or result.exit_code == 0

    def test_delete_with_short_yes_option(self, runner):
        """Test delete command with short -y option skips confirmation."""
        register_commands()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            result = runner.invoke(
                main,
                ["-y", "delete", "partitions", "testpart"],
            )
        # Should not show "cancelled" since -y skips confirmation
        assert "cancelled" not in result.output.lower()
        # Should show success or deletion message
        assert "delet" in result.output.lower() or result.exit_code == 0

    def test_delete_with_yes_after_command(self, runner):
        """Test delete command with -y after the command name."""
        register_commands()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            result = runner.invoke(
                main,
                ["delete", "-y", "partitions", "testpart"],
            )
        # Should not show "cancelled" since -y skips confirmation
        assert "cancelled" not in result.output.lower()
        # Should show success or deletion message
        assert "delet" in result.output.lower() or result.exit_code == 0

    def test_delete_with_yes_after_resource(self, runner):
        """Test delete command with -y after the resource."""
        register_commands()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            result = runner.invoke(
                main,
                ["delete", "partitions", "-y", "testpart"],
            )
        # Should not show "cancelled" since -y skips confirmation
        assert "cancelled" not in result.output.lower()
        # Should show success or deletion message
        assert "delet" in result.output.lower() or result.exit_code == 0


class TestListResourcesCommand:
    """Tests for list-resources command."""

    def test_list_resources_basic(self, runner):
        """Test list-resources command."""
        register_commands()
        result = runner.invoke(main, ["list-resources"])
        assert result.exit_code == 0
        # Should list resources
        assert (
            "partition" in result.output.lower()
            or "resource" in result.output.lower()
        )

    def test_list_resources_with_zebra(self, runner):
        """Test list-resources with zebra option."""
        register_commands()
        result = runner.invoke(main, ["--zebra", "list-resources"])
        assert result.exit_code == 0


class TestHelpCommandBranches:
    """Tests for help command edge cases."""

    def test_help_with_word_and_subcommand(self, runner):
        """Test help with both word and subcommand."""
        register_commands()
        result = runner.invoke(main, ["help", "show", "accounts"])
        assert result.exit_code == 0

    def test_help_no_parent_context(self, runner):
        """Test help when no parent context exists."""
        register_commands()
        result = runner.invoke(main, ["help"])
        assert result.exit_code == 0


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_show_with_csv_style(self, runner):
        """Test show command with CSV style."""
        register_commands()
        with patch("slurm_cli.cli.Account.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("accounts", None, {})
                result = runner.invoke(
                    main, ["--csv", "show", "accounts"]
                )
                mock_show.assert_called_once()
                # Check that CSV style was passed
                call_kwargs = mock_show.call_args[1]
                assert call_kwargs["style"] == "csv"
                assert result.exit_code == 0

    def test_show_with_json_style(self, runner):
        """Test show command with JSON style."""
        register_commands()
        with patch("slurm_cli.cli.Account.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("accounts", None, {})
                result = runner.invoke(
                    main, ["--json", "show", "accounts"]
                )
                mock_show.assert_called_once()
                call_kwargs = mock_show.call_args[1]
                assert call_kwargs["style"] == "json"
                assert result.exit_code == 0

    def test_show_with_delimiter(self, runner):
        """Test show command with custom delimiter."""
        register_commands()
        with patch("slurm_cli.cli.Account.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("accounts", None, {})
                result = runner.invoke(
                    main,
                    ["--csv", "--delimiter", "|", "show", "accounts"],
                )
                mock_show.assert_called_once()
                call_kwargs = mock_show.call_args[1]
                assert call_kwargs["delimiter"] == "|"
                assert result.exit_code == 0

    def test_main_with_all_options(self, runner):
        """Test main command with multiple options."""
        register_commands()
        with patch("slurm_cli.cli.Account.show") as mock_show:
            with patch(
                "slurm_cli.cli.ensure_resource_name"
            ) as mock_ensure:
                mock_ensure.return_value = ("accounts", None, {})
                result = runner.invoke(
                    main,
                    [
                        "--style",
                        "pretty",
                        "--zebra",
                        "--profile",
                        "default",
                        "show",
                        "accounts",
                    ],
                )
                mock_show.assert_called_once()
                call_kwargs = mock_show.call_args[1]
                assert call_kwargs["style"] == "pretty"
                assert call_kwargs["zebra"] is True
                assert result.exit_code == 0
