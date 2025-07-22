from uuid import uuid4
from functools import partial
from typing import Type

from microsoft.agents.activity import AgentsModel
from microsoft.agents.hosting.core.storage import Storage, StoreItem

from .agent_conversation_reference import AgentConversationReference
from .conversation_id_factory_protocol import ConversationIdFactoryProtocol


def _implement_store_item_for_agents_model_cls(model_instance: AgentsModel):
    instance_cls = type(model_instance)
    if not isinstance(model_instance, StoreItem):
        instance_cls = type(model_instance)
        setattr(
            instance_cls,
            "store_item_to_json",
            partial(model_instance.model_dump, mode="json", exclude_none=True),
        )
        instance_cls.from_json_to_store_item = classmethod(instance_cls.model_validate)


class ConversationIdFactory(ConversationIdFactoryProtocol):
    def __init__(self, storage: Storage) -> None:
        if not storage:
            raise ValueError("ConversationIdFactory.__init__(): storage cannot be None")
        self._storage = storage

    async def create_conversation_id(self, options) -> str:
        if not options:
            raise ValueError(
                "ConversationIdFactory.create_conversation_id(): options cannot be None"
            )

        conversation_reference = options.activity.get_conversation_reference()
        agent_conversation_id = str(uuid4())

        agent_conversation_reference = AgentConversationReference(
            conversation_reference=conversation_reference,
            oauth_scope=options.from_oauth_scope,
        )

        _implement_store_item_for_agents_model_cls(agent_conversation_reference)

        conversation_info = {agent_conversation_id: agent_conversation_reference}
        await self._storage.write(conversation_info)

        return agent_conversation_id

    async def get_agent_conversation_reference(
        self, agent_conversation_id
    ) -> AgentConversationReference:
        if not agent_conversation_id:
            raise ValueError(
                "ConversationIdFactory.get_agent_conversation_reference(): agent_conversation_id cannot be None"
            )

        storage_record = await self._storage.read(
            [agent_conversation_id], target_cls=AgentConversationReference
        )

        return storage_record[agent_conversation_id]

    async def delete_conversation_reference(self, agent_conversation_id):
        await self._storage.delete([agent_conversation_id])
