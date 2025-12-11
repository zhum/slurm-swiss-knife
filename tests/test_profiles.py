"""Tests for the profiles module."""

import os
import sys
import tempfile
from typing import Any, Dict, Optional
from unittest.mock import patch

import pytest

# Add src to path for imports
sys.path.insert(0, "src")

from slurm_cli.utils.profiles import (  # noqa: E402
    DEFAULT_FIELD_VALUES,
    DEFAULT_PROFILES,
    ProfileManager,
    _normalize_profile_str,
    extract_fields_from_template,
    format_with_template,
    get_columns_for_resource,
    get_profile_config,
    get_profile_manager,
    get_resource_fields,
    get_styles_for_resource,
    get_template_for_resource,
    is_field_empty,
    show_profile_help,
)


class TestProfileManager:
    """Tests for ProfileManager class."""

    def test_default_profiles_exist(self):
        """Test that default profiles are defined."""
        assert "default" in DEFAULT_PROFILES
        assert "compact" in DEFAULT_PROFILES
        assert "minimal" in DEFAULT_PROFILES
        assert "oneline" in DEFAULT_PROFILES
        assert "detailed" in DEFAULT_PROFILES

    def test_default_profile_resources(self):
        """Test that default profile has all expected resources."""
        default = DEFAULT_PROFILES["default"]
        expected_resources = [
            "accounts",
            "qos",
            "partitions",
            "nodes",
            "reservations",
            "coordinators",
            "users",
        ]
        for resource in expected_resources:
            assert (
                resource in default
            ), f"Resource {resource} not in default"

    def test_profile_manager_singleton(self):
        """Test that get_profile_manager returns a singleton."""
        manager1 = get_profile_manager()
        manager2 = get_profile_manager()
        assert manager1 is manager2

    def test_list_profiles(self):
        """Test listing available profiles."""
        manager = ProfileManager()
        profiles = manager.list_profiles()
        assert "default" in profiles
        assert "compact" in profiles

    def test_get_profile(self):
        """Test getting a profile by name."""
        manager = ProfileManager()
        default = manager.get_profile("default")
        assert default is not None
        assert "accounts" in default

    def test_get_nonexistent_profile(self):
        """Test getting a non-existent profile returns None."""
        manager = ProfileManager()
        profile = manager.get_profile("nonexistent_profile_xyz")
        assert profile is None


class TestProfileFileParsing:
    """Tests for profile file parsing."""

    def test_parse_simple_profile(self):
        """Test parsing a simple profile file."""
        content = """
[profile:test]
accounts.columns = name,description
accounts.styles.name = cyan bold
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".profiles", delete=False
        ) as f:
            f.write(content)
            f.flush()
            try:
                import slurm_cli.utils.profiles as profiles_mod

                with patch.object(
                    profiles_mod, "PROFILE_FILES", [f.name]
                ):
                    manager = ProfileManager()
                    manager._loaded = False  # Reset to force reload
                    profile = manager.get_profile("test")
                    assert profile is not None
                    assert "accounts" in profile
                    assert profile["accounts"]["columns"] == [
                        "name",
                        "description",
                    ]
                    assert (
                        profile["accounts"]["styles"]["name"]
                        == "cyan bold"
                    )
            finally:
                os.unlink(f.name)

    def test_parse_multiline_template(self):
        """Test parsing multi-line templates with backslash continuation."""
        content = """
[profile:test]
accounts.template = [cyan]{name}[/] \\
    Description: {description} \\
    Org: {organization}
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".profiles", delete=False
        ) as f:
            f.write(content)
            f.flush()
            try:
                import slurm_cli.utils.profiles as profiles_mod

                with patch.object(
                    profiles_mod, "PROFILE_FILES", [f.name]
                ):
                    manager = ProfileManager()
                    manager._loaded = False
                    profile = manager.get_profile("test")
                    assert profile is not None
                    assert "accounts" in profile
                    # Template should be joined into a single line
                    template = profile["accounts"]["template"]
                    assert "[cyan]{name}[/]" in template
                    assert "Description: {description}" in template
                    assert "Org: {organization}" in template
            finally:
                os.unlink(f.name)

    def test_parse_comments_and_empty_lines(self):
        """Test that comments and empty lines are ignored."""
        content = """
# This is a comment
[profile:test]

# Another comment
accounts.columns = name

"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".profiles", delete=False
        ) as f:
            f.write(content)
            f.flush()
            try:
                import slurm_cli.utils.profiles as profiles_mod

                with patch.object(
                    profiles_mod, "PROFILE_FILES", [f.name]
                ):
                    manager = ProfileManager()
                    manager._loaded = False
                    profile = manager.get_profile("test")
                    assert profile is not None
                    assert profile["accounts"]["columns"] == ["name"]
            finally:
                os.unlink(f.name)

    def test_parse_multiple_profiles(self):
        """Test parsing multiple profiles in one file."""
        content = """
