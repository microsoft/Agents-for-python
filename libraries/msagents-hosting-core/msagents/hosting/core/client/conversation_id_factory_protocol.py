from typing import Protocol
from abc import abstractmethod

from .agent_conversation_reference import AgentConversationReference
from .conversation_id_factory_options import ConversationIdFactoryOptions


class ConversationIdFactoryProtocol(Protocol):
    @abstractmethod
    async def create_conversation_id(
        self, options: ConversationIdFactoryOptions
    ) -> str:
        """
        Creates a conversation ID for an agent conversation.
        :param options: A ConversationIdFactoryOptions instance.
        :return: A unique conversation ID.
        """

    @abstractmethod
    async def get_agent_conversation_reference(
        self, agent_conversation_id: str
    ) -> AgentConversationReference:
        """
        Gets the AgentConversationReference for a conversation ID.
        :param agent_conversation_id: An ID created with create_conversation_id.
        :return: AgentConversationReference or None if not found.
        """

    @abstractmethod
    async def delete_conversation_reference(self, agent_conversation_id: str) -> None:
        """
        Deletes an agent conversation reference.
        :param agent_conversation_id: A conversation ID created with create_conversation_id.
        """
