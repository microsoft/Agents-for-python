# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Thread-based concurrent executor."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Awaitable, Callable, Any

from .executor import Executor
from .execution_result import ExecutionResult


class ThreadExecutor(Executor):
    """Executor that runs functions concurrently using threads.
    
    Each worker gets its own thread and event loop. Useful when you need
    isolation between workers or when working with thread-local resources.
    
    Example:
        >>> executor = ThreadExecutor()
        >>> results = executor.run(my_async_func, num_workers=4)
    """

    def run(
        self, 
        func: Callable[[], Awaitable[Any]], 
        num_workers: int = 1,
    ) -> list[ExecutionResult]:
        """Run the function in separate threads.
        
        Args:
            func: Async function to execute.
            num_workers: Number of threads to spawn.
            
        Returns:
            List of ExecutionResult objects.
        """
        with ThreadPoolExecutor(max_workers=num_workers) as pool:
            futures = [
                pool.submit(self._run_in_thread, exe_id=i, func=func)
                for i in range(num_workers)
            ]
            return [future.result() for future in futures]

    def _run_in_thread(
        self, 
        exe_id: int, 
        func: Callable[[], Awaitable[Any]],
    ) -> ExecutionResult:
        """Run the async function in a new event loop within this thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.run_func(exe_id, func))
        finally:
            loop.close()
