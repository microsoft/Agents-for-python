# test_thread_executor.py
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
import asyncio
import time
import threading
from unittest.mock import patch, MagicMock

from microsoft_agents.testing.cli.common.executor import (
    ThreadExecutor,
    ExecutionResult,
)


class TestThreadExecutor:
    """Tests for ThreadExecutor class."""

    @pytest.fixture
    def executor(self):
        """Create a ThreadExecutor instance for testing."""
        return ThreadExecutor()

    def test_initialization(self, executor):
        """Test that ThreadExecutor can be instantiated."""
        assert executor is not None
        assert isinstance(executor, ThreadExecutor)

    def test_run_with_single_worker(self, executor):
        """Test run method with a single worker thread."""
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
        """Test run method with multiple worker threads."""
        call_count = 0
        lock = threading.Lock()

        async def test_func():
            nonlocal call_count
            with lock:
                call_count += 1
                current = call_count
            return f"result_{current}"

        num_workers = 5
        results = executor.run(test_func, num_workers=num_workers)

        assert len(results) == num_workers
        assert all(isinstance(r, ExecutionResult) for r in results)
        assert all(r.success for r in results)
        # Check that exe_ids are present
        exe_ids = [r.exe_id for r in results]
        assert len(exe_ids) == num_workers
        assert all(0 <= id < num_workers for id in exe_ids)

    def test_run_with_failing_function(self, executor):
        """Test run method when the function raises an exception."""
        test_error = ValueError("test error")

        async def failing_func():
            raise test_error

        results = executor.run(failing_func, num_workers=1)

        assert len(results) == 1
        assert results[0].success is False
        assert isinstance(results[0].error, ValueError)
        assert str(results[0].error) == "test error"
        assert results[0].result is None

    def test_run_with_mixed_success_and_failure(self, executor):
        """Test run with some workers succeeding and some failing."""
        call_count = 0
        lock = threading.Lock()

        async def mixed_func():
            nonlocal call_count
            with lock:
                call_count += 1
                current = call_count
            if current % 2 == 0:
                raise ValueError(f"Error on call {current}")
            return f"success_{current}"

        results = executor.run(mixed_func, num_workers=6)

        assert len(results) == 6
        success_count = sum(1 for r in results if r.success)
        failure_count = sum(1 for r in results if not r.success)
        # Should have both successes and failures
        assert success_count == 3
        assert failure_count == 3

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

        with pytest.raises(ValueError):
            executor.run(test_func, num_workers=0)

    def test_run_with_large_number_of_workers(self, executor):
        """Test run with a large number of concurrent worker threads."""
        counter = 0
        lock = threading.Lock()

        async def counting_func():
            nonlocal counter
            with lock:
                counter += 1
                current = counter
            await asyncio.sleep(0.001)
            return current

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

    def test_run_uses_thread_pool_executor(self, executor):
        """Test that run uses ThreadPoolExecutor."""
        async def test_func():
            return threading.current_thread().name

        results = executor.run(test_func, num_workers=3)

        assert len(results) == 3
        # Thread names should indicate they're from ThreadPoolExecutor
        thread_names = [r.result for r in results]
        assert all(isinstance(name, str) for name in thread_names)

    def test_run_execution_ids_are_assigned(self, executor):
        """Test that execution IDs are assigned correctly."""
        async def test_func():
            return "result"

        results = executor.run(test_func, num_workers=10)

        exe_ids = sorted([r.exe_id for r in results])
        assert exe_ids == list(range(10))

    def test_concurrent_execution_performance(self, executor):
        """Test that concurrent execution using threads is actually concurrent."""
        async def sleep_func():
            await asyncio.sleep(0.1)
            return "done"

        start = time.time()
        results = executor.run(sleep_func, num_workers=5)
        duration = time.time() - start

        # If truly concurrent, 5 tasks sleeping 0.1s should take ~0.1s, not 0.5s
        assert duration < 0.5  # Give margin for thread overhead
        assert all(r.success for r in results)

    def test_thread_safety_with_shared_state(self, executor):
        """Test thread safety when accessing shared state."""
        shared_list = []
        lock = threading.Lock()

        async def append_func():
            with lock:
                current_len = len(shared_list)
                await asyncio.sleep(0.001)  # Simulate some async work
                shared_list.append(current_len)
            return current_len

        results = executor.run(append_func, num_workers=10)

        assert len(results) == 10
        assert all(r.success for r in results)
        assert len(shared_list) == 10
        # All appended values should be unique if thread-safe
        assert len(set(shared_list)) == 10

    def test_run_with_asyncio_operations(self, executor):
        """Test that async operations work correctly in threads."""
        async def async_operations():
            # Test various asyncio operations
            await asyncio.sleep(0.01)
            result = await asyncio.gather(
                asyncio.sleep(0.01, result="a"),
                asyncio.sleep(0.01, result="b"),
            )
            return result

        results = executor.run(async_operations, num_workers=3)

        assert len(results) == 3
        assert all(r.success for r in results)
        assert all(r.result == ["a", "b"] for r in results)

    def test_run_with_different_return_types(self, executor):
        """Test run with functions returning different types."""
        test_cases = [
            (lambda: 42, int),
            (lambda: "string", str),
            (lambda: [1, 2, 3], list),
            (lambda: {"key": "value"}, dict),
            (lambda: (1, 2), tuple),
            (lambda: True, bool),
            (lambda: 3.14, float),
        ]

        for func_body, expected_type in test_cases:
            async def async_wrapper():
                return func_body()

            results = executor.run(async_wrapper, num_workers=1)
            assert len(results) == 1
            assert results[0].success is True
            assert isinstance(results[0].result, expected_type)