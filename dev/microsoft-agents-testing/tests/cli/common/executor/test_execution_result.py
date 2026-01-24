# test_execution_result.py
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.testing.cli.common.executor import ExecutionResult


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""

    def test_initialization_with_success(self):
        """Test creating an ExecutionResult with a successful result."""
        result = ExecutionResult(
            exe_id=1,
            start_time=100.0,
            end_time=105.0,
            result="success_value",
        )
        assert result.exe_id == 1
        assert result.start_time == 100.0
        assert result.end_time == 105.0
        assert result.result == "success_value"
        assert result.error is None

    def test_initialization_with_error(self):
        """Test creating an ExecutionResult with an error."""
        test_error = ValueError("test error")
        result = ExecutionResult(
            exe_id=2,
            start_time=100.0,
            end_time=105.0,
            error=test_error,
        )
        assert result.exe_id == 2
        assert result.start_time == 100.0
        assert result.end_time == 105.0
        assert result.result is None
        assert result.error == test_error

    def test_success_property_returns_true_when_no_error(self):
        """Test that success property returns True when error is None."""
        result = ExecutionResult(
            exe_id=1,
            start_time=100.0,
            end_time=105.0,
            result="success",
        )
        assert result.success is True

    def test_success_property_returns_false_when_error_exists(self):
        """Test that success property returns False when error exists."""
        result = ExecutionResult(
            exe_id=1,
            start_time=100.0,
            end_time=105.0,
            error=Exception("error"),
        )
        assert result.success is False

    def test_duration_property_calculates_correctly(self):
        """Test that duration property calculates the correct time difference."""
        result = ExecutionResult(
            exe_id=1,
            start_time=100.5,
            end_time=105.7,
            result="test",
        )
        assert result.duration == pytest.approx(5.2)

    def test_duration_property_with_zero_duration(self):
        """Test duration property when start and end times are equal."""
        result = ExecutionResult(
            exe_id=1,
            start_time=100.0,
            end_time=100.0,
            result="test",
        )
        assert result.duration == 0.0

    def test_duration_property_with_fractional_seconds(self):
        """Test duration with fractional seconds."""
        result = ExecutionResult(
            exe_id=1,
            start_time=100.123456,
            end_time=100.987654,
            result="test",
        )
        expected_duration = 100.987654 - 100.123456
        assert result.duration == pytest.approx(expected_duration)

    def test_result_with_none_values(self):
        """Test ExecutionResult with None as result value."""
        result = ExecutionResult(
            exe_id=1,
            start_time=100.0,
            end_time=105.0,
            result=None,
        )
        assert result.result is None
        assert result.success is True  # No error means success

    def test_result_with_complex_object(self):
        """Test ExecutionResult with complex object as result."""
        complex_result = {"key": "value", "nested": {"data": [1, 2, 3]}}
        result = ExecutionResult(
            exe_id=1,
            start_time=100.0,
            end_time=105.0,
            result=complex_result,
        )
        assert result.result == complex_result
        assert result.success is True

    def test_multiple_execution_results_different_ids(self):
        """Test creating multiple ExecutionResults with different IDs."""
        result1 = ExecutionResult(exe_id=1, start_time=100.0, end_time=105.0)
        result2 = ExecutionResult(exe_id=2, start_time=200.0, end_time=210.0)
        result3 = ExecutionResult(exe_id=3, start_time=300.0, end_time=315.0)

        assert result1.exe_id == 1
        assert result2.exe_id == 2
        assert result3.exe_id == 3
        assert result1.duration == 5.0
        assert result2.duration == 10.0
        assert result3.duration == 15.0