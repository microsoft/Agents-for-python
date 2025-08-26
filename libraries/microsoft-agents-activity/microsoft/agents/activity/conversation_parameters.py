from pydantic import Field

from .channel_account import ChannelAccount
from .activity import Activity
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class ConversationParameters(AgentsModel):
    """Parameters for creating a new conversation.

    :param is_group: IsGroup
    :type is_group: bool
    :param agent: The agent address for this conversation
    :type agent: ~microsoft.agents.protocols.models.ChannelAccount
    :param members: Members to add to the conversation
    :type members: list[~microsoft.agents.protocols.models.ChannelAccount]
    :param topic_name: (Optional) Topic of the conversation (if supported by
     the channel)
    :type topic_name: str
    :param activity: (Optional) When creating a new conversation, use this
     activity as the initial message to the conversation
    :type activity: ~microsoft.agents.protocols.models.Activity
    :param channel_data: Channel specific payload for creating the
     conversation
    :type channel_data: object
    :param tenant_id: (Optional) The tenant ID in which the conversation should be created
    :type tenant_id: str
    """

    is_group: bool = None
    agent: ChannelAccount = Field(None, alias="bot")
    members: list[ChannelAccount] = None
    topic_name: NonEmptyString = None
    activity: Activity = None
    channel_data: object = None
    tenant_id: NonEmptyString = None
