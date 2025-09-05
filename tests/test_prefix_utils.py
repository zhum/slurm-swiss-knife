"""Tests for prefix_utils module."""

import pytest

from slurm_cli.utils.prefix_utils import (
    COMMANDS,
    RESOURCES,
    PrefixMatcher,
    compute_shortest_unique_prefixes,
    generate_bash_command_case,
    generate_bash_resource_case,
    get_all_command_names,
    get_all_resource_names,
    get_cached_command_matcher,
    get_cached_resource_matcher,
    get_resource_help,
)


class TestComputeShortestUniquePrefixes:
    """Tests for compute_shortest_unique_prefixes function."""

    def test_empty_list(self):
        """Test with empty list."""
        result = compute_shortest_unique_prefixes([])
        assert result == {}

    def test_single_item(self):
        """Test with single item."""
        result = compute_shortest_unique_prefixes(["show"])
        assert result == {"show": "s"}

    def test_unique_prefixes(self):
        """Test that prefixes are unique."""
        items = ["show", "create", "delete"]
        result = compute_shortest_unique_prefixes(items)
        # All prefixes should be different
        prefixes = list(result.values())
        assert len(prefixes) == len(set(prefixes))

    def test_conflict_resolution(self):
        """Test that conflicts are resolved with longer prefixes."""
        items = ["show", "suspend"]
        result = compute_shortest_unique_prefixes(items)
        # Both start with 's', so need longer prefixes
        assert result["show"].startswith("sh")
        assert result["suspend"].startswith("su")

    def test_min_length(self):
        """Test minimum prefix length."""
        items = ["a", "b", "c"]
        result = compute_shortest_unique_prefixes(items, min_length=2)
        # Even though single char would be unique, min_length forces 2
        # But items are only 1 char, so full string is used
        assert result == {"a": "a", "b": "b", "c": "c"}

    def test_drain_undrain_conflict(self):
        """Test that drain and undrain have unique prefixes."""
        items = ["drain", "undrain"]
        result = compute_shortest_unique_prefixes(items)
        # These should not conflict
        assert result["drain"] == "d"
        assert result["undrain"] == "u"


class TestPrefixMatcher:
    """Tests for PrefixMatcher class."""

    def test_exact_match(self):
        """Test exact matching."""
        matcher = PrefixMatcher(["show", "create"])
        canonical, exact = matcher.match("show")
        assert canonical == "show"
        assert exact is True

    def test_prefix_match(self):
        """Test prefix matching."""
        matcher = PrefixMatcher(["show", "create"])
        canonical, exact = matcher.match("sh")
        assert canonical == "show"
        assert exact is False

    def test_alias_match(self):
        """Test alias matching."""
        matcher = PrefixMatcher(
            ["show", "create"], aliases={"show": ["get"]}
        )
        canonical, exact = matcher.match("get")
        assert canonical == "show"
        assert exact is True

    def test_no_match(self):
        """Test no match returns input."""
        matcher = PrefixMatcher(["show", "create"])
        canonical, exact = matcher.match("unknown")
        assert canonical == "unknown"
        assert exact is False

    def test_get_shortest_prefix(self):
        """Test getting shortest prefix."""
        matcher = PrefixMatcher(["show", "suspend"])
        assert matcher.get_shortest_prefix("show").startswith("sh")
        assert matcher.get_shortest_prefix("suspend").startswith("su")

    def test_get_all_names(self):
        """Test getting all valid names."""
        matcher = PrefixMatcher(
            ["show", "create"], aliases={"show": ["get"]}
        )
        names = matcher.get_all_names()
        assert "show" in names
        assert "create" in names
        assert "get" in names


