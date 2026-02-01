# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Execution utilities for running async operations.

Provides different execution strategies (coroutine-based, thread-based)
for running async functions with timing and error handling.
"""

from .execution_result import ExecutionResult
from .executor import Executor
from .coroutine_executor import CoroutineExecutor
from .thread_executor import ThreadExecutor

__all__ = [
    "ExecutionResult",
    "Executor",
    "CoroutineExecutor",
    "ThreadExecutor",
]
