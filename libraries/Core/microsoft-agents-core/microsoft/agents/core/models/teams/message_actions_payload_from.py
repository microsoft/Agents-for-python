from pydantic import BaseModel
from typing import Optional


class MessageActionsPayloadFrom(BaseModel):
    """Represents a user, application, or conversation type that either sent or was referenced in a message.

    :param user: Represents details of the user.
    :type user: Optional["MessageActionsPayloadUser"]
    :param application: Represents details of the app.
    :type application: Optional["MessageActionsPayloadApp"]
    :param conversation: Represents details of the conversation.
    :type conversation: Optional["MessageActionsPayloadConversation"]
    """

    user: Optional["MessageActionsPayloadUser"]
    application: Optional["MessageActionsPayloadApp"]
    conversation: Optional["MessageActionsPayloadConversation"]
