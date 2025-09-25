from __future__ import annotations

from typing import Optional

from microsoft_agents.activity import Activity

from ...storage._type_aliases import JSON
from ...storage import StoreItem

class SignInState(StoreItem):

    def __init__(self, data: Optional[JSON] = None, continuation_activity: Optional[Activity] = None) -> None:
        self.tokens = data or {}
        self.continuation_activity = continuation_activity

    def store_item_to_json(self) -> JSON:
        return {
            "tokens": self.tokens,
            "continuation_activity": self.continuation_activity,
        }
    
    @staticmethod
    def from_json_to_store_item(json_data: JSON) -> SignInState:
        return SignInState(json_data["tokens"], json_data.get("continuation_activity"))
    
    def active_handler(self) -> "":
        for handler_id, token in self.tokens.items():
            if not token:
                return handler_id
        return ""