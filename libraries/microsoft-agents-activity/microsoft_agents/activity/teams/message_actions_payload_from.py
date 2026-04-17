# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel

from .message_actions_payload_user import MessageActionsPayloadUser
from .message_actions_payload_app import MessageActionsPayloadApp
from .message_actions_payload_conversation import MessageActionsPayloadConversation


class MessageActionsPayloadFrom(AgentsModel):
    """Represents a user, application, or conversation type that either sent or was referenced in a message.

    :param user: Represents details of the user.
    :type user: MessageActionsPayloadUser | None
    :param application: Represents details of the app.
    :type application: MessageActionsPayloadApp | None
    :param conversation: Represents details of the conversation.
    :type conversation: MessageActionsPayloadConversation | None
    """

    user: MessageActionsPayloadUser | None
    application: MessageActionsPayloadApp | None
    conversation: MessageActionsPayloadConversation | None
