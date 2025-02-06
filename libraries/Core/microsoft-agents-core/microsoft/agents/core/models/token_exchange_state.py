from .conversation_reference import ConversationReference
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class TokenExchangeState(AgentsModel):
    """TokenExchangeState

    :param connection_name: The connection name that was used.
    :type connection_name: str
    :param conversation: Gets or sets a reference to the conversation.
    :type conversation: ~microsoft.agents.protocols.models.ConversationReference
    :param relates_to: Gets or sets a reference to a related parent conversation for this token exchange.
    :type relates_to: ~microsoft.agents.protocols.models.ConversationReference
    :param bot_ur: The URL of the bot messaging endpoint.
    :type bot_ur: str
    :param ms_app_id: The bot's registered application ID.
    :type ms_app_id: str
    """

    connection_name: NonEmptyString = None
    conversation: ConversationReference = None
    relates_to: ConversationReference = None
    bot_url: NonEmptyString = None
    ms_app_id: NonEmptyString = None
