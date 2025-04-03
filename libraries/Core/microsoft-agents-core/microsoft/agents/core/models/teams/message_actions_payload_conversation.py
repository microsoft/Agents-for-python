from pydantic import BaseModel


class MessageActionsPayloadConversation(BaseModel):
    """Represents a team or channel entity.

    :param conversation_identity_type: The type of conversation, whether a team or channel.
    :type conversation_identity_type: str
    :param id: The id of the team or channel.
    :type id: str
    :param display_name: The plaintext display name of the team or channel entity.
    :type display_name: str
    """

    conversation_identity_type: str
    id: str
    display_name: str
