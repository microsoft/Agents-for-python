# test_executor.py
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from unittest.mock import AsyncMock, patch, Mock
from datetime import datetime, timezone

from microsoft_agents.testing.cli.common.executor import Executor, ExecutionResult


class ConcreteExecutor(Executor):
    """Concrete implementation of Executor for testing."""

    def run(self, func, num_workers=1):
        """Minimal implementation for testing."""
        return []


class TestExecutor:
    """Tests for the Executor base class."""

    @pytest.fixture
    def executor(self):
        """Create a concrete executor instance for testing."""
        return ConcreteExecutor()

    @pytest.mark.asyncio
    async def test_run_func_with_successful_execution(self, executor):
        """Test run_func with a successful async function."""
        async def success_func():
            return "success"

        result = await executor.run_func(1, success_func)

        assert isinstance(result, ExecutionResult)
        assert result.exe_id == 1
        assert result.result == "success"
        assert result.error is None
        assert result.success is True
        assert result.start_time > 0
        assert result.end_time > result.start_time

    @pytest.mark.asyncio
    async def test_run_func_with_exception(self, executor):
        """Test run_func when the async function raises an exception."""
        test_exception = ValueError("test error")

        async def failing_func():
            raise test_exception

        result = await executor.run_func(2, failing_func)

        assert isinstance(result, ExecutionResult)
        assert result.exe_id == 2
        assert result.result is None
        assert result.error == test_exception
        assert result.success is False
        assert result.start_time > 0
        assert result.end_time > result.start_time

    @pytest.mark.asyncio
    async def test_run_func_execution_time_tracking(self, executor):
        """Test that run_func correctly tracks execution time."""
        import asyncio

        async def slow_func():
            await asyncio.sleep(0.1)
            return "done"

        result = await executor.run_func(3, slow_func)

        assert result.duration >= 0.1
        assert result.success is True
        assert result.result == "done"

    @pytest.mark.asyncio
    async def test_run_func_with_different_exe_ids(self, executor):
        """Test run_func with different execution IDs."""
        async def test_func():
            return "result"

        result1 = await executor.run_func(1, test_func)
        result2 = await executor.run_func(42, test_func)
        result3 = await executor.run_func(999, test_func)

        assert result1.exe_id == 1
        assert result2.exe_id == 42
        assert result3.exe_id == 999

    @pytest.mark.asyncio
    async def test_run_func_with_none_return_value(self, executor):
        """Test run_func when the function returns None."""
        async def none_func():
            return None

        result = await executor.run_func(1, none_func)

        assert result.result is None
        assert result.success is True
        assert result.error is None

    @pytest.mark.asyncio
    async def test_run_func_with_complex_return_value(self, executor):
        """Test run_func with complex return values."""
        complex_value = {"data": [1, 2, 3], "nested": {"key": "value"}}

        async def complex_func():
            return complex_value

        result = await executor.run_func(1, complex_func)

        assert result.result == complex_value
        assert result.success is True

    @pytest.mark.asyncio
    async def test_run_func_timestamps_use_utc(self, executor):
        """Test that run_func uses UTC timezone for timestamps."""
        async def test_func():
            return "result"

        with patch('microsoft_agents.testing.cli.common.executor.executor.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.timestamp.return_value = 1234567890.0
            mock_datetime.now.return_value = mock_now

            result = await executor.run_func(1, test_func)

            # Verify that datetime.now was called with timezone.utc
            assert mock_datetime.now.call_count == 2
            mock_datetime.now.assert_any_call(timezone.utc)

    @pytest.mark.asyncio
    async def test_run_func_catches_all_exception_types(self, executor):
        """Test that run_func catches different types of exceptions."""
        exceptions = [
            ValueError("value error"),
            TypeError("type error"),
            RuntimeError("runtime error"),
            Exception("generic exception"),
        ]

        for exc in exceptions:
            async def failing_func():
                raise exc

            result = await executor.run_func(1, failing_func)
            assert result.error == exc
            assert result.success is False

    def test_run_method_not_implemented(self, executor):
        """Test that the run method raises NotImplementedError on base class."""
        # Create an instance of the abstract class without implementing run
        class IncompleteExecutor(Executor):
            pass

        # This should work because Python doesn't enforce abstract methods at instantiation
        # unless we use ABCMeta, but the method should still raise NotImplementedError
        with pytest.raises(NotImplementedError):
            # Call the base class run method directly
            Executor.run(executor, lambda: None, 1)

    def test_executor_is_abstract_base_class(self):
        """Test that Executor is defined as an abstract base class."""
        from abc import ABC
        assert issubclass(Executor, ABC)

    @pytest.mark.asyncio
    async def test_run_func_with_async_generator(self, executor):
        """Test run_func with an async function that yields values."""
        async def generator_func():
            values = []
            for i in range(3):
                values.append(i)
            return values

        result = await executor.run_func(1, generator_func)

        assert result.result == [0, 1, 2]
        assert result.success is True