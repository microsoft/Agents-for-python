from microsoft.agents.activity import Activity

from .channel_info_protocol import ChannelInfoProtocol


class ConversationIdFactoryOptions:
    def __init__(
        self,
        from_oauth_scope: str,
        from_agent_id: str,
        activity: Activity,
        agent: ChannelInfoProtocol,
    ) -> None:
        self.from_oauth_scope = from_oauth_scope
        self.from_agent_id = from_agent_id
        # TODO: implement Activity and types as protocols and replace here
        self.activity = activity
        self.agent = agent
