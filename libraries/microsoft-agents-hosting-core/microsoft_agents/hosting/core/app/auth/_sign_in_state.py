"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from typing import Optional

from microsoft_agents.activity import Activity

from ...storage._type_aliases import JSON
from ...storage import StoreItem


class _SignInState(StoreItem):
    """Store item for sign-in state, including tokens and continuation activity.

    Used to cache tokens and keep track of activities during single and
    multi-turn sign-in flows.
    """

    def __init__(
        self,
        active_handler_id: str,
        continuation_activity: Optional[Activity] = None,
    ) -> None:
        self.active_handler_id = active_handler_id
        self.continuation_activity = continuation_activity

    def store_item_to_json(self) -> JSON:
        return {
            "active_handler_id": self.active_handler_id,
            "continuation_activity": self.continuation_activity,
        }

    @staticmethod
    def from_json_to_store_item(json_data: JSON) -> _SignInState:
        return _SignInState(
            json_data["active_handler_id"], json_data.get("continuation_activity")
        )
