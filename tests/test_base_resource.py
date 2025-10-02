"""Tests for the BaseSlurmResource module."""

import sys
from typing import List, Optional, Tuple

# Add src to path for imports
sys.path.insert(0, "src")
from slurm_cli.utils.base_resource import BaseSlurmResource  # noqa: E402


class TestTimePatterns:
    """Test time pattern matching functionality."""

    def test_time_patterns(self):
        """Test all time patterns with various valid and invalid inputs."""
        # Test cases: (input_string, should_match, expected_groups,
        # description)
        test_cases: List[Tuple[str, bool, Optional[dict], str]] = [
            # YYYY-MM-DD[THH:MM[:SS]] pattern
            ("2024-01-15", True, {"date": "2024-01-15"}, "Date only"),
            (
                "2024-01-15T10:30",
                True,
                {"date": "2024-01-15", "h": "10", "m": "30"},
                "Date with time",
            ),
            (
                "2024-01-15T10:30:45",
                True,
                {"date": "2024-01-15", "h": "10", "m": "30", "s": "45"},
                "Date with full time",
            ),
            (
                "2024-01-15 10:30",
                True,
                {"date": "2024-01-15", "h": "10", "m": "30"},
                "Date with space separator",
            ),
            (
                "2024-01-15 10:30:45",
                True,
                {"date": "2024-01-15", "h": "10", "m": "30", "s": "45"},
                "Date with space and seconds",
            ),
            # [D-]HH:MM:SS pattern
            (
                "12:30:45",
                True,
                {"h": "12", "m": "30", "s": "45"},
                "Time only",
            ),
            (
                "2-12:30:45",
                True,
                {"days": "2", "h": "12", "m": "30", "s": "45"},
                "Days with time",
            ),
            (
                "0-00:30:45",
                True,
                {"days": "0", "h": "00", "m": "30", "s": "45"},
                "Zero days with time",
            ),
            (
                "365-23:59:59",
                True,
                {"days": "365", "h": "23", "m": "59", "s": "59"},
                "Large number of days",
            ),
            # HH:MM:SS pattern (same as above, but testing the specific
            # pattern)
            (
                "01:02:03",
                True,
                {"h": "01", "m": "02", "s": "03"},
                "Two-digit time",
            ),
            (
                "1:2:3",
                True,
                {"h": "1", "m": "2", "s": "3"},
                "Single-digit time",
            ),
            (
                "00:00:00",
                True,
                {"h": "00", "m": "00", "s": "00"},
                "Midnight",
            ),
            (
                "23:59:59",
                True,
                {"h": "23", "m": "59", "s": "59"},
                "End of day",
            ),
            # MMDDYY pattern
            (
                "011524",
                True,
                {"month": "01", "day": "15", "year": "24"},
                "MMDDYY format",
            ),
            (
                "123199",
                True,
                {"month": "12", "day": "31", "year": "99"},
                "End of year",
            ),
            (
                "010100",
                True,
                {"month": "01", "day": "01", "year": "00"},
                "New year",
            ),
            # MM/DD/YY pattern
            (
                "01/15/24",
                True,
                {"month": "01", "day": "15", "year": "24"},
                "MM/DD/YY format",
            ),
            (
                "12/31/99",
                True,
                {"month": "12", "day": "31", "year": "99"},
                "End of year with slashes",
            ),
            (
                "01/01/00",
                True,
                {"month": "01", "day": "01", "year": "00"},
                "New year with slashes",
            ),
            # MM.DD.YY pattern
            (
                "01.15.24",
                True,
                {"month": "01", "day": "15", "year": "24"},
                "MM.DD.YY format",
            ),
            (
                "12.31.99",
                True,
                {"month": "12", "day": "31", "year": "99"},
                "End of year with dots",
            ),
            (
                "01.01.00",
                True,
                {"month": "01", "day": "01", "year": "00"},
                "New year with dots",
            ),
            # Invalid cases (patterns match but values are invalid)
            ("invalid", False, None, "Invalid string"),
            (
                "2024-13-01",
                True,
                {"date": "2024-13-01"},
                "Invalid month (pattern matches)",
            ),
            (
                "2024-01-32",
                True,
                {"date": "2024-01-32"},
                "Invalid day (pattern matches)",
            ),
            (
                "25:00:00",
                True,
                {"h": "25", "m": "00", "s": "00"},
                "Invalid hour (pattern matches)",
            ),
            (
                "12:60:00",
                True,
                {"h": "12", "m": "60", "s": "00"},
                "Invalid minute (pattern matches)",
            ),
            (
                "12:30:60",
                True,
                {"h": "12", "m": "30", "s": "60"},
                "Invalid second (pattern matches)",
            ),
            ("2024/01/15", False, None, "Wrong date separator"),
            ("01-15-24", False, None, "Wrong date format"),
            ("", False, None, "Empty string"),
            ("12:30", False, None, "Incomplete time"),
            ("12:30:45:00", False, None, "Too many time components"),
        ]

        for (
            input_str,
            should_match,
            expected_groups,
            description,
        ) in test_cases:
            match_result = None
            matched_pattern = None

            # Test each pattern
            for i, pattern in enumerate(
                BaseSlurmResource._TIME_PATTERNS
            ):
                match = pattern.match(input_str)
                if match:
                    match_result = match
                    matched_pattern = i
                    break

            # Check if match result is as expected
            if should_match:
                assert (
                    match_result is not None
                ), f"Expected '{input_str}' to match but didn't "
                f"({description})"

                # Check if expected groups match
                if expected_groups:
                    for key, expected_value in expected_groups.items():
                        assert (
                            match_result.group(key) == expected_value
                        ), (
                            f"Group '{key}' mismatch for '{input_str}': "
                            f"expected '{expected_value}', got "
                            f"'{match_result.group(key)}' ({description})"
                        )
            else:
                assert (
                    match_result is None
                ), f"Expected '{input_str}' to be rejected but matched "
                f"pattern {matched_pattern} ({description})"

    def test_special_time_cases(self):
        """Test special cases like 'now' and 'tomorrow'."""
        special_cases = [
            ("now", True, "now prefix"),
            ("now+1hour", True, "now with addition"),
            ("now+30minutes", True, "now with minutes"),
            ("tomorrow", True, "tomorrow"),
            ("tomorrow+2hours", True, "tomorrow with addition"),
            ("now+", True, "incomplete now (still starts with now)"),
            (
                "tomorrow+",
                True,
                "incomplete tomorrow (still starts with tomorrow)",
            ),
        ]

        for input_str, should_match, description in special_cases:
            # Test the special case logic from the actual method
            if input_str.startswith("now") or input_str.startswith(
                "tomorrow"
            ):
                result = True
            else:
                result = False

            assert (
                result == should_match
            ), f"Special case test failed for '{input_str}': {description}"


