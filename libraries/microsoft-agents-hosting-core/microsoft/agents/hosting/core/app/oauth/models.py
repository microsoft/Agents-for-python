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

class FlowState(BaseModel, StoreItem):

    flow_started: bool = False
    user_token: str = ""
    flow_expires: float = 0
    abs_oauth_connection_name: Optional[str] = None
    continuation_activity: Optional[Activity] = None
    attempts_remaining: PositiveInt = 3
    tag: FlowStateTag = FlowStateTag.INACTIVE

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        if self.is_expired() or self.reached_max_retries():
            self.tag = FlowStateTag.FAILURE

    def store_item_to_json(self) -> dict:
        return self.model_dump()

    @staticmethod
    def from_json_to_store_item(json_data: dict) -> "FlowState":
        return FlowState.model_validate(json_data)
    
    def is_expired(self) -> bool:
        return datetime.now().timestamp() >= self.flow_expires
    
    def reached_max_retries(self) -> bool:
        return self.attempts_remaining <= 0
    
    def is_active(self) -> bool:
        return not self.is_expired() and not self.reached_max_retries() and self.tag in [FlowStateTag.BEGIN, FlowStateTag.CONTINUE]
    
class FlowResponse(BaseModel):

    flow_data: FlowData
    in_flow_activity: Activity
    token_response: Optional[TokenResponse] = None
