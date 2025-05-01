import base64
import json
from typing import Optional
from pydantic import Field

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
    :param agent_url: The URL of the agent messaging endpoint.
    :type agent_url: str
    :param ms_app_id: The agent's registered application ID.
    :type ms_app_id: str
    """

    connection_name: NonEmptyString = None
    conversation: ConversationReference = None
    relates_to: Optional[ConversationReference] = None
    agent_url: NonEmptyString = Field(None, alias="bot_url")
    ms_app_id: NonEmptyString = None

    def get_encoded_state(self) -> str:
        """Returns the encoded state for the token exchange."""
        return base64.b64encode(
            json.dumps(
                self.model_dump(by_alias=True, exclude_none=True, exclude_unset=True)
            ).encode(encoding="UTF-8", errors="strict")
        ).decode()
