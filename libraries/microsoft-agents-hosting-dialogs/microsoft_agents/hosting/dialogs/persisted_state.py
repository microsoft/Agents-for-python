# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any

from .persisted_state_keys import PersistedStateKeys

class PersistedState:
    def __init__(
        self,
        keys: PersistedStateKeys | None = None,
        data: dict[str, Any] | None = None
    ):
        if keys and data:
            self.user_state: dict[str, Any] = (
                data[keys.user_state] if keys.user_state in data else {}
            )
            self.conversation_state: dict[str, Any] = (
                data[keys.conversation_state] if keys.conversation_state in data else {}
            )
        else:
            self.user_state: dict[str, Any] = {}
            self.conversation_state: dict[str, Any] = {}