from microsoft.agents.core.models import Activity

from .channel_info_protocol import ChannelInfoProtocol


class ConversationIdFactoryOptions:
    def __init__(
        self,
        from_oauth_scope: str,
        from_bot_id: str,
        activity: Activity,
        bot: ChannelInfoProtocol,
    ) -> None:
        self.from_oauth_scope = from_oauth_scope
        self.from_bot_id = from_bot_id
        # TODO: implement Activity and types as protocols and replace here
        self.activity = activity
        self.bot = bot
