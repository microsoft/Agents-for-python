# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass
from typing import Any


@dataclass
class DialogEvent:

    bubble: bool = False
    name: str = ""
    value: Any = None