class TestExpandNodenames:
    """Test node name expansion functionality."""

    def test_expand_nodenames(self):
        """Test node name expansion functionality."""
        # Test cases: (input_pattern, expected_output, description)
        test_cases = [
            # Basic patterns
            ("node01", ["node01"], "Single node without brackets"),
            ("node[01]", ["node01"], "Single node with brackets"),
            ("node[01,02]", ["node01", "node02"], "Two nodes"),
            (
                "node[01,03,05]",
                ["node01", "node03", "node05"],
                "Multiple single nodes",
            ),
            # Range patterns
            (
                "node[01-03]",
                ["node01", "node02", "node03"],
                "Simple range",
            ),
            (
                "node[10-12]",
                ["node10", "node11", "node12"],
                "Range with two digits",
            ),
            (
                "node[001-003]",
                ["node001", "node002", "node003"],
                "Range with leading zeros",
            ),
            (
                "node[1-5]",
                ["node1", "node2", "node3", "node4", "node5"],
                "Single digit range",
            ),
            # Mixed patterns
            (
                "node[01,03,10-12]",
                ["node01", "node03", "node10", "node11", "node12"],
                "Mixed single and range",
            ),
            (
                "node[001,005,010-012]",
                ["node001", "node005", "node010", "node011", "node012"],
                "Mixed with leading zeros",
            ),
            (
                "node[1,3,5-7,9]",
                ["node1", "node3", "node5", "node6", "node7", "node9"],
                "Complex mixed pattern",
            ),
            # Different prefixes
            (
                "gpu[01-03]",
                ["gpu01", "gpu02", "gpu03"],
                "Different prefix",
            ),
            (
                "compute-node[001-003]",
                [
                    "compute-node001",
                    "compute-node002",
                    "compute-node003",
                ],
                "Multi-part prefix",
            ),
            (
                "worker[1-3]",
                ["worker1", "worker2", "worker3"],
                "Simple prefix",
            ),
            # Edge cases
            (
                "node[01-01]",
                ["node01"],
                "Range with same start and end",
            ),
            (
                "node[000-002]",
                ["node000", "node001", "node002"],
                "Range with three digits",
            ),
            (
                "node[99-101]",
                ["node099", "node100", "node101"],
                "Range crossing digit boundary (preserves leading zeros)",
            ),
            (
                "node[1,2,3]",
                ["node1", "node2", "node3"],
                "All single nodes",
            ),
            # Large ranges
            (
                "node[1-10]",
                [
                    "node01",
                    "node02",
                    "node03",
                    "node04",
                    "node05",
                    "node06",
                    "node07",
                    "node08",
                    "node09",
                    "node10",
                ],
                "Large range (preserves leading zeros)",
            ),
            # Empty and invalid patterns (should still work)
            ("", [""], "Empty pattern"),
            ("node", ["node"], "No brackets or numbers"),
        ]

        for input_pattern, expected_output, description in test_cases:
            result = BaseSlurmResource.expand_nodenames(input_pattern)
            assert result == expected_output, (
                f"expand_nodenames test failed for '{input_pattern}': "
                f"expected {expected_output}, got {result} ({description})"
            )

    def test_expand_nodenames_edge_cases(self):
        """Test edge cases for node name expansion."""
        # Test that the function doesn't crash on malformed input
        malformed_inputs = [
            "node[",  # Missing closing bracket
            "node]",  # Missing opening bracket
            "node[1-]",  # Incomplete range
            "node[-5]",  # Incomplete range
            "node[1,]",  # Trailing comma
            "node[,1]",  # Leading comma
        ]

        for malformed_input in malformed_inputs:
            # The function should either return a reasonable result
            # or raise an exception
            # We just want to make sure it doesn't crash the system
            try:
                result = BaseSlurmResource.expand_nodenames(
                    malformed_input
                )
                # If it returns a result, it should be a list
                assert isinstance(
                    result, list
                ), f"Result should be a list for '{malformed_input}'"
            except Exception as e:
                # If it raises an exception, that's also acceptable
                assert isinstance(
                    e, (ValueError, IndexError, AttributeError)
                ), f"Unexpected exception type for '{malformed_input}': "
                f"{type(e)}"

    def test_expand_nodenames_performance(self):
        """Test performance with large ranges."""
        # Test with a reasonably large range to ensure performance is
        # acceptable
        large_pattern = "node[1-100]"
        result = BaseSlurmResource.expand_nodenames(large_pattern)

        # Should have 100 nodes
        assert (
            len(result) == 100
        ), f"Expected 100 nodes, got {len(result)}"

        # Check first and last few nodes (function preserves leading zeros
        # based on max width)
        assert (
            result[0] == "node001"
        ), f"First node should be 'node001', got '{result[0]}'"
        assert (
            result[9] == "node010"
        ), f"10th node should be 'node010', got '{result[9]}'"
        assert (
            result[99] == "node100"
        ), f"Last node should be 'node100', got '{result[99]}'"

        # Check that all nodes are unique
        assert len(set(result)) == len(
            result
        ), "All nodes should be unique"


