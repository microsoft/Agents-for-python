# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from microsoft_agents.activity import Activity

from ..storage import StoreItem


class _FlowStateTag(Enum):
    """Represents the top-level state of an OAuthFlow

    For instance, a flow can arrive at an error, but its
    broader state may still be CONTINUE if the flow can
    still progress
    """

    BEGIN = "begin"
    CONTINUE = "continue"
    NOT_STARTED = "not_started"
    FAILURE = "failure"
    COMPLETE = "complete"


class _FlowErrorTag(Enum):
    """Represents the various error states that can occur during an OAuthFlow"""

    NONE = "none"
    MAGIC_FORMAT = "magic_format"
    MAGIC_CODE_INCORRECT = "magic_code_incorrect"
    OTHER = "other"


class _FlowState(BaseModel, StoreItem):
    """Represents the state of an OAuthFlow"""

    channel_id: str = ""
    user_id: str = ""
    ms_app_id: str = ""
    connection: str = ""
    auth_handler_id: str = ""

    expiration: float = 0
    continuation_activity: Optional[Activity] = None
    attempts_remaining: int = 0
    tag: _FlowStateTag = _FlowStateTag.NOT_STARTED

    def store_item_to_json(self) -> dict:
        return self.model_dump(mode="json", exclude_unset=True, by_alias=True)

    @staticmethod
    def from_json_to_store_item(json_data: dict) -> _FlowState:
        return _FlowState.model_validate(json_data)

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc).timestamp() >= self.expiration

    def reached_max_attempts(self) -> bool:
        return self.attempts_remaining <= 0

    def is_active(self) -> bool:
        return (
            not self.is_expired()
            and not self.reached_max_attempts()
            and self.tag in [_FlowStateTag.BEGIN, _FlowStateTag.CONTINUE]
        )

    def refresh(self):
        if (
            self.tag
            in [_FlowStateTag.BEGIN, _FlowStateTag.CONTINUE, _FlowStateTag.COMPLETE]
            and self.is_expired()
        ):
            self.tag = _FlowStateTag.NOT_STARTED