class TestCommandsConfig:
    """Tests for COMMANDS configuration."""

    def test_commands_defined(self):
        """Test that main commands are defined."""
        assert "show" in COMMANDS
        assert "create" in COMMANDS
        assert "update" in COMMANDS
        assert "delete" in COMMANDS
        assert "drain" in COMMANDS
        assert "undrain" in COMMANDS

    def test_command_structure(self):
        """Test command structure."""
        for cmd, info in COMMANDS.items():
            assert "aliases" in info
            assert "description" in info
            assert isinstance(info["aliases"], list)

    def test_show_aliases(self):
        """Test show command aliases."""
        assert "get" in COMMANDS["show"]["aliases"]

    def test_undrain_aliases(self):
        """Test undrain command aliases."""
        assert "resume" in COMMANDS["undrain"]["aliases"]


class TestResourcesConfig:
    """Tests for RESOURCES configuration."""

    def test_resources_defined(self):
        """Test that main resources are defined."""
        assert "partitions" in RESOURCES
        assert "nodes" in RESOURCES
        assert "jobs" in RESOURCES
        assert "users" in RESOURCES
        assert "qos" in RESOURCES

    def test_resource_structure(self):
        """Test resource structure."""
        for res, info in RESOURCES.items():
            assert "aliases" in info
            assert isinstance(info["aliases"], list)
            # All resources should have description
            assert "description" in info

    def test_resource_actions(self):
        """Test that major resources have actions defined."""
        # Partitions should have all CRUD actions
        assert "actions" in RESOURCES["partitions"]
        actions = RESOURCES["partitions"]["actions"]
        assert "create" in actions
        assert "update" in actions
        assert "delete" in actions
        assert "show" in actions

    def test_action_structure(self):
        """Test action structure."""
        for res, info in RESOURCES.items():
            if "actions" in info:
                for action, action_info in info["actions"].items():
                    assert "syntax" in action_info
                    assert "options" in action_info
                    assert isinstance(action_info["options"], list)

    def test_partition_aliases(self):
        """Test partition aliases."""
        assert "part" in RESOURCES["partitions"]["aliases"]


class TestGetResourceHelp:
    """Tests for get_resource_help function."""

    def test_get_resource_info(self):
        """Test getting full resource info."""
        info = get_resource_help("partitions")
        assert info is not None
        assert "description" in info
        assert "aliases" in info
        assert "actions" in info

    def test_get_resource_by_alias(self):
        """Test getting resource by alias."""
        info = get_resource_help("part")
        assert info is not None
        assert "description" in info
        assert "Manage Slurm partitions" in info["description"]

    def test_get_action_help(self):
        """Test getting action-specific help."""
        action_help = get_resource_help("partitions", "create")
        assert action_help is not None
        assert "syntax" in action_help
        assert "examples" in action_help
        assert "options" in action_help

    def test_get_action_by_alias(self):
        """Test getting action help via alias."""
        action_help = get_resource_help("part", "show")
        assert action_help is not None
        assert "slurm-cli show part" in action_help["syntax"]

    def test_unknown_resource(self):
        """Test with unknown resource."""
        info = get_resource_help("unknownresource")
        assert info is None

    def test_unknown_action(self):
        """Test with unknown action."""
        action_help = get_resource_help("partitions", "unknownaction")
        assert action_help is None

    def test_resource_without_action(self):
        """Test resource that doesn't have the action."""
        # nodes doesn't have create action
        action_help = get_resource_help("nodes", "create")
        assert action_help is None


class TestCommandMatcher:
    """Tests for command matcher."""

    def test_cached_matcher(self):
        """Test cached matcher returns same instance."""
        m1 = get_cached_command_matcher()
        m2 = get_cached_command_matcher()
        assert m1 is m2

    def test_show_matching(self):
        """Test show command matching."""
        matcher = get_cached_command_matcher()
        canonical, _ = matcher.match("show")
        assert canonical == "show"
        canonical, _ = matcher.match("sh")
        assert canonical == "show"
        canonical, _ = matcher.match("get")
        assert canonical == "show"

    def test_drain_matching(self):
        """Test drain command matching."""
        matcher = get_cached_command_matcher()
        canonical, _ = matcher.match("drain")
        assert canonical == "drain"
        canonical, _ = matcher.match("dr")
        assert canonical == "drain"

    def test_undrain_matching(self):
        """Test undrain command matching."""
        matcher = get_cached_command_matcher()
        canonical, _ = matcher.match("undrain")
        assert canonical == "undrain"
        canonical, _ = matcher.match("und")
        assert canonical == "undrain"
        canonical, _ = matcher.match("resume")
        assert canonical == "undrain"


