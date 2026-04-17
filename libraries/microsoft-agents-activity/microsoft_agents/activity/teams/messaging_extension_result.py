# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel

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
    :type attachments: list[MessagingExtensionAttachment]
    :param suggested_actions: Suggested actions for the result.
    :type suggested_actions: MessagingExtensionSuggestedAction | None
    :param text: (Only when type is message) Text
    :type text: str | None
    :param activity_preview: (Only when type is botMessagePreview) Message activity to preview
    :type activity_preview: Activity | None
    """

    attachment_layout: str = None
    type: str = None
    attachments: list[MessagingExtensionAttachment] = None
    suggested_actions: MessagingExtensionSuggestedAction | None = None
    text: str | None = None
    activity_preview: Activity | None = None
