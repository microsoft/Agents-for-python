from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel
from pydantic.types import PositiveInt

from microsoft.agents.activity import Activity, SignInResource, TokenResponse
from microsoft.agents.hosting.core.storage import StoreItem

class FlowStateTag(Enum):
    BEGIN = "begin"
    CONTINUE = "continue"
    NOT_STARTED = "not_started"
    FAILURE = "failure"
    COMPLETE = "complete"

class FlowErrorTag(Enum):
    NONE = "none"
    MAGIC_FORMAT = "magic_format"
    MAGIC_CODE = "magic_code"
    OTHER = "OTHER"

class FlowState(BaseModel, StoreItem):

    flow_id: str = ""
    flow_started: bool = False
    user_token: str = ""
    expires_at: float = 0
    abs_oauth_connection_name: Optional[str] = None
    continuation_activity: Optional[Activity] = None
    attempts_remaining: int = 3
    tag: FlowStateTag = FlowStateTag.NOT_STARTED

    def refresh(self) -> None:
        if self.is_expired() or self.reached_max_attempts():
            self.tag = FlowStateTag.FAILURE

    def store_item_to_json(self) -> dict:
        return self.model_dump()

    @staticmethod
    def from_json_to_store_item(json_data: dict) -> "FlowState":
        return FlowState.model_validate(json_data)
    
    def is_expired(self) -> bool:
        return datetime.now().timestamp() >= self.expires_at

    def reached_max_attempts(self) -> bool:
        return self.attempts_remaining <= 0
    
    def is_active(self) -> bool:
        return not self.is_expired() and not self.reached_max_attempts() and self.tag in [FlowStateTag.BEGIN, FlowStateTag.CONTINUE]
    
class FlowResponse(BaseModel):

    flow_state: FlowState = FlowState()
    flow_error_tag: FlowErrorTag = FlowErrorTag.NONE
    token_response: Optional[TokenResponse] = None
    sign_in_resource: Optional[SignInResource] = None
