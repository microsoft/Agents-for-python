import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel
from pydantic.types import PositiveInt

from microsoft.agents.activity import Activity
from microsoft.agents.hosting.core import StoreItem

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

class FlowState(BaseModel, StoreItem):

    flow_id: NonEmptyString
    flow_started: bool = False
    user_token: str = ""
    expires: float = 0
    abs_oauth_connection_name: Optional[str] = None
    continuation_activity: Optional[Activity] = None
    attempts_remaining: PositiveInt = 3
    tag: FlowStateTag = FlowStateTag.INACTIVE

    def refresh(self) -> None:
        if self.is_expired() or self.reached_max_retries():
            self.tag = FlowStateTag.FAILURE

    def store_item_to_json(self) -> dict:
        return self.model_dump()

    @staticmethod
    def from_json_to_store_item(json_data: dict) -> "FlowState":
        return FlowState.model_validate(json_data)
    
    def is_expired(self) -> bool:
        return datetime.now().timestamp() >= self.flow_expires
    
    def reached_max_attempts(self) -> bool:
        return self.attempts_remaining <= 0
    
    def is_active(self) -> bool:
        return not self.is_expired() and not self.reached_max_retries() and self.tag in [FlowStateTag.BEGIN, FlowStateTag.CONTINUE]
    
class FlowResponse(BaseModel):

    flow_data: FlowData
    flow_error_tag: FlowErrorTag = FlowErrorTag.NONE
    token_response: Optional[TokenResponse] = None
    sign_in_resource: Optional[SignInResource] = None
