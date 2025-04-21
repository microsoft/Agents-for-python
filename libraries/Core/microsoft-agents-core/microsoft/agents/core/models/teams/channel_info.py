# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from typing import Optional


class ChannelInfo(AgentsModel):
    """A channel info object which describes the channel.

    :param id: Unique identifier representing a channel
    :type id: Optional[str]
    :param name: Name of the channel
    :type name: Optional[str]
    :param type: The channel type
    :type type: Optional[str]
    """

    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
