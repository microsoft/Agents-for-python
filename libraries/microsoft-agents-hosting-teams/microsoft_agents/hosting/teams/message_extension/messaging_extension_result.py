from typing import List, Optional, TypeVar, Literal

from microsoft_agents.activity import AgentsModel, Activity

from .messaging_extension_attachment import MessagingExtensionAttachment
from .messaging_extension_suggested_action import MessagingExtensionSuggestedAction

AttachmentLayout = TypeVar("AttachmentLayout", bound=Literal["list", "grid"])

MessagingExtensionResultType = TypeVar(
    "MessagingExtensionResultType",
    bound=Literal["result", "auth", "config", "message", "botMessagePreview", "silentAuth"])

class MessagingExtensionResult(AgentsModel):
    attachment_layout: Optional[AttachmentLayout] = None
    type: Optional[MessagingExtensionResultType] = None
    attachments: Optional[list[MessagingExtensionAttachment]] = None
    suggested_actions: Optional[list[MessagingExtensionSuggestedAction]] = None # robrandao: TODO -> js bug?
    text: Optional[str] = None
    activity_preview: Optional[Activity] = None 
