from microsoft_agents.activity import (
    Activity,
    ActivityTypes
)

from microsoft_agents.hosting.core import (
    AuthHandler,
    TurnContext,
)

class TEST_DEFAULTS:

    def __init__(self):
        
        self.channel_id = "__channel_id"
        self.user_id = "__user_id"
        self.ms_app_id = "__ms_app_id"

        self.activity = Activity(type=ActivityTypes.message)
        self.turn_context = TurnContext()
        self.auth_handlers = [AuthHandler()]