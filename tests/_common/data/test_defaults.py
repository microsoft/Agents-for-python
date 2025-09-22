from microsoft_agents.activity import Activity, ActivityTypes

from microsoft_agents.hosting.core import (
    AuthHandler,
    TurnContext,
)


class TEST_DEFAULTS:
    def __init__(self):

        self.token = "__token"
        self.channel_id = "__channel_id"
        self.user_id = "__user_id"
        self.bot_url = "https://botframework.com"
        self.ms_app_id = "__ms_app_id"
        self.abs_oauth_connection_name = "__connection_name"
        self.missing_abs_oauth_connection_name = "__missing_connection_name"

        self.auth_handlers = [AuthHandler()]
