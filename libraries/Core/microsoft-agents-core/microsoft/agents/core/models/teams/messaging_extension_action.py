from pydantic import BaseModel
from typing import List, Optional


class MessagingExtensionAction(BaseModel):
    """Messaging extension action.

    :param data: User input data. Free payload with key-value pairs.
    :type data: object
    :param context: Current user context, i.e., the current theme
    :type context: Optional["TaskModuleRequestContext"]
    :param command_id: Id of the command assigned by Bot
    :type command_id: str
    :param command_context: The context from which the command originates. Possible values include: 'message', 'compose', 'commandbox'
    :type command_context: str
    :param bot_message_preview_action: Bot message preview action taken by user. Possible values include: 'edit', 'send'
    :type bot_message_preview_action: str
    :param bot_activity_preview: List of bot activity previews.
    :type bot_activity_preview: List["Activity"]
    :param message_payload: Message content sent as part of the command request.
    :type message_payload: Optional["MessageActionsPayload"]
    """

    data: object
    context: Optional["TaskModuleRequestContext"]
    command_id: str
    command_context: str
    bot_message_preview_action: str
    bot_activity_preview: List["Activity"]
    message_payload: Optional["MessageActionsPayload"]
