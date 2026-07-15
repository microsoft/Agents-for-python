import re
import sys
import traceback

from microsoft_agents.activity import ConversationUpdateTypes

from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnContext,
    TurnState
)

from microsoft_agents.testing import (
    AgentEnvironment,
)

async def init_agent(env: AgentEnvironment):
    """Initialize the application for the quickstart sample."""

    app: AgentApplication[TurnState] = env.agent_application

    @app.conversation_update(ConversationUpdateTypes.MEMBERS_ADDED)
    async def on_members_added(context: TurnContext, state: TurnState) -> None:
        await context.send_activity(
            "Welcome to the empty agent! "
            "This agent is designed to be a starting point for your own agent development."
        )

    @app.message(re.compile(r"^hello$"))
    async def on_hello(context: TurnContext, state: TurnState) -> None:
        await context.send_activity("Hello!")

    @app.activity("message")
    async def on_message(context: TurnContext, state: TurnState) -> None:
        await context.send_activity(f"you said: {context.activity.text}")

    @app.error
    async def on_error(context: TurnContext, error: Exception):
        # This check writes out errors to console log .vs. app insights.
        # NOTE: In production environment, you should consider logging this to Azure
        #       application insights.
        print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
        traceback.print_exc()

        # Send a message to the user
        await context.send_activity("The bot encountered an error or bug.")