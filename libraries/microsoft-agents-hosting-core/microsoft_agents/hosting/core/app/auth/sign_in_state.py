from __future__ import annotations

from typing import Optional

from ...storage._type_aliases import JSON
from ...storage import StoreItem

class SignInState(StoreItem):

    def __init__(self, data: Optional[JSON] = None):
        self.tokens = data or {}

    def store_item_to_json(self) -> JSON:
        return self.tokens
    
    @staticmethod
    def from_json_to_store_item(json_data: JSON) -> SignInState:
        return SignInState(json_data)
    
    def active_handler(self) -> Optional[str]:
        for handler_id, token in self.tokens.items():
            if not token:
                return handler_id