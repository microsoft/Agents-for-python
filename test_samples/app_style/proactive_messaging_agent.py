# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Proactive messaging sample demonstrating how to start and continue a Teams conversation."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from os import environ, path
from typing import Any, Dict, Optional

from aiohttp import web
from dotenv import load_dotenv

from microsoft_agents.activity import (
    ChannelAccount,
    ConversationAccount,
    ConversationParameters,
    ConversationReference,
    # load_configuration_from_env,
)
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter, jwt_authorization_middleware
from microsoft_agents.hosting.core import (
    AgentApplication,
    Authorization,
    AuthenticationConstants,
    ClaimsIdentity,
    MessageFactory,
    MemoryStorage,
    TurnContext,
    TurnState,
)


# TODO: libraries will be updated to add current changes to this method
def load_configuration_from_env(
    env_vars: dict[str, Any], custom_config_keys: list[str] = None
) -> dict:
    """
    Parses environment variables and returns a dictionary with the relevant configuration.
    """
    custom_config_keys = custom_config_keys or []
    vars = env_vars.copy()
    result = {}
    for key, value in vars.items():
        levels = key.split("__")
        current_level = result
        last_level = None
        for next_level in levels:
            if next_level not in current_level:
                current_level[next_level] = {}
            last_level = current_level
            current_level = current_level[next_level]
        last_level[levels[-1]] = value

    if result.get("CONNECTIONSMAP") and isinstance(result["CONNECTIONSMAP"], dict):
        result["CONNECTIONSMAP"] = [
            conn for conn in result.get("CONNECTIONSMAP", {}).values()
        ]

    configuration = {
        "AGENTAPPLICATION": result.get("AGENTAPPLICATION", {}),
        "CONNECTIONS": result.get("CONNECTIONS", {}),
        "CONNECTIONSMAP": result.get("CONNECTIONSMAP", {}),
    }
    configuration.update(
        {key: result[key] for key in custom_config_keys if key in result}
    )

    return configuration


@dataclass
class ProactiveMessagingSettings:
    """Configuration required to perform proactive operations."""

    bot_id: str
    agent_id: str
    tenant_id: str
    scope: str = "https://api.botframework.com/.default"
    channel_id: str = "msteams"
    service_url: str = "https://smba.trafficmanager.net/teams/"
    default_user_aad_object_id: Optional[str] = None

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "ProactiveMessagingSettings":
        try:
            return cls(
                bot_id=raw["BOTID"],
                agent_id=raw["AGENTID"],
                tenant_id=raw["TENANTID"],
                scope=raw.get("SCOPE", cls.scope),
                channel_id=raw.get("CHANNELID", cls.channel_id),
                service_url=raw.get("SERVICEURL", cls.service_url),
                default_user_aad_object_id=raw.get("USERAADOBJECTID"),
            )
        except KeyError as exc:  # pragma: no cover - defensive guard
            missing = exc.args[0]
            raise ValueError(
                f"Missing required PROACTIVEMESSAGING__{missing} environment variable"
            ) from exc


class ProactiveMessenger:
    """Encapsulates proactive conversation helpers for Teams."""

    def __init__(
        self,
        adapter: CloudAdapter,
        settings: ProactiveMessagingSettings,
    ) -> None:
        self._adapter = adapter
        self._settings = settings

    async def create_conversation(
        self,
        message: Optional[str],
        user_aad_object_id: Optional[str],
    ) -> str:
        """Create a new conversation and optionally seed it with an initial message."""

        effective_user = user_aad_object_id or self._settings.default_user_aad_object_id
        if not effective_user:
            raise ValueError(
                "UserAadObjectId is required when no default is configured."
            )

        members = [ChannelAccount(id=effective_user)]
        parameters = ConversationParameters(
            is_group=False,
            agent=ChannelAccount(id=self._settings.agent_id),
            members=members,
            tenant_id=self._settings.tenant_id,
        )

        conversation_id: Optional[str] = None

        async def _callback(turn_context: TurnContext) -> None:
            nonlocal conversation_id
            conversation_id = turn_context.activity.conversation.id
            if message:
                await turn_context.send_activity(MessageFactory.text(message))

        await self._adapter.create_conversation(
            self._settings.bot_id,
            self._settings.channel_id,
            self._settings.service_url,
            self._settings.scope,
            parameters,
            _callback,
        )

        if not conversation_id:
            raise RuntimeError("Conversation id was not returned by the channel.")

        return conversation_id

    async def send_message(self, conversation_id: str, message: str) -> None:
        """Send a proactive message into an existing conversation."""

        if not conversation_id:
            raise ValueError("conversationId is required.")
        if not message:
            raise ValueError("message is required.")

        # TODO: user field not really needed but requires library update
        reference = ConversationReference(
            channel_id=self._settings.channel_id,
            service_url=self._settings.service_url,
            agent=ChannelAccount(id="<<from conversation reference>>", name="<<from conversation reference>>"),
            conversation=ConversationAccount(
                id=conversation_id
            ),
            user=ChannelAccount(id="user_id", name="user_name"),
        )
        continuation_activity = reference.get_continuation_activity()

        # TODO: activity id as parameter requires library update
        continuation_activity.id = conversation_id + "|0000001"

        async def _callback(turn_context: TurnContext) -> None:
            await turn_context.send_activity(MessageFactory.text(message))

        await self._adapter.continue_conversation_with_claims(
            self._create_identity(
                self._settings.bot_id,
                self._settings.service_url,
                "https://api.botframework.com",
            ),
            continuation_activity,
            _callback,
        )

    @staticmethod
    def _create_identity(audience: str, service_url: str, issuer: str) -> ClaimsIdentity:
        """Create a claims identity for proactive messaging."""
        return ClaimsIdentity(
            claims={
                AuthenticationConstants.AUDIENCE_CLAIM: audience,
                AuthenticationConstants.SERVICE_URL_CLAIM: service_url,
                AuthenticationConstants.ISSUER_CLAIM: issuer,
            },
            is_authenticated=True,
        )