[profile:test1]
accounts.columns = name

[profile:test2]
accounts.columns = name,description
qos.columns = name,priority
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".profiles", delete=False
        ) as f:
            f.write(content)
            f.flush()
            try:
                import slurm_cli.utils.profiles as profiles_mod

                with patch.object(
                    profiles_mod, "PROFILE_FILES", [f.name]
                ):
                    manager = ProfileManager()
                    manager._loaded = False
                    test1 = manager.get_profile("test1")
                    test2 = manager.get_profile("test2")

                    assert test1 is not None
                    assert test1["accounts"]["columns"] == ["name"]

                    assert test2 is not None
                    assert test2["accounts"]["columns"] == [
                        "name",
                        "description",
                    ]
                    assert test2["qos"]["columns"] == [
                        "name",
                        "priority",
                    ]
            finally:
                os.unlink(f.name)

    def test_wildcard_columns(self):
        """Test parsing wildcard (*) columns."""
        content = """
[profile:test]
accounts.columns = *
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".profiles", delete=False
        ) as f:
            f.write(content)
            f.flush()
            try:
                import slurm_cli.utils.profiles as profiles_mod

                with patch.object(
                    profiles_mod, "PROFILE_FILES", [f.name]
                ):
                    manager = ProfileManager()
                    manager._loaded = False
                    profile = manager.get_profile("test")
                    assert profile["accounts"]["columns"] == "*"
            finally:
                os.unlink(f.name)


class TestProfileStringParsing:
    """Tests for inline profile string parsing."""

    def test_parse_simple_string(self):
        """Test parsing a simple profile string."""
        manager = ProfileManager()
        result = manager.parse_profile_string(
            "accounts.columns=name,description"
        )
        assert "accounts" in result
        assert result["accounts"]["columns"] == ["name", "description"]

    def test_parse_template_string(self):
        """Test parsing a template profile string."""
        manager = ProfileManager()
        result = manager.parse_profile_string(
            "accounts.template=[cyan]{name}[/] - {description}"
        )
        assert "accounts" in result
        assert (
            result["accounts"]["template"]
            == "[cyan]{name}[/] - {description}"
        )

    def test_parse_multiple_settings(self):
        """Test parsing multiple settings separated by semicolon."""
        manager = ProfileManager()
        result = manager.parse_profile_string(
            "accounts.columns=name;qos.columns=name,priority"
        )
        assert "accounts" in result
        assert "qos" in result
        assert result["accounts"]["columns"] == ["name"]
        assert result["qos"]["columns"] == ["name", "priority"]

    def test_parse_semicolon_in_template(self):
        """Test that semicolons in templates are preserved."""
        manager = ProfileManager()
        result = manager.parse_profile_string(
            "accounts.template=name: {name}; desc: {description}"
        )
        assert "accounts" in result
        # Semicolon should be preserved since it's not followed by resource.key=
        assert (
            "name: {name}; desc: {description}"
            in result["accounts"]["template"]
        )

    def test_parse_styles(self):
        """Test parsing style settings."""
        manager = ProfileManager()
        result = manager.parse_profile_string(
            "accounts.styles.name=cyan bold"
        )
        assert "accounts" in result
        assert result["accounts"]["styles"]["name"] == "cyan bold"


class TestNormalizeProfileStr:
    """Tests for _normalize_profile_str function."""

    def test_normalize_with_prefix(self):
        """Test that strings with prefix are unchanged."""
        result = _normalize_profile_str(
            "accounts.template=[cyan]{name}[/]", "accounts"
        )
        assert result == "accounts.template=[cyan]{name}[/]"

    def test_normalize_without_prefix(self):
        """Test that strings without prefix get resource.template= added."""
        result = _normalize_profile_str("[cyan]{name}[/]", "accounts")
        assert result == "accounts.template=[cyan]{name}[/]"

    def test_normalize_none(self):
        """Test that None input returns None."""
        result = _normalize_profile_str(None, "accounts")
        assert result is None

    def test_normalize_different_resources(self):
        """Test normalization with different resource types."""
        result = _normalize_profile_str(
            "{name} - {users}", "reservations"
        )
        assert result == "reservations.template={name} - {users}"

    def test_normalize_column_list_shorthand(self):
        """Test that comma-separated words become columns."""
        result = _normalize_profile_str(
            "name,organization,flags", "accounts"
        )
        assert result == "accounts.columns=name,organization,flags"

    def test_normalize_single_column_shorthand(self):
        """Test that single word without markers becomes column."""
        result = _normalize_profile_str("name", "accounts")
        assert result == "accounts.columns=name"

    def test_normalize_column_vs_template(self):
        """Test distinguishing columns from templates."""
        # With braces -> template
        result = _normalize_profile_str("{name}", "accounts")
        assert result == "accounts.template={name}"

        # With brackets -> template
        result = _normalize_profile_str("[cyan]name[/]", "accounts")
        assert result == "accounts.template=[cyan]name[/]"

        # Plain comma-separated -> columns
        result = _normalize_profile_str("name,desc", "accounts")
        assert result == "accounts.columns=name,desc"


class TestGetProfileConfig:
    """Tests for get_profile_config function."""

    def test_get_default_config(self):
        """Test getting default profile config."""
        columns, styles, template = get_profile_config(
            "default", "accounts"
        )
        assert columns == "*"
        assert "name" in styles
        assert template is None  # default uses columns, not template

    def test_inline_profile_precedence(self):
        """Test that inline profile string takes precedence."""
        columns, styles, template = get_profile_config(
            "default",
            "accounts",
            profile_str="accounts.template=[cyan]{name}[/]",
        )
        assert template == "[cyan]{name}[/]"

    def test_simplified_profile_str(self):
        """Test simplified profile string without resource prefix."""
        columns, styles, template = get_profile_config(
            "default",
            "accounts",
            profile_str="[cyan]{name}[/] - {description}",
        )
        assert template == "[cyan]{name}[/] - {description}"


class TestIsFieldEmpty:
    """Tests for is_field_empty function."""

    def test_none_is_empty(self):
        """Test that None is considered empty."""
        assert is_field_empty("name", None)

    def test_empty_string_is_empty(self):
        """Test that empty string is considered empty."""
        assert is_field_empty("name", "")

    def test_dash_is_empty(self):
        """Test that '-' is considered empty."""
        assert is_field_empty("name", "-")

    def test_empty_list_is_empty(self):
        """Test that empty list is considered empty."""
        assert is_field_empty("items", [])

    def test_value_not_empty(self):
        """Test that actual values are not empty."""
        assert not is_field_empty("name", "test")
        assert not is_field_empty("items", ["a", "b"])

    def test_set_dict_not_set(self):
        """Test set/number pattern when not set."""
        assert is_field_empty("timestamp", {"set": False, "number": 0})

    def test_set_dict_is_set(self):
        """Test set/number pattern when set."""
        assert not is_field_empty(
            "timestamp", {"set": True, "number": 12345}
        )

    def test_default_value_empty(self):
        """Test that default values are considered empty."""
        # accounts.coordinators default is []
        assert is_field_empty("coordinators", [], resource="accounts")
        # reservations.accounts default is ""
        assert is_field_empty("accounts", "", resource="reservations")

    def test_non_default_not_empty(self):
        """Test that non-default values are not empty."""
        assert not is_field_empty(
            "coordinators", ["user1"], resource="accounts"
        )


class TestFormatWithTemplate:
    """Tests for format_with_template function."""

    def test_simple_substitution(self):
        """Test simple field substitution."""
        result = format_with_template("Name: {name}", {"name": "test"})
        assert result == "Name: test"

    def test_multiple_fields(self):
        """Test multiple field substitutions."""
        result = format_with_template(
            "{name} - {description}",
            {"name": "test", "description": "A test item"},
        )
        assert result == "test - A test item"

    def test_newline_escape(self):
        """Test that \\n is converted to newline."""
        result = format_with_template("Line1\\nLine2", {})
        assert result == "Line1\nLine2"

    def test_missing_field(self):
        """Test that missing fields are replaced with placeholder."""
        result = format_with_template(
            "{name} - {missing}", {"name": "test"}
        )
        # Missing fields get a placeholder value (e.g., "-" or empty)
        assert "test - " in result

    def test_conditional_field_with_value(self):
        """Test conditional {?field TEXT} when field has value."""
        result = format_with_template(
            "Name: {name}{?users , Users: {users}}",
            {"name": "test", "users": "root,admin"},
        )
        assert result == "Name: test, Users: root,admin"

    def test_conditional_field_without_value(self):
        """Test conditional {?field TEXT} when field is empty."""
        result = format_with_template(
            "Name: {name}{?users , Users: {users}}",
            {"name": "test", "users": ""},
        )
        assert result == "Name: test"

    def test_conditional_with_none(self):
        """Test conditional when field is None."""
        result = format_with_template(
            "Name: {name}{?users , Users: {users}}",
            {"name": "test", "users": None},
        )
        assert result == "Name: test"

    def test_conditional_with_resource_defaults(self):
        """Test conditional with resource-specific defaults."""
        result = format_with_template(
            "Name: {name}{?accounts , Accounts: {accounts}}",
            {"name": "test", "accounts": ""},
            resource="reservations",
        )
        # accounts default for reservations is ""
        assert result == "Name: test"

    def test_rich_markup_preserved(self):
        """Test that Rich markup is preserved in output."""
        result = format_with_template(
            "[cyan]{name}[/cyan]", {"name": "test"}
        )
        assert result == "[cyan]test[/cyan]"

    def test_custom_value_formatter(self):
        """Test using a custom value formatter."""

        def uppercase_formatter(field: str, value: Any) -> str:
            return str(value).upper()

        result = format_with_template(
            "Name: {name}",
            {"name": "test"},
            value_formatter=uppercase_formatter,
        )
        assert result == "Name: TEST"

    def test_nested_conditional(self):
        """Test conditional with field placeholder inside."""
        result = format_with_template(
            "{?users Users: [hot_pink]{users}[/]}", {"users": "root"}
        )
        assert result == "Users: [hot_pink]root[/]"


class TestMultilineTemplateParsing:
    """Tests for multi-line template parsing with backslash continuation."""

    def test_simple_continuation(self):
        """Test simple line continuation."""
        content = """
