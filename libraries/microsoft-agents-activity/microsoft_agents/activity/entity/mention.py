# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Literal

from ..channel_account import ChannelAccount
from .entity import Entity
from .entity_types import EntityTypes


class Mention(Entity):
    """Mention information (entity type: "mention").

    :param mentioned: The mentioned user
    :type mentioned: ~microsoft_agents.activity.ChannelAccount
    :param text: Sub Text which represents the mention (can be null or empty)
    :type text: str
    :param type: Type of this entity (RFC 3987 IRI)
    :type type: str
    """

    mentioned: ChannelAccount = None
    text: str = None
    type: Literal[EntityTypes.MENTION] = EntityTypes.MENTION
