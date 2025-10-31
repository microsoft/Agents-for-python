"""Echo skill sample that mirrors the Copilot Studio EchoSkill agent."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from os import environ, path
from typing import Any, Dict, Optional

from aiohttp import web
from dotenv import load_dotenv

from microsoft_agents.activity import (
    load_configuration_from_env,
    Activity,
    ConversationReference,
    EndOfConversationCodes,
)
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter, start_agent_process
from microsoft_agents.hosting.core import (
    AgentApplication,
    Authorization,
    MemoryStorage,
    MessageFactory,
    TurnContext,
    TurnState,
)
from microsoft_agents.hosting.core.authorization import ClaimsIdentity
from microsoft_agents.hosting.core.storage import StoreItem


@dataclass
class SendActivityRequest:
    """Request payload used to resume conversations proactively."""

    conversation_id: str
    message: str

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "SendActivityRequest":
        conversation_id = payload.get("conversationId") or payload.get(
            "conversation_id"
        )
        if not conversation_id:
            raise ValueError("conversationId is required.")

        message = payload.get("message")
        if not message:
            raise ValueError("message is required.")

        return cls(conversation_id=conversation_id, message=message)


@dataclass
class ConversationReferenceRecord(StoreItem):
    """Persistent envelope for a conversation reference and associated identity."""

    claims: dict[str, str]
    is_authenticated: bool
    authentication_type: Optional[str]
    reference: ConversationReference

    @staticmethod
    def get_key(conversation_id: str) -> str:
        return f"conversationreferences/{conversation_id}"

    @property
    def key(self) -> str:
        return self.get_key(self.reference.conversation.id)

    @classmethod
    def from_context(cls, context: TurnContext) -> "ConversationReferenceRecord":
        identity = context.identity or ClaimsIdentity({}, False)
        reference = context.activity.get_conversation_reference()
        return cls(
            claims=dict(identity.claims),
            is_authenticated=identity.is_authenticated,
            authentication_type=identity.authentication_type,
            reference=reference,
        )

    def to_identity(self) -> ClaimsIdentity:
        return ClaimsIdentity(
            claims=dict(self.claims),
            is_authenticated=self.is_authenticated,
            authentication_type=self.authentication_type,
        )

    def store_item_to_json(self) -> Dict[str, Any]:
        return {
            "claims": dict(self.claims),
            "is_authenticated": self.is_authenticated,
            "authentication_type": self.authentication_type,
            "reference": self.reference.model_dump(mode="json"),
        }

    @staticmethod
    def from_json_to_store_item(
        json_data: Dict[str, Any],
    ) -> "ConversationReferenceRecord":
        reference_payload = json_data.get("reference")
        if not reference_payload:
            raise ValueError("Conversation reference payload is missing.")

        reference = ConversationReference.model_validate(
            reference_payload, strict=False
        )
        return ConversationReferenceRecord(
            claims=json_data.get("claims", {}),
            is_authenticated=json_data.get("is_authenticated", False),
            authentication_type=json_data.get("authentication_type"),
            reference=reference,
        )


load_dotenv(path.join(path.dirname(__file__), ".env"))
agents_sdk_config = load_configuration_from_env(environ)

storage = MemoryStorage()
connection_manager = MsalConnectionManager(**agents_sdk_config)
adapter = CloudAdapter(connection_manager=connection_manager)
authorization = Authorization(storage, connection_manager, **agents_sdk_config)
AGENT_APP = AgentApplication[TurnState](
    storage=storage,
    adapter=adapter,
    authorization=authorization,
    **agents_sdk_config.get("AGENTAPPLICATION", {}),
)


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, state: TurnState) -> None:
    text = context.activity.text or ""
    if "end" == text:
        await context.send_activity("(EchoSkill) Ending conversation...")
        end_activity = Activity.create_end_of_conversation_activity()
        end_activity.code = EndOfConversationCodes.completed_successfully
        await context.send_activity(end_activity)
        await state.conversation.delete(context)
        conversation = context.activity.conversation
        if conversation and conversation.id:
            await state.conversation._storage.delete(
                [ConversationReferenceRecord.get_key(conversation.id)]
            )
        return

    logging.info(
        f"(EchoSkill) ConversationReference to save: {context.activity.get_conversation_reference().model_dump(mode='json', exclude_unset=True, by_alias=True)} with message: {text}"
    )
    record = ConversationReferenceRecord.from_context(context)
    await state.conversation._storage.write({record.key: record})

    await context.send_activity(MessageFactory.text(f"(EchoSkill): {text}"))


class EchoSkillService:
    def __init__(
        self,
        storage: MemoryStorage,
        adapter: CloudAdapter,
    ) -> None:
        self._storage = storage
        self._adapter = adapter

    async def send_activity_to_conversation(
        self, conversation_id: str, message: str
    ) -> bool:
        if not conversation_id:
            return False

        key = ConversationReferenceRecord.get_key(conversation_id)
        items: Dict[str, ConversationReferenceRecord] = await self._storage.read(
            [key], target_cls=ConversationReferenceRecord
        )
        record = items.get(key)
        if not record:
            return False

        continuation_activity = record.reference.get_continuation_activity()

        async def _callback(turn_context: TurnContext) -> None:
            await turn_context.send_activity(message)

        await self._adapter.continue_conversation_with_claims(
            record.to_identity(), continuation_activity, _callback
        )
        return True


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

    echo_service = EchoSkillService(storage, adapter)
    global SERVICE_INSTANCE
    SERVICE_INSTANCE = echo_service

    app = web.Application()
    app["adapter"] = adapter
    app["agent_app"] = AGENT_APP
    app["echo_service"] = echo_service
    agent_config = connection_manager.get_default_connection_configuration()
    if not agent_config:
        raise ValueError("SERVICE_CONNECTION settings are missing.")
    app["agent_configuration"] = agent_config

    app.router.add_get("/", _handle_root)
    app.router.add_post("/api/messages", _agent_entry_point)
    app.router.add_post("/api/sendactivity", _handle_send_activity)

    return app


async def _handle_root(request: web.Request) -> web.Response:
    return web.json_response({"status": "ready", "sample": "echo-skill"})


async def _agent_entry_point(request: web.Request) -> web.Response:
    agent_app: AgentApplication = request.app["agent_app"]
    adapter: CloudAdapter = request.app["adapter"]
    response = await start_agent_process(request, agent_app, adapter)
    return response or web.Response(status=202)


async def _handle_send_activity(request: web.Request) -> web.Response:
    service: EchoSkillService = request.app["echo_service"]
    payload = await _read_optional_json(request)

    try:
        send_request = SendActivityRequest.from_dict(payload)
    except ValueError as exc:
        return web.json_response(
            {
                "status": "Error",
                "error": {"code": "Validation", "message": str(exc)},
            },
            status=400,
        )

    success = await service.send_activity_to_conversation(
        send_request.conversation_id, send_request.message
    )

    if not success:
        return web.json_response(
            {
                "status": "Error",
                "error": {
                    "code": "NotFound",
                    "message": "Conversation reference not found.",
                },
            },
            status=404,
        )

    return web.json_response(
        {"status": "Delivered", "conversationId": send_request.conversation_id},
        status=202,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app = create_app()

    host = environ.get("HOST", "localhost")
    port = int(environ.get("PORT", "3978"))

    web.run_app(app, host=host, port=port)


if __name__ == "__main__":
    main()