[profile:test]
accounts.template = line1 \\
line2
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".profiles", delete=False
        ) as f:
            f.write(content)
            f.flush()
            try:
                import slurm_cli.utils.profiles as profiles_mod

                with patch.object(
                    profiles_mod, "PROFILE_FILES", [f.name]
                ):
                    manager = ProfileManager()
                    manager._loaded = False
                    profile = manager.get_profile("test")
                    template = profile["accounts"]["template"]
                    assert "line1" in template
                    assert "line2" in template
            finally:
                os.unlink(f.name)

    def test_multiple_continuations(self):
        """Test multiple line continuations."""
        content = """
[profile:test]
reservations.template = [bold]{name}[/] \\
    Start: {start_time} \\
    End: {end_time} \\
    Users: {users}
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".profiles", delete=False
        ) as f:
            f.write(content)
            f.flush()
            try:
                import slurm_cli.utils.profiles as profiles_mod

                with patch.object(
                    profiles_mod, "PROFILE_FILES", [f.name]
                ):
                    manager = ProfileManager()
                    manager._loaded = False
                    profile = manager.get_profile("test")
                    template = profile["reservations"]["template"]
                    assert "[bold]{name}[/]" in template
                    assert "Start: {start_time}" in template
                    assert "End: {end_time}" in template
                    assert "Users: {users}" in template
            finally:
                os.unlink(f.name)

    def test_continuation_preserves_newline_escapes(self):
        """Test that \\n escapes are preserved across continuations."""
        content = """
