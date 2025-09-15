from microsoft_agents.activity import AgentsModel

from ..task_module import (
    TaskModuleContinueResponse,
    TaskModuleMessageResponse
)
from .messaging_extension_result import MessagingExtensionResult

class MessagingExtensionActionResponse(AgentsModel):
    task: Optional[Union[TaskModuleContinueResponse, TaskModuleMessageResponse]] = None
    compose_extension: Optional[MessagingExtensionResult] = None
    cache_info: Optional[Any] = None # robrandao: TODO