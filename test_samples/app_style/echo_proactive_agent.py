# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import logging
from dataclasses import dataclass
from os import environ, path
from typing import Any

from dotenv import load_dotenv

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ConversationReference,
    EndOfConversationCodes,
    MessageFactory,
    load_configuration_from_env,
)
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    AgentApplication,
    Authorization,
    ConversationState,
    MemoryStorage,
    TurnContext,
    TurnState,
)
from microsoft_agents.hosting.core.app._routes import RouteRank
from microsoft_agents.hosting.core.authorization import ClaimsIdentity
from microsoft_agents.hosting.core.storage import StoreItem

from shared import start_server

logger = logging.getLogger(__name__)


@dataclass
class ConversationReferenceRecord(StoreItem):
    """Persistable envelope for a conversation reference and associated identity."""

    claims: dict[str, str]
    is_authenticated: bool
    authentication_type: str | None
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

    def store_item_to_json(self) -> dict[str, Any]:
        return {
            "claims": dict(self.claims),
            "is_authenticated": self.is_authenticated,
            "authentication_type": self.authentication_type,
            "reference": self.reference.model_dump(mode="json"),
        }

    @staticmethod
    def from_json_to_store_item(
        json_data: dict[str, Any]
    ) -> "ConversationReferenceRecord":
        reference_data = json_data.get("reference")
        if not reference_data:
            raise ValueError("Conversation reference payload is missing.")
        reference = ConversationReference.model_validate(reference_data)
        return ConversationReferenceRecord(
            claims=json_data.get("claims", {}),
            is_authenticated=json_data.get("is_authenticated", False),
            authentication_type=json_data.get("authentication_type"),
            reference=reference,
        )


class EchoSkill(AgentApplication[TurnState]):
    """AgentApplication equivalent of the Copilot Studio Echo skill sample."""

    def __init__(
        self,
        *,
        storage: MemoryStorage,
        adapter: CloudAdapter,
        authorization: Authorization,
        connection_manager: MsalConnectionManager,
        **options: Any,
    ) -> None:
        super().__init__(
            connection_manager=connection_manager,
            storage=storage,
            adapter=adapter,
            authorization=authorization,
            **options,
        )

        self._storage = storage
        self._conversation_state = ConversationState(storage)

        self.conversation_update("membersAdded")(self._welcome_message)
        self.activity(ActivityTypes.end_of_conversation)(
            self._handle_end_of_conversation
        )
        self.activity(ActivityTypes.message, rank=RouteRank.LAST)(self._on_message)
        self.error(self._handle_turn_error)

    async def _welcome_message(
        self, context: TurnContext, _: TurnState
    ) -> None:  # pragma: no cover - sample behaviour
        for member in context.activity.members_added or []:
            recipient_id = context.activity.recipient.id if context.activity.recipient else None
            if member.id != recipient_id:
                await context.send_activity("Hi, This is EchoSkill")

    async def _handle_end_of_conversation(
        self, context: TurnContext, state: TurnState
    ) -> None:
        await state.conversation.delete(context)
        conversation = context.activity.conversation
        if conversation and conversation.id:
            await self._storage.delete([ConversationReferenceRecord.get_key(conversation.id)])

    async def _on_message(self, context: TurnContext, state: TurnState) -> None:
        text = context.activity.text or ""
        if "end" in text:
            await context.send_activity("(EchoSkill) Ending conversation...")
            end_activity = Activity.create_end_of_conversation_activity()
            end_activity.code = EndOfConversationCodes.completed_successfully
            await context.send_activity(end_activity)
            await state.conversation.delete(context)
            return

        record = ConversationReferenceRecord.from_context(context)
        await self._storage.write({record.key: record})  # Keep reference for proactive sends.

        await context.send_activity(MessageFactory.text(f"(EchoSkill): {text}"))
        await context.send_activity(
            MessageFactory.text('(EchoSkill): Say "end" and I\'ll end the conversation.')
        )
        await state.save(context)

    async def _handle_turn_error(
        self, context: TurnContext, error: Exception
    ) -> None:  # pragma: no cover - sample logging
        logger.exception("Unhandled error during turn", exc_info=error)

        await self._conversation_state.load(context)
        await self._conversation_state.delete(context)

        await context.send_activity(
            MessageFactory.text(f"Error during turn, ending conversation ({error})")
        )
        end_activity = Activity.create_end_of_conversation_activity()
        end_activity.code = EndOfConversationCodes.error
        end_activity.text = str(error)
        await context.send_activity(end_activity)

    async def send_activity_to_conversation(
        self, conversation_id: str, activity: Activity
    ) -> bool:
        if not conversation_id or not activity:
            return False

        key = ConversationReferenceRecord.get_key(conversation_id)
        items = await self._storage.read([key], target_cls=ConversationReferenceRecord)
        record = items.get(key)
        if not record:
            return False

        continuation_activity = record.reference.get_continuation_activity()

        async def _callback(turn_context: TurnContext) -> None:
            await turn_context.send_activity(activity)

        await self.adapter.continue_conversation_with_claims(
            record.to_identity(), continuation_activity, _callback
        )
        return True


@dataclass
class SendActivityRequest:
    conversation_id: str
    activity: Activity

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SendActivityRequest":
        conversation_id = payload.get("conversationId") or payload.get("conversation_id")
        activity_payload = payload.get("activity")
        if not conversation_id or not activity_payload:
            raise ValueError("conversationId and activity are required.")
        activity = Activity.model_validate(activity_payload)
        return cls(conversation_id=conversation_id, activity=activity)


load_dotenv(path.join(path.dirname(__file__), ".env"))

agents_sdk_config = load_configuration_from_env(environ)

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

ECHO_SKILL = EchoSkill(
    storage=STORAGE,
    adapter=ADAPTER,
    authorization=AUTHORIZATION,
    connection_manager=CONNECTION_MANAGER,
    **agents_sdk_config.get("AGENTAPPLICATION", {}),
)


async def send_activity_to_conversation(
    conversation_id: str, activity: Activity
) -> bool:
    """Module-level convenience wrapper matching the C# sample signature."""

    return await ECHO_SKILL.send_activity_to_conversation(conversation_id, activity)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    start_server(
        agent_application=ECHO_SKILL,
        auth_configuration=CONNECTION_MANAGER.get_default_connection_configuration(),
    )


if __name__ == "__main__":
    main()