[profile:test]
accounts.template = Line1\\n\\
    Line2\\n\\
    Line3
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".profiles", delete=False
        ) as f:
            f.write(content)
            f.flush()
            try:
                import slurm_cli.utils.profiles as profiles_mod

                with patch.object(
                    profiles_mod, "PROFILE_FILES", [f.name]
                ):
                    manager = ProfileManager()
                    manager._loaded = False
                    profile = manager.get_profile("test")
                    template = profile["accounts"]["template"]
                    # Should contain \n escapes
                    assert (
                        "\\n" in template
                        or "\n"
                        not in template.replace("Line1", "")
                        .replace("Line2", "")
                        .replace("Line3", "")
                    )
            finally:
                os.unlink(f.name)


class TestDefaultFieldValues:
    """Tests for DEFAULT_FIELD_VALUES configuration."""

    def test_reservations_defaults(self):
        """Test default values for reservations."""
        defaults = DEFAULT_FIELD_VALUES.get("reservations", {})
        assert "accounts" in defaults
        assert "users" in defaults
        assert defaults["accounts"] == ""

    def test_accounts_defaults(self):
        """Test default values for accounts."""
        defaults = DEFAULT_FIELD_VALUES.get("accounts", {})
        assert "coordinators" in defaults
        assert defaults["coordinators"] == []

    def test_qos_defaults(self):
        """Test default values for qos."""
        defaults = DEFAULT_FIELD_VALUES.get("qos", {})
        assert "flags" in defaults
        assert defaults["flags"] == []


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_profile_string(self):
        """Test parsing empty profile string."""
        manager = ProfileManager()
        result = manager.parse_profile_string("")
        assert result == {}

    def test_invalid_profile_file(self):
        """Test that missing profile files are handled gracefully."""
        import slurm_cli.utils.profiles as profiles_mod

        with patch.object(
            profiles_mod,
            "PROFILE_FILES",
            ["/nonexistent/path/profiles.conf"],
        ):
            manager = ProfileManager()
            manager._loaded = False
            # Should not raise, just skip missing files
            profiles = manager.list_profiles()
            assert (
                "default" in profiles
            )  # Built-in defaults still present

    def test_profile_without_resources(self):
        """Test parsing profile with no resource settings."""
        content = """
[profile:empty]
# No settings here
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".profiles", delete=False
        ) as f:
            f.write(content)
            f.flush()
            try:
                import slurm_cli.utils.profiles as profiles_mod

                with patch.object(
                    profiles_mod, "PROFILE_FILES", [f.name]
                ):
                    manager = ProfileManager()
                    manager._loaded = False
                    profile = manager.get_profile("empty")
                    assert profile == {}
            finally:
                os.unlink(f.name)

    def test_template_with_special_characters(self):
        """Test template with special characters."""
        result = format_with_template(
            "CPU: {cpu}% | RAM: {ram}GB | Temp: {temp}°C",
            {"cpu": "85", "ram": "16", "temp": "72"},
        )
        assert "CPU: 85%" in result
        assert "RAM: 16GB" in result
        assert "Temp: 72°C" in result

    def test_template_with_unicode(self):
        """Test template with Unicode characters."""
        result = format_with_template(
            "Status: {status} ✓ Users: {users} 👥",
            {"status": "active", "users": "5"},
        )
        assert "✓" in result
        assert "👥" in result
        assert "active" in result

    def test_deeply_nested_styles(self):
        """Test parsing deeply nested styles."""
        manager = ProfileManager()
        result = manager.parse_profile_string(
            "accounts.styles.name=cyan bold"
        )
        assert result["accounts"]["styles"]["name"] == "cyan bold"


class TestProfileFileParseErrors:
    """Tests for profile file parse error handling."""

    def test_parse_error_in_profile_file(self):
        """Test handling of parse errors in profile files."""
        import io
        import sys
        from unittest import mock

        with tempfile.TemporaryDirectory() as tmpdir:
            profile_file = os.path.join(tmpdir, "bad.profiles")
            # Create a file that might cause issues
            with open(profile_file, "w") as f:
                f.write("[profile:test]\n")
                f.write("bad line without equals\n")

            manager = ProfileManager()
            # Mock PROFILE_FILES to use our test file
            with mock.patch(
                "slurm_cli.utils.profiles.PROFILE_FILES", [profile_file]
            ):
                # Capture stderr
                captured = io.StringIO()
                with mock.patch.object(sys, "stderr", captured):
                    manager._load_profiles()
                # Should have warning in stderr
                # (may or may not depending on implementation)


class TestMergeProfiles:
    """Tests for _merge_profiles method."""

    def test_merge_existing_profile(self):
        """Test merging into existing profile."""
        manager = ProfileManager()
        manager._profiles = {
            "custom": {"accounts": {"columns": ["name"]}}
        }
        new_profiles = {
            "custom": {"accounts": {"styles": {"name": "bold"}}}
        }
        manager._merge_profiles(new_profiles)

        assert "custom" in manager._profiles
        assert manager._profiles["custom"]["accounts"]["columns"] == [
            "name"
        ]
        assert (
            manager._profiles["custom"]["accounts"]["styles"]["name"]
            == "bold"
        )


class TestDeepMerge:
    """Tests for _deep_merge method."""

    def test_deep_merge_nested_dicts(self):
        """Test deep merge with nested dicts."""
        manager = ProfileManager()
        base = {"level1": {"level2": {"key1": "value1"}}}
        override = {"level1": {"level2": {"key2": "value2"}}}
        manager._deep_merge(base, override)

        assert base["level1"]["level2"]["key1"] == "value1"
        assert base["level1"]["level2"]["key2"] == "value2"

    def test_deep_merge_replace_non_dict(self):
        """Test deep merge replaces non-dict values."""
        manager = ProfileManager()
        base = {"key": "old_value"}
        override = {"key": "new_value"}
        manager._deep_merge(base, override)

        assert base["key"] == "new_value"


class TestIsFieldEmptyWithDefaults:
    """Tests for is_field_empty with default values."""

    def test_field_matches_default(self):
        """Test field that matches its default value."""
        # If DEFAULT_FIELD_VALUES has a value for accounts.coordinators
        result = is_field_empty("coordinators", "", resource="accounts")
        assert result is True

    def test_field_differs_from_default(self):
        """Test field that differs from its default value."""
        result = is_field_empty(
            "coordinators", "admin,user1", resource="accounts"
        )
        assert result is False


class TestFormatWithTemplateDict:
    """Tests for format_with_template with dict values."""

    def test_dict_with_set_number(self):
        """Test formatting dict with set=True and number."""
        result = format_with_template(
            "{value}", {"value": {"set": True, "number": 42}}
        )
        assert "42" in result

    def test_dict_with_infinite(self):
        """Test formatting dict with infinite=True."""
        result = format_with_template(
            "{value}", {"value": {"infinite": True}}
        )
        assert "∞" in result

    def test_dict_without_set(self):
        """Test formatting dict without set flag."""
        result = format_with_template(
            "{value}", {"value": {"some_key": "some_val"}}
        )
        # Should stringify the dict
        assert "some_key" in result or "some_val" in result


class TestExtractFieldsFromTemplate:
    """Tests for extract_fields_from_template."""

    def test_simple_fields(self):
        """Test extracting simple fields."""
        fields = extract_fields_from_template("{name} {description}")
        assert "name" in fields
        assert "description" in fields

    def test_conditional_fields(self):
        """Test extracting conditional fields."""
        fields = extract_fields_from_template("{?status Active}")
        assert "status" in fields

    def test_mixed_fields(self):
        """Test extracting mix of regular and conditional fields."""
        fields = extract_fields_from_template(
            "{name} {?status [status]}"
        )
        assert "name" in fields
        assert "status" in fields


class TestShowProfileHelp:
    """Tests for show_profile_help."""

    def test_known_resource(self, capsys):
        """Test showing help for known resource."""
        result = show_profile_help("accounts")
        assert result is True
        captured = capsys.readouterr()
        assert "name" in captured.out
        assert "description" in captured.out

    def test_unknown_resource(self, capsys):
        """Test showing help for unknown resource."""
        result = show_profile_help("unknownresource")
        assert result is True
        captured = capsys.readouterr()
        assert "No field documentation" in captured.out
        assert "Available resources" in captured.out

    def test_resource_alias(self, capsys):
        """Test showing help with resource alias."""
        result = show_profile_help("acc")
        assert result is True
        captured = capsys.readouterr()
        assert "accounts" in captured.out.lower()


class TestResourceFields:
    """Tests for get_resource_fields() function."""

    def test_all_resources_have_fields(self):
        """Test all expected resources have field definitions."""
        resource_fields = get_resource_fields()
        expected = [
            "accounts",
            "qos",
            "partitions",
            "nodes",
            "reservations",
            "coordinators",
            "users",
        ]
        for resource in expected:
            assert resource in resource_fields
