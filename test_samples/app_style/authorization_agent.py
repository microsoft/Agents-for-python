# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import re
import sys
import traceback
from aiohttp.web import Application, Request, Response, run_app
from dotenv import load_dotenv

from os import environ
from microsoft.agents.authentication.msal import AuthTypes, MsalAuthConfiguration
from microsoft.agents.builder.app import AgentApplication, TurnState
from microsoft.agents.builder.app.oauth import AuthHandler
from microsoft.agents.hosting.aiohttp import (
    CloudAdapter,
    jwt_authorization_middleware,
    start_agent_process,
)
from microsoft.agents.authorization import (
    Connections,
    AccessTokenProviderBase,
    ClaimsIdentity,
)
from microsoft.agents.authentication.msal import MsalAuth

from microsoft.agents.builder import (
    RestChannelServiceClientFactory,
    TurnContext,
    MessageFactory,
)
from microsoft.agents.storage import MemoryStorage
from microsoft.agents.core.models import ActivityTypes, TokenResponse

load_dotenv()


class DefaultConfig(MsalAuthConfiguration):
    """Agent Configuration"""

    def __init__(self) -> None:
        self.AUTH_TYPE = AuthTypes.client_secret
        self.TENANT_ID = "" or environ.get("TENANT_ID")
        self.CLIENT_ID = "" or environ.get("CLIENT_ID")
        self.CLIENT_SECRET = "" or environ.get("CLIENT_SECRET")
        self.PORT = 3978


CONFIG = DefaultConfig()
AUTH_PROVIDER = MsalAuth(CONFIG)


class DefaultConnection(Connections):
    def get_default_connection(self) -> AccessTokenProviderBase:
        pass

    def get_token_provider(
        self, claims_identity: ClaimsIdentity, service_url: str
    ) -> AccessTokenProviderBase:
        return AUTH_PROVIDER

    def get_connection(self, connection_name: str) -> AccessTokenProviderBase:
        pass


CHANNEL_CLIENT_FACTORY = RestChannelServiceClientFactory(CONFIG, DefaultConnection())

# Create adapter.
ADAPTER = CloudAdapter(CHANNEL_CLIENT_FACTORY)

AGENT_APP = AgentApplication[TurnState](
    storage=MemoryStorage(),
    adapter=ADAPTER,
    authorization={
        "graph": AuthHandler(title="Graph API", text="Connect to Microsoft Graph"),
        "github": AuthHandler(
            title="GitHub",
            text="Connect to GitHub",
        ),
    },
)


@AGENT_APP.message(re.compile(r"^(status|auth status|check status)$", re.IGNORECASE))
async def status(context: TurnContext, state: TurnState) -> bool:
    """
    Internal method to check authorization status for all configured handlers.
    Returns True if at least one handler has a valid token.
    """
    if not AGENT_APP.auth:
        await context.send_activity(
            MessageFactory.text("Authorization is not configured.")
        )
        return False

    try:
        # Check status for each auth handler
        status_messages = []
        has_valid_token = False

        for handler_id in AGENT_APP.auth._auth_handlers.keys():
            try:
                token_response = await AGENT_APP.auth.get_token(context, handler_id)
                if token_response and token_response.token:
                    status_messages.append(f"✅ {handler_id}: Connected")
                    has_valid_token = True
                else:
                    status_messages.append(f"❌ {handler_id}: Not connected")
            except Exception as e:
                status_messages.append(f"❌ {handler_id}: Error - {str(e)}")

        status_text = "Authorization Status:\n" + "\n".join(status_messages)
        await context.send_activity(MessageFactory.text(status_text))
        return has_valid_token

    except Exception as e:
        await context.send_activity(
            MessageFactory.text(f"Error checking status: {str(e)}")
        )
        return False


@AGENT_APP.message(re.compile(r"^(logout|signout|sign out)$", re.IGNORECASE))
async def sign_out(
    context: TurnContext, state: TurnState, handler_id: str = None
) -> bool:
    """
    Internal method to sign out from the specified handler or all handlers.
    """
    if not AGENT_APP.auth:
        await context.send_activity(
            MessageFactory.text("Authorization is not configured.")
        )
        return False

    try:
        await AGENT_APP.auth.sign_out(context, state, handler_id)
        if handler_id:
            await context.send_activity(
                MessageFactory.text(f"Successfully signed out from {handler_id}.")
            )
        else:
            await context.send_activity(
                MessageFactory.text("Successfully signed out from all services.")
            )
        return True
    except Exception as e:
        await context.send_activity(MessageFactory.text(f"Error signing out: {str(e)}"))
        return False


@AGENT_APP.message(re.compile(r"^(login|signin|sign in)$", re.IGNORECASE))
async def sign_in(
    context: TurnContext, state: TurnState, handler_id: str = None
) -> TokenResponse:
    """
    Internal method to begin or continue sign-in flow for the specified handler.
    """
    if not AGENT_APP.auth:
        await context.send_activity(
            MessageFactory.text("Authorization is not configured.")
        )
        return None

    try:
        token_response = await AGENT_APP.auth.begin_or_continue_flow(
            context, state, handler_id
        )
        if token_response and token_response.token:
            await context.send_activity(
                MessageFactory.text(
                    f"Successfully signed in to {handler_id or 'service'}."
                )
            )
        return token_response
    except Exception as e:
        await context.send_activity(
            MessageFactory.text(f"Error during sign-in: {str(e)}")
        )
        return None


