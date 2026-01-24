# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Asyncio-based concurrent executor."""

import asyncio
from typing import Awaitable, Callable, Any

from .executor import Executor
from .execution_result import ExecutionResult


class CoroutineExecutor(Executor):
    """Executor that runs functions concurrently using asyncio.
    
    Best suited for I/O-bound operations where you want to maximize
    concurrent network requests or file operations.
    
    Example:
        >>> executor = CoroutineExecutor()
        >>> results = executor.run(my_async_func, num_workers=10)
    """

    def run(
        self, 
        func: Callable[[], Awaitable[Any]], 
        num_workers: int = 1,
    ) -> list[ExecutionResult]:
        """Run the function concurrently with asyncio.gather.
        
        Args:
            func: Async function to execute.
            num_workers: Number of concurrent coroutines to spawn.
            
        Returns:
            List of ExecutionResult objects.
        """
        return asyncio.run(self._run_async(func, num_workers))

    async def _run_async(
        self, 
        func: Callable[[], Awaitable[Any]], 
        num_workers: int,
    ) -> list[ExecutionResult]:
        """Internal async implementation."""
        tasks = [
            self.run_func(exe_id=i, func=func) 
            for i in range(num_workers)
        ]
        return await asyncio.gather(*tasks)
