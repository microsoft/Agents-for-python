from uuid import uuid4
from functools import partial
from typing import Type

from microsoft.agents.core.models import AgentsModel
from microsoft.agents.storage import Storage, StoreItem

from .bot_conversation_reference import BotConversationReference
from .conversation_id_factory_protocol import ConversationIdFactoryProtocol


class ConversationIdFactory(ConversationIdFactoryProtocol):
    def __init__(self, storage: Storage) -> None:
        if not storage:
            raise ValueError("ConversationIdFactory.__init__(): storage cannot be None")
        self._storage = storage

    def create_conversation_id(self, options) -> str:
        if not options:
            raise ValueError(
                "ConversationIdFactory.create_conversation_id(): options cannot be None"
            )

        conversation_reference = options.activity.get_conversation_reference()
        bot_conversation_id = str(uuid4())

        bot_conversation_reference = BotConversationReference(
            conversation_reference=conversation_reference,
            oauth_scope=options.from_oauth_scope,
        )

        conversation_info = {bot_conversation_id: bot_conversation_reference}

    def get_bot_conversation_reference(self, bot_conversation_id):
        raise NotImplementedError()

    def delete_conversation_reference(self, bot_conversation_id):
        raise NotImplementedError()

    @staticmethod
    def _implement_store_item_for_agents_model_cls(model_instance: AgentsModel):
        if not isinstance(model_instance, StoreItem):
            instance_cls = type(model_instance)
            setattr(
                instance_cls,
                partial(model_instance.model_dump, mode="json", exclude_none=True),
            )
