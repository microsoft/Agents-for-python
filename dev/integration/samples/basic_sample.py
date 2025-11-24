import os
import sys
import traceback

from dotenv import load_dotenv

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ConversationUpdateTypes,
    InvokeResponse,
    MessageReactionTypes,
)
from microsoft_agents.hosting.core import AgentApplication, TurnContext, TurnState
from microsoft_agents.testing.integration.core import Sample


class BasicSample(Sample):
    """A quickstart sample implementation."""

    @classmethod
    async def get_config(cls) -> dict:
        """Retrieve the configuration for the sample."""

        load_dotenv("./src/tests/.env")

        return {
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID": os.getenv(
                "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID"
            ),
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET": os.getenv(
                "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET"
            ),
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID": os.getenv(
                "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID"
            ),
        }

    async def init_app(self):
        """Initialize the application for the quickstart sample."""

        app: AgentApplication[TurnState] = self.env.agent_application

        @app.conversation_update(ConversationUpdateTypes.MEMBERS_ADDED)
        async def on_members_added(context: TurnContext, state: TurnState) -> None:
            await context.send_activity("Hello and Welcome!")

        @app.activity(ActivityTypes.message)
        async def on_message(context: TurnContext, state: TurnState) -> None:
            counter = state.get_value(
                "ConversationState.counter",
                default_value_factory=(lambda: 0),
                target_cls=int,
            )
            await context.send_activity(
                f"[{counter}] You said: {context.activity.text}"
            )
            counter += 1
            state.set_value("ConversationState.counter", counter)
            await state.save(context)

        @app.activity(ActivityTypes.invoke)
        async def on_invoke(context: TurnContext, state: TurnState) -> None:
            invoke_response = InvokeResponse(
                status=200,
                body={"message": "Invoke received.", "data": context.activity.value},
            )

            await context.send_activity(
                Activity(type=ActivityTypes.invoke_response, value=invoke_response)
            )

        @app.activity(ActivityTypes.message_update)
        async def on_message_update(context: TurnContext, state: TurnState) -> None:
            await context.send_activity(f"Message Edited: {context.activity.id}")

        @app.activity(ActivityTypes.event)
        async def on_event(context: TurnContext, state: TurnState) -> None:
            await context.send_activity("Received an event: " + context.activity.name)

        @app.message_reaction(MessageReactionTypes.REACTIONS_ADDED)
        async def on_reactions_added(context: TurnContext, state: TurnState) -> None:
            await context.send_activity(
                "Message Reaction Added: " + context.activity.reactions_added[0].type
            )

        @app.message_reaction(MessageReactionTypes.REACTIONS_REMOVED)
        async def on_reactions_removed(context: TurnContext, state: TurnState) -> None:
            await context.send_activity(
                "Message Reaction Removed: "
                + context.activity.reactions_removed[0].type
            )

        @app.error
        async def on_error(context: TurnContext, error: Exception):
            # This check writes out errors to console log .vs. app insights.
            # NOTE: In production environment, you should consider logging this to Azure
            #       application insights.
            print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
            traceback.print_exc()

            # Send a message to the user
            await context.send_activity("The bot encountered an error or bug.")
