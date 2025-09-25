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

        self.abs_oauth_connection_name = "connection_name"
        self.obo_connection_name = "SERVICE_CONNECTION"
        self.auth_handler_id = "auth_handler_id"
        self.auth_handler_title = "auth_handler_title"
        self.auth_handler_text = "auth_handler_text"

        self.agentic_abs_oauth_connection_name = "agentic_connection_name"
        self.agentic_obo_connection_name = "SERVICE_CONNECTION"
        self.agentic_auth_handler_id = "agentic_auth_handler_id"
        self.agentic_auth_handler_title = "agentic_auth_handler_title"
        self.agentic_auth_handler_text = "agentic_auth_handler_text"


        self.missing_abs_oauth_connection_name = "missing_connection_name"

        self.auth_handlers = [AuthHandler()]
