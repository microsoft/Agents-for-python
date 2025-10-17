# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
from typing import Callable, Awaitable, Any

from .executor import Executor
from .execution_result import ExecutionResult


class CoroutineExecutor(Executor):
    """An executor that runs asynchronous functions using asyncio."""

    def run(
        self, func: Callable[[], Awaitable[Any]], num_workers: int = 1
    ) -> list[ExecutionResult]:
        # """Run the given asynchronous function using the specified number of coroutines.

        # :param func: An asynchronous function to be executed.
        # :param num_workers: The number of coroutines to use.
        # """
        async def gather():
            return await asyncio.gather(
                *[self.run_func(i, func) for i in range(num_workers)]
            )

        return asyncio.run(gather())
