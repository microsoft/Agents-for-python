# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class ChannelInfo(AgentsModel):
    """A channel info object which describes the channel.

    :param id: Unique identifier representing a channel
    :type id: str | None
    :param name: Name of the channel
    :type name: str | None
    :param type: The channel type
    :type type: str | None
    """

    id: str | None = None
    name: str | None = None
    type: str | None = None
