from microsoft.agents.builder import (
    ActivityHandler,
    BasicOAuthFlow,
    MessageFactory,
    TurnContext,
)
from microsoft.agents.builder.state import UserState
from microsoft.agents.core.models import ChannelAccount
from microsoft.agents.hosting.teams import TeamsActivityHandler, TeamsInfo

from graph_client import GraphClient


class TeamsSso(TeamsActivityHandler):
    def __init__(self, user_state: UserState, connection_name: str = None, app_id: str = None):
        """
        Initializes a new instance of the TeamsSso class.
        :param user_state: The user state.
        :param connection_name: Connection name for OAuth.
        :param app_id: Application ID.
        """
        self.user_state = user_state
        self.oauth_flow = BasicOAuthFlow(user_state, connection_name, app_id)

    async def on_members_added_activity(
        self, members_added: list[ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello and welcome to Teams SSO sample!")

    async def on_message_activity(self, turn_context: TurnContext):
        text = turn_context.activity.text.strip() if turn_context.activity.text else ""
        
        if text == "login":
            await self.oauth_flow.get_oauth_token(turn_context)
        elif text == "logout":
            await self.oauth_flow.sign_out(turn_context)
            await turn_context.send_activity(
                MessageFactory.text("You have been signed out.")
            )
        elif "getUserProfile" in text:
            user_token = await self.oauth_flow.get_oauth_token(turn_context)
            if user_token:
                await self.send_logged_user_info(turn_context, user_token)
            else:
                await turn_context.send_activity(
                    MessageFactory.text("Please type 'login' to sign in first.")
                )
        elif "getPagedMembers" in text:
            members = await TeamsInfo.get_paged_members(turn_context, 2)
            member_emails = [m.email for m in members.members if m.email]
            await turn_context.send_activity(
                MessageFactory.text(f"Team members: {member_emails}")
            )
        else:
            await turn_context.send_activity(
                MessageFactory.text(
                    "Type 'login' to sign in, 'logout' to sign out, "
                    "'getUserProfile' to see your profile, or "
                    "'getPagedMembers' to see team members."
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