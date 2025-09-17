from microsoft_agents.activity import (
    Activity,
    ActivityTypes
)

from microsoft_agents.hosting.core import (
    UserTokenClient,
    OAuthFlow,
    AuthHandler,
    ConnectionManager,
    Authorization,
    TurnContext,
)

class TEST_DEFAULTS:

    def __init__(self):
        
        self.channel_id = "__channel_id"
        self.user_id = "__user_id"
        self.ms_app_id = "__ms_app_id"

        self.activity = Activity(type=ActivityTypes.message)
        self.turn_context = TurnContext()
        self.user_token_client = UserTokenClient()
        self.oauth_flow = OAuthFlow()
        self.auth_handlers = [AuthHandler()]
        self.connection_manager = ConnectionManager()
        self.authorization = Authorization()