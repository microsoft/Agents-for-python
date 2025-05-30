from microsoft.agents.builder import (
    ActivityHandler,
    OAuthFlow,
    MessageFactory,
    TurnContext,
)
from microsoft.agents.builder.state import UserState
from microsoft.agents.core.models import ChannelAccount
from microsoft.agents.hosting.teams import TeamsActivityHandler, TeamsInfo

from graph_client import GraphClient


class TeamsSso(TeamsActivityHandler):
    def __init__(
        self, user_state: UserState, connection_name: str = None, app_id: str = None
    ):
        """
        Initializes a new instance of the TeamsSso class.
        :param user_state: The user state.
        :param connection_name: Connection name for OAuth.
        :param app_id: AgentApplication ID.
        """
        self.user_state = user_state
        self.oauth_flow = OAuthFlow(user_state, connection_name)

    async def on_sign_in_invoke(self, turn_context):
        # Log Event trigggered
        token_response = await self.oauth_flow.continue_flow(turn_context)
        if token_response.token:
            await self.send_logged_user_info(turn_context, token_response.token)

    async def on_members_added_activity(
        self, members_added: list[ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    "Hello and welcome to Teams SSO sample! Please type ‘login’ to sign in, ‘logout’ to sign out, or ‘getUserProfile’ to get user info."
                )

    async def on_message_activity(self, turn_context: TurnContext):
        text = turn_context.activity.text.strip() if turn_context.activity.text else ""

        if text == "login":
            await self.oauth_flow.begin_flow(turn_context)
        elif text == "logout":
            await self.oauth_flow.sign_out(turn_context)
            await turn_context.send_activity(
                MessageFactory.text("You have been signed out.")
            )
        elif text.isnumeric() and len(text) == 6:
            token_response = await self.oauth_flow.continue_flow(turn_context)
            if token_response.token:
                await self.send_logged_user_info(turn_context, token_response.token)
            else:
                await turn_context.send_activity(
                    MessageFactory.text("Invalid code. Please try again.")
                )
        elif "getUserProfile" in text:
            user_token = await self.oauth_flow.get_user_token(turn_context)
            if user_token.token:
                await self.send_logged_user_info(turn_context, user_token.token)
            else:
                await turn_context.send_activity(
                    MessageFactory.text("Please type 'login' to sign in first.")
                )
        else:
            await turn_context.send_activity(
                MessageFactory.text(
                    "Please type 'login' to sign in, 'logout' to sign out, or 'getUserProfile' to get user info."
                )
            )

    async def on_turn(self, turn_context: TurnContext):
        await super().on_turn(turn_context)
        await self.user_state.save_changes(turn_context)

    async def send_logged_user_info(self, turn_context: TurnContext, token: str):
        """
        Sends the logged user info.
        :param turn_context: The turn context.
        :param token: OAuth token.
        """
        graph_client = GraphClient(token)
        user_info = await graph_client.get_me()
        message = (
            f"You are {user_info.get('displayName', 'Unknown')} "
            f"and your email is {user_info.get('mail', 'Unknown')}."
        )
        await turn_context.send_activity(MessageFactory.text(message))
