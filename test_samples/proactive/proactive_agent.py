# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Proactive messaging sample.

Mirrors the pattern from the C# ProactiveAgent sample.

Bot commands (all via /api/messages):
  -s          — store this conversation so it can be resumed later.
  -c          — continue THIS conversation proactively (no stored ID needed).
  -c <id>     — continue a previously stored conversation by ID.
                The continuation requires the user to be signed in via "me".
  -signin     — sign in with the "me" OAuth connection.
  -signout    — sign out from the "me" OAuth connection.
  /help       — show help text.
  anything else — echo the message back via a proactive continuation turn,
                  passing the original activity as the continuation value.

HTTP endpoints:
  POST /api/messages         — standard bot channel endpoint (all commands above).
  POST /api/proactive/notify — send a one-off notification to a stored conversation.
                               Body: {"conversationId": "<id>", "message": "<text>"}
  GET  /                     — health check.
"""

from __future__ import annotations

import json
import logging
import re
from os import environ, path
from typing import Any, Dict

from aiohttp import web
from dotenv import load_dotenv

from microsoft_agents.activity import Activity, ActivityTypes, load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import (
    CloudAdapter,
    jwt_authorization_middleware,
    start_agent_process,
)
from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    MessageFactory,
    TurnContext,
    TurnState,
)
from microsoft_agents.hosting.core.app import ApplicationOptions, Authorization, ProactiveOptions
from microsoft_agents.hosting.core.app.proactive import Conversation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

load_dotenv(path.join(path.dirname(__file__), ".env"))
agents_sdk_config = load_configuration_from_env(environ)

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)

# Authorization is built from agents_sdk_config so the "me" handler
# defined in the env file is automatically registered.
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

AGENT_APP = AgentApplication[TurnState](
    options=ApplicationOptions(
        storage=STORAGE,
        adapter=ADAPTER,
        proactive=ProactiveOptions(),
    ),
    authorization=AUTHORIZATION,
)

# ---------------------------------------------------------------------------
# Proactive handlers
# ---------------------------------------------------------------------------


async def _on_continue(context: TurnContext, state: TurnState) -> None:
    """Proactive turn handler for -c.

    Requires the user to be signed in via the "me" OAuth connection — enforced
    by passing token_handlers=["me"] to continue_conversation.  If sign-in is
    complete, retrieve the token and report its length (mirrors C# sample).
    """
    token_response = await AGENT_APP.auth.get_token(context, auth_handler_id="me")
    token_len = len(token_response.token) if token_response and token_response.token else 0
    await context.send_activity(
        f"This is the proactive continuation turn. "
        f"Token length = {token_len if token_len else 'not signed in'}."
    )


async def _on_echo(context: TurnContext, state: TurnState) -> None:
    """Proactive turn handler for the catch-all echo pattern.

    The original activity is carried in context.activity.value so this handler
    can reply without touching shared state.
    """
    original: Activity = context.activity.value
    text = original.text if original and original.text else "(empty)"
    await context.send_activity(f"You said: {text}")


# ---------------------------------------------------------------------------
# Agent handlers
# ---------------------------------------------------------------------------


@AGENT_APP.conversation_update("membersAdded")
async def on_members_added(context: TurnContext, _state: TurnState) -> None:
    await context.send_activity(
        "Welcome to the Proactive Agent sample!\n\n"
        "Commands:\n"
        "  **-s**          — store this conversation for later\n"
        "  **-c**          — proactively continue this conversation (requires sign-in)\n"
        "  **-c \<id\>**   — proactively continue a stored conversation\n"
        "  **-signin**     — sign in with the 'me' OAuth connection\n"
        "  **-signout**    — sign out from the 'me' OAuth connection\n"
        "  **/help**       — show this message\n\n"
        "Send anything else to see the echo-via-proactive pattern."
    )


@AGENT_APP.message("/help")
async def on_help(context: TurnContext, _state: TurnState) -> None:
    await context.send_activity(
        "Commands:\n"
        "  **-s**          — store this conversation\n"
        "  **-c**          — proactively continue this conversation (requires sign-in)\n"
        "  **-c \<id\>**   — proactively continue a stored conversation\n"
        "  **-signin**     — sign in with the 'me' OAuth connection\n"
        "  **-signout**    — sign out from the 'me' OAuth connection\n"
        "  **/help**       — show this message\n\n"
        "Anything else is echoed back via a proactive continuation turn.\n\n"
        "HTTP: POST /api/proactive/notify to send an external notification."
    )


@AGENT_APP.message("-s")
async def on_store(context: TurnContext, _state: TurnState) -> None:
    """Store the current conversation so it can be resumed proactively."""
    await AGENT_APP.proactive.store_conversation(context)
    conversation_id = context.activity.conversation.id
    await context.send_activity(
        f"Conversation stored. Use this ID with **-c** or the notify endpoint:\n\n"
        f"```\n{conversation_id}\n```"
    )
    logger.info("Stored conversation: %s", conversation_id)


@AGENT_APP.message("-signin", auth_handlers=["me"])
async def on_signin(context: TurnContext, _state: TurnState) -> None:
    """Trigger the OAuth sign-in flow for the 'me' connection.

    The auth_handlers=["me"] parameter causes the SDK to start or resume the
    OAuth flow before this handler runs.  By the time we reach here the user
    is signed in.
    """
    await context.send_activity("Signed in.")


@AGENT_APP.message("-signout")
async def on_signout(context: TurnContext, state: TurnState) -> None:
    """Sign the user out from the 'me' OAuth connection."""
    await AGENT_APP.auth.sign_out(context, auth_handler_id="me")
    await context.send_activity("Signed out.")


@AGENT_APP.message(re.compile(r"^-c(\s+\S+)?$"))
async def on_continue(context: TurnContext, _state: TurnState) -> None:
    """-c [id] — trigger a proactive continuation via the messaging turn.

    With no argument, continues THIS conversation (no prior -s needed).
    With an argument, continues the stored conversation with that ID.

    Passes token_handlers=["me"] so the proactive turn will fail with a
    RuntimeError if the user is not yet signed in — mirrors the C# sample's
    UserNotSignedIn exception handling.
    """
    parts = (context.activity.text or "").split(maxsplit=1)

    if len(parts) == 2:
        # -c <stored-id>
        conversation_id = parts[1].strip()
        try:
            await AGENT_APP.proactive.continue_conversation(
                ADAPTER,
                conversation_id,
                _on_continue,
                token_handlers=["me"],
            )
            await context.send_activity(
                f"Proactive continuation sent to conversation `{conversation_id}`."
            )
        except KeyError:
            await context.send_activity(
                f"Conversation `{conversation_id}` not found. Send **-s** first to store it."
            )
        except RuntimeError:
            await context.send_activity("Send **-signin** first.")
    else:
        # -c alone: continue THIS conversation without a storage lookup.
        conversation = Conversation.from_turn_context(context)
        try:
            await AGENT_APP.proactive.continue_conversation(
                ADAPTER,
                conversation,
                _on_continue,
                token_handlers=["me"],
            )
        except RuntimeError:
            await context.send_activity("Send **-signin** first.")


@AGENT_APP.activity(ActivityTypes.message)
async def on_message(context: TurnContext, _state: TurnState) -> None:
    """Catch-all: echo the message back via a proactive continuation turn.

    Mirrors C# ProactiveAgent.OnMessageAsync — builds a Conversation from the
    current turn context, attaches the original activity as the continuation
    value, and lets _on_echo reply from inside the proactive turn.
    """
    conversation = Conversation.from_turn_context(context)

    # Attach the original activity as the value on the continuation event so
    # _on_echo can read it from context.activity.value without touching state.
    continuation = conversation.conversation_reference.get_continuation_activity()
    continuation.value = context.activity

    await AGENT_APP.proactive.continue_conversation(
        ADAPTER,
        conversation,
        _on_echo,
        continuation_activity=continuation,
    )


@AGENT_APP.error
async def on_error(context: TurnContext, error: Exception) -> None:
    logger.exception("Unhandled error in AgentApplication: %s", error)
    await context.send_activity("An unexpected error occurred. Please try again.")


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


async def _read_json(request: web.Request) -> Dict[str, Any]:
    if request.content_length in (0, None):
        return {}
    try:
        return await request.json()
    except json.JSONDecodeError:
        return {}


# ---------------------------------------------------------------------------
# HTTP route handlers
# ---------------------------------------------------------------------------


async def _handle_root(_request: web.Request) -> web.Response:
    return web.json_response({"status": "ready", "sample": "proactive-agent"})


async def _handle_messages(request: web.Request) -> web.Response:
    agent_app: AgentApplication = request.app["agent_app"]
    adapter: CloudAdapter = request.app["adapter"]
    response = await start_agent_process(request, agent_app, adapter)
    return response or web.Response(status=202)


async def _handle_proactive_notify(request: web.Request) -> web.Response:
    """Send a one-off proactive activity to a stored conversation.

    Intended for external triggers (schedulers, webhooks, etc.).
    For in-conversation proactive messaging use the **-c** command instead.

    Expected JSON body::

        {
            "conversationId": "<id returned by the -s command>",
            "message": "Hello from the server!"
        }
    """
    payload = await _read_json(request)
    conversation_id: str = (payload.get("conversationId") or "").strip()
    message: str = (payload.get("message") or "").strip()

    if not conversation_id:
        return web.json_response({"error": "'conversationId' is required."}, status=400)
    if not message:
        return web.json_response({"error": "'message' is required."}, status=400)

    try:
        await AGENT_APP.proactive.send_activity(
            ADAPTER,
            conversation_id,
            MessageFactory.text(f"[Notification] {message}"),
        )
    except KeyError:
        return web.json_response(
            {
                "error": (
                    f"Conversation '{conversation_id}' not found. "
                    "Send -s in the conversation first."
                )
            },
            status=404,
        )
    except Exception as exc:
        logger.exception("Error sending proactive notification: %s", exc)
        return web.json_response({"error": str(exc)}, status=500)

    logger.info("Notification delivered to: %s", conversation_id)
    return web.json_response(
        {"status": "delivered", "conversationId": conversation_id},
        status=202,
    )


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app() -> web.Application:
    app = web.Application(middlewares=[jwt_authorization_middleware])

    app["agent_app"] = AGENT_APP
    app["adapter"] = ADAPTER
    app["agent_configuration"] = CONNECTION_MANAGER.get_default_connection_configuration()

    app.router.add_get("/", _handle_root)
    app.router.add_post("/api/messages", _handle_messages)
    app.router.add_post("/api/proactive/notify", _handle_proactive_notify)

    return app


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    host = environ.get("HOST", "localhost")
    port = int(environ.get("PORT", "3978"))

    web.run_app(create_app(), host=host, port=port)
