from .channel_account import ChannelAccount
from ._type_aliases import NonEmptyString
from .agents_model import AgentsModel


class PagedMembersResult(AgentsModel):
    """Page of members.

    :param continuation_token: Paging token
    :type continuation_token: str
    :param members: The Channel Accounts.
    :type members: list[~microsoft.agents.protocols.models.ChannelAccount]
    """

    continuation_token: NonEmptyString = None
    members: list[ChannelAccount] = None
