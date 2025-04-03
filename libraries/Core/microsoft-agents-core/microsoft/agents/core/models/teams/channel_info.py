from pydantic import BaseModel


class ChannelInfo(BaseModel):
    """A channel info object which describes the channel.

    :param id: Unique identifier representing a channel
    :type id: str
    :param name: Name of the channel
    :type name: str
    :param type: The channel type
    :type type: str
    """

    id: str
    name: str
    type: str
