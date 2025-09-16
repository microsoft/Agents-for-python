from typing import (
    Optional,
    Any,
    Union,
    Literal,
    TypeVar
)

from microsoft_agents.activity import AgentsModel, Attachment

MessagePreviewType = TypeVar("MessagePreviewType", bound=Literal["message", "continue"])

class TaskModuleResponseBase(AgentsModel):
    type: Optional[MessagePreviewType] = None

class TaskModuleTaskInfo(AgentsModel):
    title: Optional[str] = None
    height: Optional[Union[int, Literal["small", "medium", "large"]]] = None
    width: Optional[Union[int, Literal["small", "medium", "large"]]] = None
    url: Optional[str] = None
    card: Optional[Attachment] = None
    fallback_url: Optional[str] = None
    completion_agent_id: Optional[str] = None

class TaskModuleContinueResponse(TaskModuleResponseBase):
    value: Optional[TaskModuleTaskInfo] = None

class TaskModuleMessageResponse(TaskModuleResponseBase):
    value: Optional[str] = None

class TaskModuleRequestContext(AgentsModel):
    theme: Optional[str] = None

class TaskModuleRequest(AgentsModel):
    data: Optional[Any] = None
    context: Optional[TaskModuleRequestContext] = None
    type: Optional[Any] = None # TabEntityContext -> TODO

class TaskModuleResponse(AgentsModel):
    task: Optional[Union[TaskModuleContinueResponse, TaskModuleMessageResponse]] = None
    cache_info: Optional[Any] = None