# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core import UserState

from microsoft_agents.hosting.dialogs.memory import scope_path
from .bot_state_memory_scope import BotStateMemoryScope


class UserMemoryScope(BotStateMemoryScope):
    def __init__(self):
        super().__init__(UserState, scope_path.USER)
