# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from os import environ
from dotenv import load_dotenv

from microsoft.agents.builder.app import AgentApplication, TurnState
from microsoft.agents.builder.app.oauth import Authorization
from microsoft.agents.builder import TurnContext, MessageFactory
from microsoft.agents.storage import MemoryStorage
from microsoft.agents.core.models import ActivityTypes, Activity
from microsoft.agents.core import load_configuration_from_env
from microsoft.agents.copilotstudio.client import ConnectionSettings, CopilotClient
from microsoft.agents.hosting.aiohttp import CloudAdapter
from microsoft.agents.authentication.msal import MsalConnectionManager

from shared import start_server

load_dotenv()

# Load configuration from environment
agents_sdk_config = load_configuration_from_env(environ)

# Create storage and connection manager
STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)


class McsConnectionSettings(ConnectionSettings):
    """Connection settings for MCS that loads from environment variables"""

    def __init__(self):
        environment_id = environ.get("ENVIRONMENT_ID")
        agent_identifier = environ.get("AGENT_IDENTIFIER")

        if not environment_id:
            raise ValueError("ENVIRONMENT_ID must be provided in environment variables")
        if not agent_identifier:
            raise ValueError(
                "AGENT_IDENTIFIER must be provided in environment variables"
            )

        # Call parent constructor with required parameters
        super().__init__(
            environment_id=environment_id,
            agent_identifier=agent_identifier,
            cloud=None,  # Will use default
            copilot_agent_type=None,  # Will use default
            custom_power_platform_cloud=None,
        )


# Create the agent instance
AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE, adapter=ADAPTER, authorization=AUTHORIZATION, **agents_sdk_config
)


@AGENT_APP.conversation_update("membersAdded")
async def status(context: TurnContext, state: TurnState) -> None:
    await context.send_activity(
        MessageFactory.text("Welcome to the MCS Agent demo!, ready to chat with MCS!")
    )


@AGENT_APP.on_sign_in_success
async def signin_success(
    context: TurnContext, state: TurnState, handler_id: str = None
) -> None:
    await context.send_activity(MessageFactory.text("User signed in successfully"))


@AGENT_APP.message("/logout")
async def sign_out(context: TurnContext, state: TurnState) -> None:
    if AGENT_APP.auth:
        await AGENT_APP.auth.sign_out(context, state)
    await context.send_activity(MessageFactory.text("User signed out"))


@AGENT_APP.activity(ActivityTypes.invoke)
async def invoke(context: TurnContext, state: TurnState) -> None:
    await context.send_activity(MessageFactory.text("Invoke received."))


@AGENT_APP.activity(ActivityTypes.message, auth_handlers=["mcs"])
async def message(context: TurnContext, state: TurnState) -> None:
    await _handle_message(context, state)


async def _handle_message(context: TurnContext, state: TurnState) -> None:
    """Handle incoming messages with MCS integration"""

    # Get conversation ID from state
    conversation_id = state.get_value("conversation.conversationId")

    # Get OBO token for Power Platform API
    if not AGENT_APP.auth:
        await _status(context, state)
        return

    try:
        obo_token = await AGENT_APP.auth.exchange_token(
            context, ["https://api.powerplatform.com/.default"]
        )

        if not obo_token or not obo_token.token:
            await _status(context, state)
            return

        # Create CopilotClient
        copilot_client = _create_client(obo_token.token)

        if not conversation_id:
            # Start new conversation
            async for activity in copilot_client.start_conversation():
                if activity.type == ActivityTypes.message:
                    await context.send_activity(MessageFactory.text(activity.text))
                    if activity.conversation and activity.conversation.id:
                        state.set_value(
                            "conversation.conversationId", activity.conversation.id
                        )
                        break
        else:
            # Continue existing conversation
            async for activity in copilot_client.ask_question(
                context.activity.text, conversation_id
            ):
                print(f"Received activity: {activity.type}, {activity.text}")

                if activity.type == ActivityTypes.message:
                    await context.send_activity(activity)
                elif activity.type == "typing":
                    typing_activity = Activity(type=ActivityTypes.typing)
                    await context.send_activity(typing_activity)

    except Exception as e:
        await context.send_activity(
            MessageFactory.text(f"Error communicating with MCS: {str(e)}")
        )


async def _status(context: TurnContext, state: TurnState) -> None:
    """Send status message when not authenticated"""
    await context.send_activity(
        MessageFactory.text("Welcome to the MCS Agent demo!, ready to chat with MCS!")
    )


def _create_client(token: str) -> CopilotClient:
    """Create CopilotClient with connection settings from environment"""
    settings = McsConnectionSettings()
    return CopilotClient(settings, token)


def load_copilot_studio_connection_settings_from_env() -> McsConnectionSettings:
    """Load Copilot Studio connection settings from environment variables"""
    return McsConnectionSettings()


# Create and start the agent
if __name__ == "__main__":
    # Use the start_server function from shared module
    start_server(
        agent_application=AGENT_APP,
        auth_configuration=CONNECTION_MANAGER.get_default_connection_configuration(),
    )
