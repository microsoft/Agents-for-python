# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Abstract base class for execution strategies."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Awaitable, Callable, Any

from .execution_result import ExecutionResult


class Executor(ABC):
    """Abstract base class for executing async functions.
    
    Provides a common interface for different execution strategies
    (threading, asyncio, etc.) with built-in timing and error handling.
    
    Subclasses must implement the `run` method.
    """

    async def run_func(
        self, 
        exe_id: int, 
        func: Callable[[], Awaitable[Any]],
    ) -> ExecutionResult:
        """Execute a single async function with timing and error capture.
        
        Args:
            exe_id: Identifier for this execution instance.
            func: Async function to execute.
            
        Returns:
            ExecutionResult containing timing info and result/error.
        """
        start_time = datetime.now(timezone.utc).timestamp()
        
        try:
            result = await func()
            return ExecutionResult(
                exe_id=exe_id,
                result=result,
                start_time=start_time,
                end_time=datetime.now(timezone.utc).timestamp(),
            )
        except Exception as e:  # pylint: disable=broad-except
            return ExecutionResult(
                exe_id=exe_id,
                error=e,
                start_time=start_time,
                end_time=datetime.now(timezone.utc).timestamp(),
            )

    @abstractmethod
    def run(
        self, 
        func: Callable[[], Awaitable[Any]], 
        num_workers: int = 1,
    ) -> list[ExecutionResult]:
        """Execute the function using the specified number of workers.
        
        Args:
            func: Async function to execute.
            num_workers: Number of concurrent workers.
            
        Returns:
            List of ExecutionResult objects, one per worker.
        """
        raise NotImplementedError("Subclasses must implement run()")
