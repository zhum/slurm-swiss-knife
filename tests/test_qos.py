"""Tests for the qos module."""

import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

import pytest  # noqa: F401

# Add src to path for imports
sys.path.insert(0, "src")

from slurm_cli.utils.qos import Qos  # noqa: E402


def create_mock_subprocess_result(
    stdout: str = "", returncode: int = 0
):
    """Create a mock subprocess.CompletedProcess result."""
    mock_result = MagicMock()
    mock_result.stdout = stdout
    mock_result.returncode = returncode
    return mock_result


class TestQosInit:
    """Tests for Qos.__init__ method."""

    def test_qos_init_with_name(self):
        """Test Qos initialization with just name."""
        qos = Qos("normal")
        assert qos.name == "normal"
        assert qos.kwargs == {}

    def test_qos_init_with_kwargs(self):
        """Test Qos initialization with additional kwargs."""
        qos = Qos("high", priority=100, description="High priority QoS")
        assert qos.name == "high"
        assert qos.kwargs["priority"] == 100
        assert qos.kwargs["description"] == "High priority QoS"


class TestQosCreate:
    """Tests for Qos.create method."""

    def test_create_qos_success(self):
        """Test successful QoS creation."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.create("newqos")

            result = output.getvalue()
            assert "Creating QoS: newqos" in result
            assert "created successfully" in result

    def test_create_qos_with_stdout(self):
        """Test QoS creation with subprocess stdout."""
        mock_result = create_mock_subprocess_result(
            stdout="QoS newqos added successfully"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.create("newqos")

            result = output.getvalue()
            assert "QoS newqos added successfully" in result

    def test_create_qos_with_kwargs(self):
        """Test QoS creation with additional arguments."""
        mock_result = create_mock_subprocess_result()
        with patch.object(
            subprocess, "run", return_value=mock_result
        ) as mock_run:
            Qos.create("newqos", priority=100, description="Test QoS")

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "sacctmgr" in call_args
            assert "create" in call_args
            assert "qos" in call_args
            assert "newqos" in call_args
            assert "priority=100" in call_args
            assert "description=Test QoS" in call_args

    def test_create_qos_failure(self):
        """Test QoS creation failure handling."""
        error = subprocess.CalledProcessError(
            1, "sacctmgr", stderr="QoS already exists"
        )
        with patch.object(subprocess, "run", side_effect=error):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.create("existingqos")

            result = output.getvalue()
            assert "Creating QoS: existingqos" in result
            assert "Failed to create QoS" in result

    def test_create_qos_failure_without_stderr(self):
        """Test QoS creation failure without stderr."""
        error = subprocess.CalledProcessError(1, "sacctmgr")
        with patch.object(subprocess, "run", side_effect=error):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.create("badqos")

            result = output.getvalue()
            assert "Failed to create QoS" in result


class TestQosUpdate:
    """Tests for Qos.update method."""

    def test_update_qos_simple(self):
        """Test simple QoS update with name."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(
            subprocess,
            "run",
            return_value=mock_result,
        ) as mock_run:
            Qos.update("normal", priority=200)

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "sacctmgr" in call_args
            assert "-i" in call_args
            assert "modify" in call_args
            assert "qos" in call_args
            assert "where" in call_args
            assert "name=normal" in call_args
            assert "set" in call_args
            assert "priority=200" in call_args

    def test_update_qos_with_preemptmode_valid(self):
        """Test update with valid preempt modes."""
        for mode in [
            "OFF",
            "CANCEL",
            "GANG",
            "REQUEUE",
            "SUSPEND",
            "WITHIN",
        ]:
            mock_result = create_mock_subprocess_result(stdout="")
            with patch.object(
                subprocess,
                "run",
                return_value=mock_result,
            ) as mock_run:
                Qos.update("testqos", preemptmode=mode)

                mock_run.assert_called_once()
                call_args = mock_run.call_args[0][0]
                assert f"preemptmode={mode}" in call_args

    def test_update_qos_preemptmode_invalid(self):
        """Test update with invalid preempt mode."""
        with patch.object(subprocess, "run") as mock_run:
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.update("testqos", preemptmode="INVALID")

            # Should NOT call subprocess.run
            mock_run.assert_not_called()
            result = output.getvalue()
            assert "Invalid preemptmode" in result

    def test_update_qos_multiple_kwargs(self):
        """Test update with multiple kwargs."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(
            subprocess,
            "run",
            return_value=mock_result,
        ) as mock_run:
            Qos.update(
                "testqos",
                priority=100,
                maxwall=3600,
                description="Updated QoS",
            )

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "priority=100" in call_args
            assert "maxwall=3600" in call_args
            assert "description=Updated QoS" in call_args

    def test_update_qos_where_mode(self):
        """Test update with where conditions."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(
            subprocess,
            "run",
            return_value=mock_result,
        ) as mock_run:
            Qos.update(
                "",
                where_conditions=["priority=100"],
                set_values=["priority=200"],
            )

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "where" in call_args
            assert "priority=100" in call_args
            assert "set" in call_args
            assert "priority=200" in call_args

    def test_update_qos_where_mode_preemptmode_validation(self):
        """Test that invalid preemptmode is rejected in WHERE mode."""
        with patch.object(subprocess, "run") as mock_run:
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.update(
                    "",
                    where_conditions=["priority=100"],
                    set_values=["preemptmode=INVALID"],
                )

            # Should NOT call subprocess.run
            mock_run.assert_not_called()
            result = output.getvalue()
            assert "Invalid preemptmode" in result

    def test_update_qos_no_name_or_conditions(self):
        """Test update without name or where conditions."""
        with patch.object(subprocess, "run") as mock_run:
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.update("")

            # Should NOT call subprocess.run
            mock_run.assert_not_called()
            result = output.getvalue()
            assert "No QoS name or WHERE conditions" in result

    def test_update_qos_failure(self):
        """Test update failure handling."""
        error = subprocess.CalledProcessError(
            1, "sacctmgr", stderr="No matching QoS"
        )
        with patch.object(subprocess, "run", side_effect=error):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.update("nonexistent", priority=100)

            result = output.getvalue()
            assert "Failed to update QoS" in result

    def test_update_qos_verbose(self):
        """Test update with verbose flag."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(
            subprocess,
            "run",
            return_value=mock_result,
        ):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.update("testqos", verbose=True, priority=100)

            result = output.getvalue()
            assert "Running:" in result
            assert "updated successfully" in result

    def test_update_qos_with_stdout(self):
        """Test update with subprocess stdout."""
        mock_result = create_mock_subprocess_result(
            stdout="Modified QoS record(s)"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.update("testqos", priority=100)

            result = output.getvalue()
            assert "Modified QoS record(s)" in result

    def test_update_qos_skip_none_values(self):
        """Test that None values are skipped."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(
            subprocess,
            "run",
            return_value=mock_result,
        ) as mock_run:
            Qos.update("testqos", priority=100, maxwall=None)

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "priority=100" in call_args
            # maxwall should NOT be included
            assert "maxwall=None" not in call_args
            assert "maxwall=" not in " ".join(call_args)

    def test_update_qos_where_mode_multiple_conditions(self):
        """Test update with multiple WHERE conditions."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(
            subprocess,
            "run",
            return_value=mock_result,
        ) as mock_run:
            Qos.update(
                "",
                where_conditions=[
                    "priority=100",
                    "flags=NoDecay",
                ],
                set_values=["priority=200"],
            )

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "priority=100" in call_args
            assert "flags=NoDecay" in call_args


class TestQosDelete:
    """Tests for Qos.delete method."""

    def test_delete_qos(self):
        """Test QoS delete method."""
        output = io.StringIO()
        with redirect_stdout(output):
            Qos.delete("oldqos")

        result = output.getvalue()
        assert "Deleting QoS: oldqos" in result


class TestQosShow:
    """Tests for Qos.show method."""

    def test_show_json_style(self):
        """Test show with JSON style."""
        mock_data = {
            "qos": [
                {
                    "name": "normal",
                    "id": 1,
                    "description": "Normal QoS",
                    "priority": {"set": True, "number": 100},
                    "flags": [],
                }
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.show(style="json")

            result = output.getvalue()
            assert "normal" in result

    def test_show_pretty_style(self):
        """Test show with pretty style (default)."""
        mock_data = {
            "qos": [
                {
                    "name": "normal",
                    "id": 1,
                    "description": "Normal QoS",
                    "priority": {"set": True, "number": 100},
                    "flags": [],
                    "preempt": {"mode": [], "list": []},
                    "usage_factor": {"set": True, "number": 1.0},
                    "limits": {},
                }
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.show(style="pretty")

            result = output.getvalue()
            assert "normal" in result

    def test_show_csv_style(self):
        """Test show with CSV style."""
        mock_data = {
            "qos": [
                {
                    "name": "normal",
                    "id": 1,
                    "description": "Normal QoS",
                    "priority": {"set": True, "number": 100},
                    "flags": ["FLAG1"],
                    "preempt": {"mode": [], "list": []},
                    "usage_factor": {"set": True, "number": 1.0},
                    "limits": {},
                }
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.show(style="csv", delimiter=";")

            result = output.getvalue()
            lines = result.strip().split("\n")
            assert len(lines) >= 2  # Header + data
            assert ";" in lines[0]

    def test_show_csv_with_custom_delimiter(self):
        """Test show CSV with custom delimiter."""
        mock_data = {
            "qos": [
                {
                    "name": "normal",
                    "id": 1,
                    "description": "",
                    "priority": {"set": False},
                    "flags": [],
                    "preempt": {"mode": [], "list": []},
                    "limits": {},
                }
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.show(style="csv", delimiter="|")

            result = output.getvalue()
            assert "|" in result

    def test_show_empty_qos(self):
        """Test show with no QoS in output."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.show()

            result = output.getvalue()
            assert "No QoS found" in result

    def test_show_with_field_filter(self):
        """Test show with field filter."""
        mock_data = {
            "qos": [
                {"name": "normal", "id": 1},
                {"name": "high", "id": 2},
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.show(field="normal")

            result = output.getvalue()
            assert "normal" in result

    def test_show_with_field_not_found(self):
        """Test show with field filter that doesn't match."""
        mock_data = {"qos": [{"name": "normal", "id": 1}]}
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.show(field="nonexistent")

            result = output.getvalue()
            assert "not found" in result

    def test_show_with_zebra_striping(self):
        """Test show with zebra striping enabled."""
        mock_data = {
            "qos": [
                {
                    "name": f"qos{i}",
                    "id": i,
                    "description": "",
                    "priority": {"set": False},
                    "flags": [],
                    "preempt": {"mode": [], "list": []},
                    "limits": {},
                }
                for i in range(5)
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.show(zebra=True)

            result = output.getvalue()
            assert len(result) > 0

    def test_show_with_template(self):
        """Test show with template-based output."""
        mock_data = {
            "qos": [
                {
                    "name": "normal",
                    "id": 1,
                    "description": "Normal QoS",
                    "priority": {"set": True, "number": 100},
                    "flags": ["FLAG1"],
                    "preempt": {"mode": ["SUSPEND"], "list": []},
                    "usage_factor": {"set": True, "number": 1.0},
                    "limits": {
                        "max": {
                            "jobs": {
                                "per": {
                                    "user": {"set": True, "number": 10}
                                }
                            },
                            "tres": {
                                "per": {"job": [], "user": []},
                                "total": [],
                            },
                            "wall_clock": {
                                "per": {
                                    "job": {"set": True, "number": 3600}
                                }
                            },
                        }
                    },
                }
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.show(
                    style="pretty",
                    profile_str="[cyan]{name}[/] - {description}",
                )

            result = output.getvalue()
            assert "normal" in result.lower()

    def test_show_subprocess_error(self):
        """Test show with subprocess error."""
        error = subprocess.CalledProcessError(
            1, "sacctmgr", stderr="Permission denied"
        )
        with patch.object(subprocess, "run", side_effect=error):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.show()

            result = output.getvalue()
            assert "Failed to show QoS" in result

    def test_show_json_decode_error(self):
        """Test show with invalid JSON response."""
        mock_result = create_mock_subprocess_result(
            stdout="invalid json {"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.show()

            result = output.getvalue()
            assert "Failed to parse JSON" in result

    def test_show_with_tres_data(self):
        """Test show with TRES data in limits."""
        mock_data = {
            "qos": [
                {
                    "name": "gpu",
                    "id": 2,
                    "description": "GPU QoS",
                    "priority": {"set": True, "number": 200},
                    "flags": [],
                    "preempt": {"mode": [], "list": []},
                    "usage_factor": {"set": True, "number": 1.0},
                    "limits": {
                        "max": {
                            "tres": {
                                "per": {
                                    "job": [
                                        {"name": "cpu", "count": 64},
                                        {"type": "gpu", "count": 4},
                                    ],
                                    "user": [
                                        {"name": "mem", "count": 256}
                                    ],
                                },
                                "total": [
                                    {"name": "node", "count": 10}
                                ],
                            }
                        }
                    },
                }
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.show(style="pretty")

            result = output.getvalue()
            assert "gpu" in result.lower()

    def test_show_with_default_values_skipped(self):
        """Test that default values are skipped in column detection."""
        mock_data = {
            "qos": [
                {
                    "name": "normal",
                    "id": 1,
                    "description": "",
                    "priority": {"set": True, "number": 0},  # Default
                    "flags": [],
                    "preempt": {
                        "mode": ["DISABLED"],
                        "list": [],
                    },  # Default
                    "usage_factor": {
                        "set": True,
                        "number": 1.0,
                    },  # Default
                    "limits": {},
                }
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.show(style="pretty")

            # Should still work even with defaults
            result = output.getvalue()
            assert "normal" in result

    def test_show_with_non_dict_nested_value(self):
        """Test show with non-dict value in nested path."""
        mock_data = {
            "qos": [
                {
                    "name": "test",
                    "id": 1,
                    "description": "",
                    "priority": {"set": False},
                    "flags": [],
                    "preempt": {"mode": [], "list": []},
                    "limits": {
                        "max": {
                            # Non-dict value where dict is expected
                            "wall_clock": "invalid",
                        }
                    },
                }
            ]
        }
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                Qos.show(style="pretty")

            # Should still work with invalid nested data
            result = output.getvalue()
            assert "test" in result


class TestQosPrepareTemplateData:
    """Tests for Qos._prepare_template_data method."""

    def test_prepare_basic_data(self):
        """Test preparing basic QoS data."""
        qos = {
            "name": "normal",
            "id": 1,
            "description": "Normal QoS",
        }
        result = Qos._prepare_template_data(qos)
        assert result["name"] == "normal"
        assert result["id"] == 1
        assert result["description"] == "Normal QoS"

    def test_prepare_priority_set(self):
        """Test preparing priority when set."""
        qos = {
            "name": "high",
            "priority": {"set": True, "number": 100},
        }
        result = Qos._prepare_template_data(qos)
        assert result["priority"] == 100

    def test_prepare_priority_not_set(self):
        """Test preparing priority when not set."""
        qos = {
            "name": "normal",
            "priority": {"set": False},
        }
        result = Qos._prepare_template_data(qos)
        assert result["priority"] == "-"

    def test_prepare_usage_factor(self):
        """Test preparing usage_factor."""
        qos = {
            "name": "normal",
            "usage_factor": {"set": True, "number": 2.0},
        }
        result = Qos._prepare_template_data(qos)
        assert result["usage_factor"] == 2.0

    def test_prepare_flags(self):
        """Test preparing flags list."""
        qos = {
            "name": "normal",
            "flags": ["FLAG1", "FLAG2"],
        }
        result = Qos._prepare_template_data(qos)
        assert result["flags"] == "FLAG1,FLAG2"

    def test_prepare_empty_flags(self):
        """Test preparing empty flags list."""
        qos = {
            "name": "normal",
            "flags": [],
        }
        result = Qos._prepare_template_data(qos)
        assert result["flags"] == "-"

    def test_prepare_preempt_mode(self):
        """Test preparing preempt mode."""
        qos = {
            "name": "high",
            "preempt": {"mode": ["SUSPEND", "CANCEL"], "list": []},
        }
        result = Qos._prepare_template_data(qos)
        assert result["preempt_mode"] == "SUSPEND,CANCEL"

    def test_prepare_max_jobs_per_user(self):
        """Test preparing max jobs per user."""
        qos = {
            "name": "normal",
            "limits": {
                "max": {
                    "jobs": {
                        "per": {"user": {"set": True, "number": 10}}
                    }
                }
            },
        }
        result = Qos._prepare_template_data(qos)
        assert result["max_jobs_per_user"] == 10

    def test_prepare_max_wall_time(self):
        """Test preparing max wall time."""
        qos = {
            "name": "normal",
            "limits": {
                "max": {
                    "wall_clock": {
                        "per": {"job": {"set": True, "number": 7200}}
                    }
                }
            },
        }
        result = Qos._prepare_template_data(qos)
        assert result["max_wall"] == 7200

    def test_prepare_tres_per_job(self):
        """Test preparing TRES per job."""
        qos = {
            "name": "gpu",
            "limits": {
                "max": {
                    "tres": {
                        "per": {
                            "job": [
                                {"name": "cpu", "count": 32},
                                {"type": "gpu", "count": 2},
                            ]
                        }
                    }
                }
            },
        }
        result = Qos._prepare_template_data(qos)
        assert "cpu=32" in result["max_tres_per_job"]

    def test_prepare_tres_empty(self):
        """Test preparing empty TRES."""
        qos = {
            "name": "normal",
            "limits": {"max": {"tres": {"per": {"job": []}}}},
        }
        result = Qos._prepare_template_data(qos)
        assert result["max_tres_per_job"] == "-"


class TestQosInheritance:
    """Tests for Qos class inheritance."""

    def test_qos_inherits_from_base_resource(self):
        """Test that Qos inherits from BaseSlurmResource."""
        from slurm_cli.utils.base_resource import BaseSlurmResource

        assert issubclass(Qos, BaseSlurmResource)

    def test_qos_has_required_methods(self):
        """Test that Qos has all required methods."""
        assert hasattr(Qos, "create")
        assert hasattr(Qos, "update")
        assert hasattr(Qos, "delete")
        assert hasattr(Qos, "show")
        assert hasattr(Qos, "_prepare_template_data")
        assert callable(Qos.create)
        assert callable(Qos.update)
        assert callable(Qos.delete)
        assert callable(Qos.show)
        assert callable(Qos._prepare_template_data)
