# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
import asyncio
from typing import Callable, Awaitable, Any
from concurrent.futures import ThreadPoolExecutor

from .executor import Executor
from .execution_result import ExecutionResult

logger = logging.getLogger(__name__)


class ThreadExecutor(Executor):
    """An executor that runs asynchronous functions using multiple threads."""

    def run(
        self, func: Callable[[], Awaitable[Any]], num_workers: int = 1
    ) -> list[ExecutionResult]:
        """Run the given asynchronous function using the specified number of threads.

        :param func: An asynchronous function to be executed.
        :param num_workers: The number of concurrent threads to use.
        """

        def _func(exe_id: int) -> ExecutionResult:
            return asyncio.run(self.run_func(exe_id, func))

        results: list[ExecutionResult] = []

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(_func, i) for i in range(num_workers)]
            for future in futures:
                results.append(future.result())

        return results