async def _read_optional_json(request: web.Request) -> Dict[str, Any]:
    if request.content_length in (0, None):
        return {}
    try:
        return await request.json()
    except json.JSONDecodeError:
        return {}


def create_app() -> web.Application:
    """Create and configure the aiohttp application hosting the sample."""

    load_dotenv(path.join(path.dirname(__file__), ".env"))

    # Load base Agents SDK configuration that the core components expect.
    agents_sdk_config = load_configuration_from_env(
        environ, custom_config_keys=["PROACTIVEMESSAGING"]
    )

    storage = MemoryStorage()
    connection_manager = MsalConnectionManager(**agents_sdk_config)
    adapter = CloudAdapter(connection_manager=connection_manager)
    authorization = Authorization(storage, connection_manager, **agents_sdk_config)
    agent_app = AgentApplication[TurnState](
        storage=storage,
        adapter=adapter,
        authorization=authorization,
        **agents_sdk_config.get("AGENTAPPLICATION", {}),
    )
    adapter.on_turn_error = _default_error_handler

    proactive_raw = agents_sdk_config.get("PROACTIVEMESSAGING", {})
    settings = ProactiveMessagingSettings.from_dict(proactive_raw)
    messenger = ProactiveMessenger(adapter, settings)

    middlewares = []
    agent_config = connection_manager.get_default_connection_configuration()
    if not agent_config:
        raise ValueError("SERVICE_CONNECTION settings are missing.")
    # middlewares.append(jwt_authorization_middleware)

    app = web.Application(middlewares=middlewares)
    app["adapter"] = adapter
    app["agent_app"] = agent_app
    app["messenger"] = messenger
    app["agent_configuration"] = agent_config

    app.router.add_get("/", _handle_root)
    app.router.add_get("/healthz", _handle_health)
    app.router.add_post("/api/createconversation", _handle_create_conversation)
    app.router.add_post("/api/sendmessage", _handle_send_message)

    return app


async def _handle_root(request: web.Request) -> web.Response:
    return web.json_response({"status": "ready", "sample": "proactive-messaging"})


async def _handle_health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def _handle_create_conversation(request: web.Request) -> web.Response:
    messenger: ProactiveMessenger = request.app["messenger"]
    payload = await _read_optional_json(request)

    message = payload.get("message") or payload.get("Message")
    user_aad_object_id = payload.get("userAadObjectId") or payload.get(
        "UserAadObjectId"
    )

    try:
        conversation_id = await messenger.create_conversation(
            message=message, user_aad_object_id=user_aad_object_id
        )
    except ValueError as exc:
        return web.json_response(
            {
                "status": "Error",
                "error": {
                    "code": "Validation",
                    "message": str(exc),
                },
            },
            status=400,
        )
    except Exception as exc:  # pragma: no cover - sample logging
        logging.exception("Create conversation failed")
        return web.json_response(
            {
                "status": "Error",
                "error": {
                    "code": "ServerError",
                    "message": str(exc),
                },
            },
            status=500,
        )

    return web.json_response(
        {
            "conversationId": conversation_id,
            "status": "Created",
        },
        status=201,
    )


async def _handle_send_message(request: web.Request) -> web.Response:
    messenger: ProactiveMessenger = request.app["messenger"]
    payload = await _read_optional_json(request)

    conversation_id = payload.get("conversationId") or payload.get("ConversationId")
    message = payload.get("message") or payload.get("Message")

    if not conversation_id or not message:
        return web.json_response(
            {
                "status": "Error",
                "error": {
                    "code": "Validation",
                    "message": "conversationId and message are required",
                },
            },
            status=400,
        )

    try:
        await messenger.send_message(conversation_id, message)
    except ValueError as exc:
        return web.json_response(
            {
                "status": "Error",
                "error": {
                    "code": "Validation",
                    "message": str(exc),
                },
            },
            status=400,
        )
    except Exception as exc:  # pragma: no cover - sample logging
        logging.exception("Send message failed")
        return web.json_response(
            {
                "status": "Error",
                "error": {
                    "code": "ServerError",
                    "message": str(exc),
                },
            },
            status=500,
        )

    return web.json_response(
        {
            "conversationId": conversation_id,
            "status": "Delivered",
        }
    )


async def _default_error_handler(context: TurnContext, error: Exception) -> None:
    logging.exception("Adapter pipeline failure", exc_info=error)
    await context.send_activity(
        "The proactive messaging agent encountered an unexpected error."
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app = create_app()

    host = environ.get("HOST", "localhost")
    port = int(environ.get("PORT", "5199"))

    web.run_app(app, host=host, port=port)


if __name__ == "__main__":
    main()
