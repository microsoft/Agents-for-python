# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import traceback
from os import environ, path
from dotenv import load_dotenv

from microsoft_agents.hosting.core import (
    Authorization,
    TurnContext,
    MessageFactory,
    MemoryStorage,
    AgentApplication,
    TurnState,
    ConversationState,
)
from microsoft_agents.activity import (
    load_configuration_from_env,
    ActivityTypes,
    Activity,
)
from microsoft_agents.activity.config import Configuration
from microsoft_agents.copilotstudio.client import (
    ConnectionSettings,
    CopilotClient,
    PowerPlatformCloud,
    AgentType,
)
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.authentication.msal import MsalConnectionManager

from shared import start_server

load_dotenv(path.join(path.dirname(__file__), ".env"))

# Load configuration from environment
agents_sdk_config = load_configuration_from_env(environ)

# Create storage and connection manager
STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(config=agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, config=agents_sdk_config)


class McsConnectionSettings(ConnectionSettings):
    """Connection settings for the COPILOTSTUDIOAGENT configuration section."""

    def __init__(self, config: Configuration) -> None:
        self.app_client_id = config.get_str("AGENTAPPID", default=None)
        self.tenant_id = config.get_str("TENANTID", default=None)

        if not self.app_client_id:
            raise ValueError("Agent App ID must be provided")
        if not self.tenant_id:
            raise ValueError("Tenant ID must be provided")

        super().__init__(
            environment_id=config.get_str("ENVIRONMENTID", default=None),
            agent_identifier=config.get_str("SCHEMANAME", default=None),
            cloud=PowerPlatformCloud[config.get_str("CLOUD", default="UNKNOWN")],
            copilot_agent_type=AgentType[
                config.get_str("COPILOTAGENTTYPE", default="PUBLISHED")
            ],
            custom_power_platform_cloud=config.get_str(
                "CUSTOMPOWERPLATFORMCLOUD", default=None
            ),
        )


# Create the agent instance
AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE, authorization=AUTHORIZATION
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


@AGENT_APP.activity(ActivityTypes.message, auth_handlers=["MCS"])
async def message(context: TurnContext, state: TurnState) -> None:
    await _handle_message(context, state)


async def _handle_message(context: TurnContext, state: TurnState) -> None:
    """Handle incoming messages with MCS integration"""

    # Get conversation ID from state
    conversation_id = state.get_value(
        ConversationState.CONTEXT_SERVICE_KEY + ".conversation_id", target_cls=str
    )

    # Get OBO token for Power Platform API
    if not AGENT_APP.auth:
        await _status(context, state)
        return

    try:
        obo_token = await AGENT_APP.auth.exchange_token(
            context, ["https://api.powerplatform.com/.default"], "MCS"
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
                            ConversationState.CONTEXT_SERVICE_KEY + ".conversation_id",
                            activity.conversation.id,
                        )
                        await state.save(context)
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
        traceback.print_exc()
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
    settings = McsConnectionSettings(agents_sdk_config.get_section("COPILOTSTUDIOAGENT"))
    return CopilotClient(settings, token)


# Create and start the agent
if __name__ == "__main__":
    # Use the start_server function from shared module
    start_server(
        agent_application=AGENT_APP,
        adapter=ADAPTER,
        config=agents_sdk_config,
    )
