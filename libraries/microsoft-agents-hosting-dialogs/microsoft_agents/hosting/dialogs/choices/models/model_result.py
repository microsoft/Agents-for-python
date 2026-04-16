# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass
from typing import Any

@dataclass
class ModelResult:
    """Contains recognition result information."""

    text: str
    start: int
    end: int
    type_name: str
    resolution: Any