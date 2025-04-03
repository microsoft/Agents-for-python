from pydantic import BaseModel
from typing import List, Optional


class MessagingExtensionQuery(BaseModel):
    """Messaging extension query.

    :param command_id: Id of the command assigned by Bot
    :type command_id: str
    :param parameters: Parameters for the query
    :type parameters: List["MessagingExtensionParameter"]
    :param query_options: Query options for the extension
    :type query_options: Optional["MessagingExtensionQueryOptions"]
    :param state: State parameter passed back to the bot after authentication/configuration flow
    :type state: str
    """

    command_id: str
    parameters: List["MessagingExtensionParameter"]
    query_options: Optional["MessagingExtensionQueryOptions"]
    state: str
