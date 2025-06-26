# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from os import environ
from typing import Optional
from dotenv import load_dotenv

from microsoft.agents.builder.app import AgentApplication, TurnState
from microsoft.agents.builder.app.oauth import Authorization
from microsoft.agents.builder import TurnContext, MessageFactory
from microsoft.agents.storage import MemoryStorage
from microsoft.agents.core.models import ActivityTypes, Activity
from microsoft.agents.core import load_configuration_from_env
from microsoft.agents.copilotstudio.client import (
    ConnectionSettings,
    CopilotClient,
    PowerPlatformCloud,
    AgentType,
)
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

    def __init__(
        self,
        app_client_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        environment_id: Optional[str] = None,
        agent_identifier: Optional[str] = None,
        cloud: Optional[PowerPlatformCloud] = None,
        copilot_agent_type: Optional[AgentType] = None,
        custom_power_platform_cloud: Optional[str] = None,
        **kwargs: Optional[str],
    ) -> None:
        self.app_client_id = app_client_id or kwargs.get("AGENTAPPID")
        self.tenant_id = tenant_id or kwargs.get("TENANTID")

        if not self.app_client_id:
            raise ValueError("App Client ID must be provided")
        if not self.tenant_id:
            raise ValueError("Tenant ID must be provided")

        environment_id = environment_id or kwargs.get("ENVIRONMENTID")
        agent_identifier = agent_identifier or kwargs.get("SCHEMANAME")
        cloud = cloud or PowerPlatformCloud[kwargs.get("CLOUD", "UNKNOWN")]
        copilot_agent_type = (
            copilot_agent_type or AgentType[kwargs.get("COPILOTAGENTTYPE", "PUBLISHED")]
        )
        custom_power_platform_cloud = custom_power_platform_cloud or kwargs.get(
            "CUSTOMPOWERPLATFORMCLOUD", None
        )

        super().__init__(
            environment_id,
            agent_identifier,
            cloud,
            copilot_agent_type,
            custom_power_platform_cloud,
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


@AGENT_APP.activity(ActivityTypes.message, auth_handlers=["MCS"])
async def message(context: TurnContext, state: TurnState) -> None:
    await _handle_message(context, state)


async def _handle_message(context: TurnContext, state: TurnState) -> None:
    """Handle incoming messages with MCS integration"""

    # Get conversation ID from state
    conversation_id = state.get_value("ConversationState.conversationId")

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
    settings = McsConnectionSettings(**agents_sdk_config)
    return CopilotClient(settings, token)


# Create and start the agent
if __name__ == "__main__":
    # Use the start_server function from shared module
    start_server(
        agent_application=AGENT_APP,
        auth_configuration=CONNECTION_MANAGER.get_default_connection_configuration(),
    )