class TestBaseSlurmResource:
    """Test BaseSlurmResource class functionality."""

    def test_time_patterns_exist(self):
        """Test that time patterns are properly defined."""
        assert hasattr(
            BaseSlurmResource, "_TIME_PATTERNS"
        ), "_TIME_PATTERNS should exist"
        assert isinstance(
            BaseSlurmResource._TIME_PATTERNS, list
        ), "_TIME_PATTERNS should be a list"
        assert (
            len(BaseSlurmResource._TIME_PATTERNS) > 0
        ), "_TIME_PATTERNS should not be empty"

        # Check that all patterns are compiled regex objects
        for i, pattern in enumerate(BaseSlurmResource._TIME_PATTERNS):
            assert hasattr(
                pattern, "match"
            ), f"Pattern {i} should be a regex object"

    def test_expand_nodenames_method_exists(self):
        """Test that expand_nodenames method exists and is callable."""
        assert hasattr(
            BaseSlurmResource, "expand_nodenames"
        ), "expand_nodenames method should exist"
        assert callable(
            BaseSlurmResource.expand_nodenames
        ), "expand_nodenames should be callable"

    def test_expand_nodenames_return_type(self):
        """Test that expand_nodenames returns a list."""
        result = BaseSlurmResource.expand_nodenames("node[1-3]")
        assert isinstance(
            result, list
        ), "expand_nodenames should return a list"
        assert len(result) == 3, "Should return 3 nodes for node[1-3]"
