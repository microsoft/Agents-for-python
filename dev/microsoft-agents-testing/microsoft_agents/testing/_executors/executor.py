# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from datetime import datetime, timezone
from abc import ABC, abstractmethod
from typing import Callable, Awaitable, Any

from .execution_result import ExecutionResult


class Executor(ABC):
    """Protocol for executing asynchronous functions concurrently."""

    async def run_func(
        self, exe_id: int, func: Callable[[], Awaitable[Any]]
    ) -> ExecutionResult:
        """Run the given asynchronous function.

        :param exe_id: An identifier for the execution instance.
        :param func: An asynchronous function to be executed.
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
        self, func: Callable[[], Awaitable[Any]], num_workers: int = 1
    ) -> list[ExecutionResult]:
        """Run the given asynchronous function using the specified number of workers.

        :param func: An asynchronous function to be executed.
        :param num_workers: The number of concurrent workers to use.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
