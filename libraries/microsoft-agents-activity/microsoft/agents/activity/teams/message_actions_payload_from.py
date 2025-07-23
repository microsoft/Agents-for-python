# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from typing import Optional

from .message_actions_payload_user import MessageActionsPayloadUser
from .message_actions_payload_app import MessageActionsPayloadApp
from .message_actions_payload_conversation import MessageActionsPayloadConversation


class MessageActionsPayloadFrom(AgentsModel):
    """Represents a user, application, or conversation type that either sent or was referenced in a message.

    :param user: Represents details of the user.
    :type user: Optional["MessageActionsPayloadUser"]
    :param application: Represents details of the app.
    :type application: Optional["MessageActionsPayloadApp"]
    :param conversation: Represents details of the conversation.
    :type conversation: Optional["MessageActionsPayloadConversation"]
    """

    user: Optional[MessageActionsPayloadUser]
    application: Optional[MessageActionsPayloadApp]
    conversation: Optional[MessageActionsPayloadConversation]
