# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from typing import Any, List

from .task_module_request_context import TaskModuleRequestContext
from .message_actions_payload import MessageActionsPayload
from ..activity import Activity


class MessagingExtensionAction(AgentsModel):
    """Messaging extension action.

    :param data: User input data. Free payload with key-value pairs.
    :type data: object
    :param context: Current user context, i.e., the current theme
    :type context: TaskModuleRequestContext
    :param command_id: Id of the command assigned by Bot
    :type command_id: str
    :param command_context: The context from which the command originates. Possible values include: 'message', 'compose', 'commandbox'
    :type command_context: str
    :param bot_message_preview_action: Bot message preview action taken by user. Possible values include: 'edit', 'send'
    :type bot_message_preview_action: str
    :param bot_activity_preview: List of bot activity previews.
    :type bot_activity_preview: List[Activity]
    :param message_payload: Message content sent as part of the command request.
    :type message_payload: MessageActionsPayload
    """

    data: object = None
    context: TaskModuleRequestContext = None
    command_id: str = None
    command_context: str = None
    bot_message_preview_action: str = None
    bot_activity_preview: List[Activity] = None
    message_payload: MessageActionsPayload = None
