"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from microsoft_agents.activity import Activity

from ...storage._type_aliases import JSON
from ...storage import StoreItem


class _SignInState(BaseModel, StoreItem):
    """Store item for sign-in state, including tokens and continuation activity.

    Used to cache tokens and keep track of activities during single and
    multi-turn sign-in flows.
    """

    active_handler_id: str
    continuation_activity: Optional[Activity] = None

    def store_item_to_json(self) -> JSON:
        return self.model_dump(mode="json", exclude_unset=True, by_alias=True)

    @staticmethod
    def from_json_to_store_item(json_data: JSON) -> _SignInState:
        return _SignInState.model_validate(json_data)
