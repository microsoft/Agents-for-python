import pytest
import re

from microsoft_agents.hosting.core import TurnContext, TurnState

from tests._integration.common import TestingEnvironment

ON_MEMBERS_ADDED_MESSAGE = "Hello and welcome!"
HELLO_MESSAGE = "Hello!"
ON_MESSAGE_TEMPLATE = "You said: {text}"
ON_ERROR_MESSAGE = "Oops. Something went wrong."


def main(testenv: TestingEnvironment):

    AGENT_APP = testenv.agent_app

    @AGENT_APP.conversation_update("membersAdded")
    async def on_members_added(context: TurnContext, state: TurnState):
        await context.send_activity(ON_MEMBERS_ADDED_MESSAGE)

    @AGENT_APP.message(re.compile(r"^hello$"))
    async def on_hello(context: TurnContext, state: TurnState):
        await context.send_activity(HELLO_MESSAGE)

    @AGENT_APP.activity("message")
    async def on_message(context: TurnContext, state: TurnState):
        await context.send_activity(
            ON_MESSAGE_TEMPLATE.format(text=context.activity.text)
        )

    @AGENT_APP.error
    async def on_error(context: TurnContext, error: Exception):
        await context.send_activity(ON_ERROR_MESSAGE)