@AGENT_APP.message(re.compile(r"^(me|profile)$", re.IGNORECASE))
async def profile_request(
    context: TurnContext, state: TurnState, handler_id: str = "graph"
) -> dict:
    """
    Internal method to get user profile information using the specified handler.
    """
    if not AGENT_APP.auth:
        await context.send_activity(
            MessageFactory.text("Authorization is not configured.")
        )
        return None

    try:
        token_response = await AGENT_APP.auth.get_token(context, handler_id)
        if not token_response or not token_response.token:
            await context.send_activity(
                MessageFactory.text(
                    f"Not authenticated with {handler_id}. Please sign in first."
                )
            )
            return None

        # TODO: Implement actual profile request using the token
        # This would require making HTTP requests to the Graph API or other services
        # For now, return a placeholder
        profile_info = {
            "displayName": "User Name",
            "mail": "user@example.com",
            "id": "user-id-12345",
        }

        profile_text = f"Profile Information:\nName: {profile_info['displayName']}\nEmail: {profile_info['mail']}\nID: {profile_info['id']}"
        await context.send_activity(MessageFactory.text(profile_text))
        return profile_info

    except Exception as e:
        await context.send_activity(
            MessageFactory.text(f"Error getting profile: {str(e)}")
        )
        return None


@AGENT_APP.message(re.compile(r"^(prs|pull requests)$", re.IGNORECASE))
async def pull_requests(
    context: TurnContext, state: TurnState, handler_id: str = "github"
) -> list:
    """
    Internal method to get pull requests using the specified handler (typically GitHub).
    """
    if not AGENT_APP.auth:
        await context.send_activity(
            MessageFactory.text("Authorization is not configured.")
        )
        return []

    try:
        token_response = await AGENT_APP.auth.get_token(context, handler_id)
        if not token_response or not token_response.token:
            await context.send_activity(
                MessageFactory.text(
                    f"Not authenticated with {handler_id}. Please sign in first."
                )
            )
            return []

        # TODO: Implement actual GitHub API request using the token
        # This would require making HTTP requests to the GitHub API
        # For now, return placeholder data
        pull_requests = [
            {"title": "Fix authentication bug", "number": 123, "state": "open"},
            {"title": "Add new feature", "number": 124, "state": "open"},
            {"title": "Update documentation", "number": 125, "state": "closed"},
        ]

        pr_text = "Pull Requests:\n" + "\n".join(
            [f"#{pr['number']}: {pr['title']} ({pr['state']})" for pr in pull_requests]
        )
        await context.send_activity(MessageFactory.text(pr_text))
        return pull_requests

    except Exception as e:
        await context.send_activity(
            MessageFactory.text(f"Error getting pull requests: {str(e)}")
        )
        return []


@AGENT_APP.activity(ActivityTypes.invoke)
async def invoke(context: TurnContext, state: TurnState) -> str:
    """
    Internal method to process template expansion or function invocation.
    """
    await AGENT_APP.auth.begin_or_continue_flow(context, state)


@AGENT_APP.on_sign_in_success
async def handle_sign_in_success(
    context: TurnContext, state: TurnState, handler_id: str = None
) -> bool:
    """
    Internal method to handle successful sign-in events.
    """
    await context.send_activity(
        MessageFactory.text(
            f"Successfully signed in to {handler_id or 'service'}. You can now use authorized features."
        )
    )


@AGENT_APP.message(re.compile(r"^(prs|pull requests|pullrequests)$", re.IGNORECASE))
async def on_pull_requests(context: TurnContext, state: TurnState):
    await context.send_activity("PR command is not implemented yet.")


@AGENT_APP.message(re.compile(r"^\d{6}$"))
async def on_magic_code(context: TurnContext, state: TurnState):
    # Handle 6-digit magic codes for OAuth verification
    if AGENT_APP.auth:
        for handler_id in AGENT_APP.auth._auth_handlers.keys():
            try:
                token_response = await AGENT_APP.auth.begin_or_continue_flow(
                    context, state, handler_id
                )
                if token_response and token_response.token:
                    await _handle_sign_in_success(context, state, handler_id)
                    return True
            except Exception:
                # Continue trying other handlers
                continue

        await context.send_activity(
            MessageFactory.text("Invalid verification code. Please try again.")
        )
    else:
        await on_message(context, state)


@AGENT_APP.conversation_update("membersAdded")
async def on_members_added(context: TurnContext, _state: TurnState):
    await context.send_activity(
        "Welcome to the Authorization Agent! "
        "You can use commands like 'login', 'status', 'profile', 'prs', or 'logout'. "
        "For OAuth flows, enter the 6-digit verification code when prompted."
    )
    return True


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    await context.send_activity(f"You said: {context.activity.text}")


@AGENT_APP.error
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")


# Listen for incoming requests on /api/messages
async def entry_point(req: Request) -> Response:
    agent: AgentApplication = req.app["agent_app"]
    adapter: CloudAdapter = req.app["adapter"]
    return await start_agent_process(
        req,
        agent,
        adapter,
    )


APP = Application(middlewares=[jwt_authorization_middleware])
APP.router.add_post("/api/messages", entry_point)
APP["agent_configuration"] = CONFIG
APP["agent_app"] = AGENT_APP
APP["adapter"] = ADAPTER

if __name__ == "__main__":
    try:
        run_app(APP, host="localhost", port=CONFIG.PORT)
    except Exception as error:
        raise error
