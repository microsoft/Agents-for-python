# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from typing import List, Optional

from .messaging_extension_parameter import MessagingExtensionParameter
from .messaging_extension_query_options import MessagingExtensionQueryOptions


class MessagingExtensionQuery(AgentsModel):
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

    command_id: str = None
    parameters: List[MessagingExtensionParameter] = None
    query_options: Optional[MessagingExtensionQueryOptions] = None
    state: str = None
