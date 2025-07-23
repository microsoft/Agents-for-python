# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from typing import List, Optional

from .messaging_extension_attachment import MessagingExtensionAttachment
from .messaging_extension_suggested_action import MessagingExtensionSuggestedAction
from ..activity import Activity


class MessagingExtensionResult(AgentsModel):
    """Messaging extension result.

    :param attachment_layout: Hint for how to deal with multiple attachments.
    :type attachment_layout: str
    :param type: The type of the result. Possible values include: 'result', 'auth', 'config', 'message', 'botMessagePreview'
    :type type: str
    :param attachments: (Only when type is result) Attachments
    :type attachments: List["MessagingExtensionAttachment"]
    :param suggested_actions: Suggested actions for the result.
    :type suggested_actions: Optional["MessagingExtensionSuggestedAction"]
    :param text: (Only when type is message) Text
    :type text: Optional[str]
    :param activity_preview: (Only when type is botMessagePreview) Message activity to preview
    :type activity_preview: Optional["Activity"]
    """

    attachment_layout: str = None
    type: str = None
    attachments: List[MessagingExtensionAttachment] = None
    suggested_actions: Optional[MessagingExtensionSuggestedAction] = None
    text: Optional[str] = None
    activity_preview: Optional["Activity"] = None
