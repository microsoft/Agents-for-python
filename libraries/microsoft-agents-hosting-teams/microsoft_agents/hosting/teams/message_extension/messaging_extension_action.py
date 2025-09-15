from typing import Optional, TypeVar, Literal, Union

from microsoft_agents.activity import (
    Activity,
    AgentsModel
)

from ..message_actions_payload import MessageActionsPayload
from ..task_module import TaskModuleRequest

# this seems dubious
CommandContext = TypeVar(
    "CommandContext", bound=Literal["compose", "commandBox", "messagePreview"]
)

MessagePreviewActionType = TypeVar(
    "MessagePreviewActionType", bound=Literal["edit", "send"]
)

class MessagingExtensionAction(TaskModuleRequest):
    command_id: Optional[str] = None
    command_context: Optional[CommandContext] = None
    message_preview_action: Optional[MessagePreviewActionType] = None
    activity_preview: Optional[Activity] = None
    message_payload: Optional[MessageActionsPayload] = None