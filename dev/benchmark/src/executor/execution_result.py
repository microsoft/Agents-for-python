# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Optional
from dataclasses import dataclass

@dataclass
class ExecutionResult:
    """Class to represent the result of an execution."""

    exe_id: int

    start_time: float
    end_time: float

    result: Any = None
    error: Optional[Exception] = None

    @property
    def success(self) -> bool:
        """Indicate whether the execution was successful."""
        return self.error is None

    @property
    def duration(self) -> float:
        """Calculate the duration of the execution, in seconds."""
        return self.end_time - self.start_time