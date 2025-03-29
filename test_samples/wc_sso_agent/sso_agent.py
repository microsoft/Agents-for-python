from microsoft.agents.core.models import ChannelAccount
from microsoft.agents.builder import (
    ActivityHandler,
    BasicOAuthFlow,
    MessageFactory,
    TurnContext,
)
from microsoft.agents.builder.state import UserState

from graph_client import GraphClient


class SsoAgent(ActivityHandler):

    def __init__(self, user_state: UserState, connection_name: str, app_id: str):
        """
        Initializes a new instance of the SsoAgent class.
        :param user_state: The user state.
        """
        self.user_state = user_state
        self.oauth_flow = BasicOAuthFlow(user_state, connection_name, app_id)

    async def on_members_added_activity(
        self, members_added: list[ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello and welcome!")

    async def on_message_activity(self, turn_context: TurnContext):
        if turn_context.activity.text == "login":
            await self.oauth_flow.get_oauth_token(turn_context)
        elif turn_context.activity.text == "logout":
            await self.oauth_flow.sign_out(turn_context)
            await turn_context.send_activity(
                MessageFactory.text("You have been signed out.")
            )
        else:
            if len(turn_context.activity.text.strip()) != 6:
                await turn_context.send_activity(
                    MessageFactory.text(
                        'Please enter "login" to sign in or "logout" to sign out'
                    )
                )
            else:
                await self.get_token(turn_context)

    async def on_turn(self, turn_context):
        await super().on_turn(turn_context)
        await self.user_state.save_changes(turn_context)

    async def get_token(self, turn_context: TurnContext):
        """
        Gets the OAuth token.
        :param turn_context: The turn context.
        :return: The user token.
        """
        user_token = await self.oauth_flow.get_oauth_token(turn_context)
        if user_token:
            await self.send_logged_user_info(turn_context, user_token)

    async def send_logged_user_info(self, turn_context: TurnContext, token: str):
        """
        Sends the logged user info.
        :param turn_context: The turn context.
        """
        graph_client = GraphClient(token)
        user_info = await graph_client.get_me()
        message = (
            f"You are {user_info['displayName']} and your email is {user_info['mail']}."
        )
        await turn_context.send_activity(MessageFactory.text(message))
