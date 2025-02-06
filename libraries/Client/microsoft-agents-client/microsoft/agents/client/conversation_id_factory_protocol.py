from typing import Protocol
from abc import abstractmethod

from .bot_conversation_reference import BotConversationReference


class ConversationIdFactoryProtocol(Protocol):
    @abstractmethod
    def create_conversation_id(self, options: "ConversationIdFactoryOptions") -> str:
        """
        Creates a conversation ID for a bot conversation.
        :param options: A ConversationIdFactoryOptions instance.
        :return: A unique conversation ID.
        """

    @abstractmethod
    def get_bot_conversation_reference(
        self, bot_conversation_id: str
    ) -> BotConversationReference:
        """
        Gets the BotConversationReference for a conversation ID.
        :param bot_conversation_id: An ID created with create_conversation_id.
        :return: BotConversationReference or None if not found.
        """

    @abstractmethod
    def delete_conversation_reference(self, bot_conversation_id: str) -> None:
        """
        Deletes a bot conversation reference.
        :param bot_conversation_id: A conversation ID created with create_conversation_id.
        """