class TestResourceMatcher:
    """Tests for resource matcher."""

    def test_cached_matcher(self):
        """Test cached matcher returns same instance."""
        m1 = get_cached_resource_matcher()
        m2 = get_cached_resource_matcher()
        assert m1 is m2

    def test_partitions_matching(self):
        """Test partitions resource matching."""
        matcher = get_cached_resource_matcher()
        canonical, _ = matcher.match("partitions")
        assert canonical == "partitions"
        canonical, _ = matcher.match("part")
        assert canonical == "partitions"

    def test_nodes_matching(self):
        """Test nodes resource matching."""
        matcher = get_cached_resource_matcher()
        canonical, _ = matcher.match("nodes")
        assert canonical == "nodes"
        canonical, _ = matcher.match("node")
        assert canonical == "nodes"


class TestBashGeneration:
    """Tests for bash script generation."""

    def test_command_case_generated(self):
        """Test command case patterns are generated."""
        result = generate_bash_command_case()
        assert "show" in result
        assert "drain" in result
        assert "undrain" in result
        # Should have case syntax
        assert "guessed=" in result
        assert "cmd=" in result

    def test_resource_case_generated(self):
        """Test resource case patterns are generated."""
        result = generate_bash_resource_case()
        assert "partitions" in result
        assert "nodes" in result
        # Should have case syntax
        assert "guessed=" in result

    def test_all_command_names(self):
        """Test all command names are returned."""
        result = get_all_command_names()
        assert "show" in result
        assert "get" in result  # alias
        assert "drain" in result
        assert "undrain" in result
        assert "resume" in result  # alias

    def test_all_resource_names(self):
        """Test all resource names are returned."""
        result = get_all_resource_names()
        assert "partitions" in result
        assert "part" in result  # alias
        assert "nodes" in result
        assert "node" in result  # alias


class TestResourcesEpilog:
    """Tests for resources epilog generation."""

    def test_epilog_all_resources(self):
        """Test epilog without action filter includes all resources."""
        from slurm_cli.utils.prefix_utils import get_resources_epilog

        result = get_resources_epilog()
        assert "Available resources:" in result
        assert "partitions" in result
        assert "nodes" in result
        assert "jobs" in result

    def test_epilog_show_action(self):
        """Test epilog for show action includes appropriate resources."""
        from slurm_cli.utils.prefix_utils import get_resources_epilog

        result = get_resources_epilog("show")
        assert "Available resources:" in result
        assert "jobs" in result  # jobs have show action
        assert "nodes" in result  # nodes have show action

    def test_epilog_create_action(self):
        """Test epilog for create action excludes resources without create."""
        from slurm_cli.utils.prefix_utils import get_resources_epilog

        result = get_resources_epilog("create")
        assert "Available resources:" in result
        assert "users" in result  # users have create
        # jobs don't have create action, so should not be listed
        assert "jobs (job, j)" not in result

    def test_epilog_delete_action(self):
        """Test epilog for delete action excludes resources without delete."""
        from slurm_cli.utils.prefix_utils import get_resources_epilog

        result = get_resources_epilog("delete")
        assert "Available resources:" in result
        assert "users" in result  # users have delete
        # associations don't have delete action
        assert "associations (assoc)" not in result

    def test_epilog_includes_aliases(self):
        """Test epilog includes resource aliases."""
        from slurm_cli.utils.prefix_utils import get_resources_epilog

        result = get_resources_epilog()
        # Should include aliases in parentheses
        assert "(acc, account)" in result or "(account, acc)" in result
        assert "(part, parts)" in result or "(parts, part)" in result
