# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass
from typing import Any

from .dialog_turn_status import DialogTurnStatus


@dataclass
class DialogTurnResult:
    """
    Result returned to the caller of one of the various stack manipulation methods.
    """

    status: DialogTurnStatus
    result: Any = None
