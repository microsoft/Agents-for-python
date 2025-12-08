# test_coroutine_executor.py
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
import asyncio
from unittest.mock import patch, AsyncMock

from microsoft_agents.testing.cli.common.executor import (
    CoroutineExecutor,
    ExecutionResult,
)


class TestCoroutineExecutor:
    """Tests for CoroutineExecutor class."""

    @pytest.fixture
    def executor(self):
        """Create a CoroutineExecutor instance for testing."""
        return CoroutineExecutor()

    def test_initialization(self, executor):
        """Test that CoroutineExecutor can be instantiated."""
        assert executor is not None
        assert isinstance(executor, CoroutineExecutor)

    def test_run_with_single_worker(self, executor):
        """Test run method with a single worker."""
        call_count = 0

        async def test_func():
            nonlocal call_count
            call_count += 1
            return f"result_{call_count}"

        results = executor.run(test_func, num_workers=1)

        assert len(results) == 1
        assert all(isinstance(r, ExecutionResult) for r in results)
        assert results[0].result == "result_1"
        assert results[0].success is True
        assert results[0].exe_id == 0

    def test_run_with_multiple_workers(self, executor):
        """Test run method with multiple workers."""
        call_count = 0

        async def test_func():
            nonlocal call_count
            call_count += 1
            return f"result_{call_count}"

        num_workers = 5
        results = executor.run(test_func, num_workers=num_workers)

        assert len(results) == num_workers
        assert all(isinstance(r, ExecutionResult) for r in results)
        assert all(r.success for r in results)
        # Check that exe_ids are sequential
        assert [r.exe_id for r in results] == list(range(num_workers))

    def test_run_with_failing_function(self, executor):
        """Test run method when the function raises an exception."""
        test_error = ValueError("test error")

        async def failing_func():
            raise test_error

        results = executor.run(failing_func, num_workers=1)

        assert len(results) == 1
        assert results[0].success is False
        assert results[0].error == test_error
        assert results[0].result is None

    def test_run_with_mixed_success_and_failure(self, executor):
        """Test run with some workers succeeding and some failing."""
        call_count = 0

        async def mixed_func():
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                raise ValueError(f"Error on call {call_count}")
            return f"success_{call_count}"

        results = executor.run(mixed_func, num_workers=4)

        assert len(results) == 4
        success_count = sum(1 for r in results if r.success)
        failure_count = sum(1 for r in results if not r.success)
        # Due to async nature, we just check that we have both successes and failures
        assert success_count > 0
        assert failure_count > 0

    def test_run_with_async_delay(self, executor):
        """Test run with async functions that have delays."""
        async def delayed_func():
            await asyncio.sleep(0.01)
            return "completed"

        results = executor.run(delayed_func, num_workers=3)

        assert len(results) == 3
        assert all(r.success for r in results)
        assert all(r.result == "completed" for r in results)
        assert all(r.duration >= 0.01 for r in results)

    def test_run_records_execution_times(self, executor):
        """Test that run properly records execution times."""
        async def test_func():
            await asyncio.sleep(0.05)
            return "done"

        results = executor.run(test_func, num_workers=2)

        for result in results:
            assert result.start_time > 0
            assert result.end_time > result.start_time
            assert result.duration >= 0.05

    def test_run_with_zero_workers(self, executor):
        """Test run with zero workers."""
        async def test_func():
            return "result"

        results = executor.run(test_func, num_workers=0)

        assert len(results) == 0
        assert results == []

    def test_run_with_large_number_of_workers(self, executor):
        """Test run with a large number of concurrent workers."""
        counter = 0

        async def counting_func():
            nonlocal counter
            counter += 1
            await asyncio.sleep(0.001)
            return counter

        num_workers = 50
        results = executor.run(counting_func, num_workers=num_workers)

        assert len(results) == num_workers
        assert all(r.success for r in results)
        assert all(isinstance(r.result, int) for r in results)

    def test_run_with_function_returning_none(self, executor):
        """Test run when the function returns None."""
        async def none_func():
            return None

        results = executor.run(none_func, num_workers=2)

        assert len(results) == 2
        assert all(r.success for r in results)
        assert all(r.result is None for r in results)

    def test_run_with_function_returning_complex_objects(self, executor):
        """Test run with functions returning complex objects."""
        async def complex_func():
            return {
                "list": [1, 2, 3],
                "dict": {"nested": "value"},
                "tuple": (4, 5, 6),
            }

        results = executor.run(complex_func, num_workers=3)

        assert len(results) == 3
        assert all(r.success for r in results)
        assert all(isinstance(r.result, dict) for r in results)
        assert all("list" in r.result for r in results)

    def test_run_preserves_exception_details(self, executor):
        """Test that run preserves exception details."""
        class CustomException(Exception):
            def __init__(self, message, code):
                super().__init__(message)
                self.code = code

        async def custom_error_func():
            raise CustomException("Custom error message", 42)

        results = executor.run(custom_error_func, num_workers=1)

        assert len(results) == 1
        assert results[0].success is False
        assert isinstance(results[0].error, CustomException)
        assert str(results[0].error) == "Custom error message"
        assert results[0].error.code == 42

    def test_run_execution_ids_are_sequential(self, executor):
        """Test that execution IDs are assigned sequentially."""
        async def test_func():
            return "result"

        results = executor.run(test_func, num_workers=10)

        exe_ids = [r.exe_id for r in results]
        assert exe_ids == list(range(10))

    def test_concurrent_execution_performance(self, executor):
        """Test that concurrent execution is actually concurrent."""
        import time

        async def sleep_func():
            await asyncio.sleep(0.1)
            return "done"

        start = time.time()
        results = executor.run(sleep_func, num_workers=5)
        duration = time.time() - start

        # If truly concurrent, 5 tasks sleeping 0.1s should take ~0.1s, not 0.5s
        assert duration < 0.3  # Give some margin for overhead
        assert all(r.success for r in results)