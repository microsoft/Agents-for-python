# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass, field

from microsoft_agents.activity import Activity

from .models.dialog_turn_result import DialogTurnResult
from .persisted_state import PersistedState

@dataclass
class DialogManagerResult:

    turn_result: DialogTurnResult | None = None
    activities: list[Activity] = field(default_factory=list)
    persisted_state: PersistedState | None = None