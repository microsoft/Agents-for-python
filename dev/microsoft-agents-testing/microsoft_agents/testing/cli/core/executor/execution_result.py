# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Execution result container for CLI operations."""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ExecutionResult:
    """Container for the result of an async execution.
    
    Attributes:
        exe_id: Unique identifier for this execution.
        start_time: Unix timestamp when execution started.
        end_time: Unix timestamp when execution completed.
        result: The return value if successful, None otherwise.
        error: The exception if failed, None otherwise.
    """

    exe_id: int
    start_time: float
    end_time: float
    result: Any = None
    error: Optional[Exception] = None

    @property
    def success(self) -> bool:
        """Whether the execution completed without error."""
        return self.error is None

    @property
    def duration(self) -> float:
        """Duration of the execution in seconds."""
        return self.end_time - self.start_time

    def __repr__(self) -> str:
        status = "success" if self.success else f"error: {self.error}"
        return f"ExecutionResult(id={self.exe_id}, duration={self.duration:.3f}s, {status})"
