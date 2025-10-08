# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class MessageReaction(AgentsModel):
    """Message reaction object.

    :param type: Message reaction type. Possible values include: 'like',
     'plusOne'
    :type type: str or ~microsoft_agents.activity.MessageReactionTypes
    """

    type: NonEmptyString
