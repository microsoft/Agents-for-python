"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations
import logging

from typing import Any, Dict, Optional, Type, TypeVar, cast, Callable, Awaitable
import asyncio

from microsoft.agents.hosting.core.storage import Storage

from microsoft.agents.hosting.core.turn_context import TurnContext
from microsoft.agents.hosting.core.app.state.conversation_state import ConversationState
from microsoft.agents.hosting.core.state import AgentState
from microsoft.agents.hosting.core.app.state.temp_state import TempState
from microsoft.agents.hosting.core.state.user_state import UserState

logger = logging.getLogger(__name__)

ConversationStateT = TypeVar("ConversationStateT", bound=ConversationState)
UserStateT = TypeVar("UserStateT", bound=UserState)
TempStateT = TypeVar("TempStateT", bound=TempState)

T = TypeVar("T")


class TurnState:
    """
    Default Turn State

    This class manages various AgentState objects and provides a simple interface
    for setting and retrieving state values.
    """

    def __init__(self, *agent_states: AgentState) -> None:
        """
        Initializes a new instance of the TurnState class.

        Args:
            agent_states: Initial list of AgentState objects to manage.
        """
        self._scopes: Dict[str, AgentState] = {}

        # Add all provided agent states
        for agent_state in agent_states:
            self._scopes[agent_state.__class__.__name__] = agent_state

        # Ensure TempState is always available
        if not self._try_get_scope(TempState)[0]:
            self._scopes[TempState.SCOPE_NAME] = TempState()

    @classmethod
    def with_storage(cls, storage: Storage, *agent_states: AgentState) -> "TurnState":
        """
        Creates TurnState with default ConversationState and UserState.

        Args:
            storage: Storage to use for the states.
            agent_states: Additional list of AgentState objects to manage.

        Returns:
            A new TurnState instance with the default states.
        """
        logger.debug("Creating TurnState with storage: %s", storage)
        turn_state = cls()

        # Add default states
        turn_state._scopes[ConversationState.__name__] = ConversationState(storage)
        turn_state._scopes[UserState.__name__] = UserState(storage)
        turn_state._scopes[TempState.SCOPE_NAME] = TempState()

        # Add any additional agent states
        for agent_state in agent_states:
            turn_state._scopes[agent_state.__class__.__name__] = agent_state

        return turn_state

    @property
    def conversation(self) -> ConversationState:
        """Gets the conversation state."""
        return self.get_scope(ConversationState)

    @property
    def user(self) -> UserState:
        """Gets the user state."""
        return self.get_scope(UserState)

    @property
    def temp(self) -> TempState:
        """Gets the temporary state."""
        return self.get_scope(TempState)

    def has_value(self, path: str) -> bool:
        """
        Checks if a value exists at the specified path.

        Args:
            path: The path to check, in the format 'scope.property'.

        Returns:
            True if the value exists, False otherwise.
        """
        scope, property_name = self._get_scope_and_path(path)
        scope_obj = self.get_scope_by_name(scope)
        return (
            scope_obj.has_value(property_name)
            if hasattr(scope_obj, "has_value")
            else False
        )

    def get_value(
        self,
        name: str,
        default_value_factory: Optional[Callable[[], T]] = None,
        *,
        target_cls: Type[T] = None,
    ) -> T:
        """
        Gets a value from state.

        Args:
            name: The name of the value to get, in the format 'scope.property'.
            default_value_factory: A function that returns a default value if the value doesn't exist.

        Returns:
            The value, or the default value if it doesn't exist.
        """
        scope, property_name = self._get_scope_and_path(name)
        scope_obj = self.get_scope_by_name(scope)
        if hasattr(scope_obj, "get_value"):
            return scope_obj.get_value(
                property_name, default_value_factory, target_cls=target_cls
            )
        return None

    def set_value(self, path: str, value: Any) -> None:
        """
        Sets a value in state.

        Args:
            path: The path to set, in the format 'scope.property'.
            value: The value to set.
        """
        scope, property_name = self._get_scope_and_path(path)
        scope_obj = self.get_scope_by_name(scope)
        if hasattr(scope_obj, "set_value"):
            scope_obj.set_value(property_name, value)

    def delete_value(self, path: str) -> None:
        """
        Deletes a value from state.

        Args:
            path: The path to delete, in the format 'scope.property'.
        """
        scope, property_name = self._get_scope_and_path(path)
        scope_obj = self.get_scope_by_name(scope)
        if hasattr(scope_obj, "delete_value"):
            scope_obj.delete_value(property_name)

    def get_scope_by_name(self, scope: str) -> AgentState:
        """
        Gets a scope by name.

        Args:
            scope: The name of the scope to get.

        Returns:
            The scope object.

        Raises:
            ValueError: If the scope doesn't exist.
        """
        if scope not in self._scopes:
            raise ValueError(f"Scope '{scope}' not found")
        return self._scopes[scope]

    def get_scope(self, scope_type: Type[T]) -> T:
        """
        Gets a scope by type.

        Args:
            scope_type: The type of scope to get.

        Returns:
            The scope object.

        Raises:
            ValueError: If the scope doesn't exist.
        """
        has_scope, scope_obj = self._try_get_scope(scope_type)
        if has_scope:
            return scope_obj
        raise ValueError(f"Scope '{scope_type.__name__}' not found")

    def _try_get_scope(self, scope_type: Type[T]) -> tuple[bool, Optional[T]]:
        """
        Tries to get a scope by type.

        Args:
            scope_type: The type of scope to get.

        Returns:
            A tuple containing:
                - A boolean indicating whether the scope exists.
                - The scope object if it exists, otherwise None.
        """
        for scope in self._scopes.values():
            if isinstance(scope, scope_type):
                return True, scope
        return False, None

    def add(self, agent_state: AgentState) -> "TurnState":
        """
        Adds a new agent state to the turn state.

        Args:
            agent_state: The agent state to add.

        Returns:
            This instance for chaining.

        Raises:
            ValueError: If the agent state is None.
        """
        if not agent_state:
            raise ValueError("agent_state cannot be None")

        self._scopes[agent_state.__class__.__name__] = agent_state
        return self

    async def load(self, turn_context: TurnContext, force: bool = False) -> None:
        """
        Loads all agent state records in parallel.

        Args:
            turn_context: The turn context.
            force: Whether data should be forced into cache.
        """
        tasks = [
            bs.load(turn_context, force)
            for bs in self._scopes.values()
            if hasattr(bs, "load")
        ]
        await asyncio.gather(*tasks)

    def clear(self, scope: str) -> None:
        """
        Clears a state scope.

        Args:
            scope: The name of the scope to clear.
        """
        scope_obj = self.get_scope_by_name(scope)
        if hasattr(scope_obj, "clear"):
            scope_obj.clear()

    async def save(self, turn_context: TurnContext, force: bool = False) -> None:
        """
        Saves all agent state changes in parallel.

        Args:
            turn_context: The turn context.
            force: Whether data should be forced to save even if no change was detected.
        """
        tasks = [
            bs.save(turn_context, force)
            for bs in self._scopes.values()
            if hasattr(bs, "save")
        ]
        await asyncio.gather(*tasks)

    async def load(self, context: TurnContext, storage: Storage) -> "TurnState":
        """
        Loads a TurnState instance with the default states.

        Args:
            context: The turn context.
            storage: Optional storage to use for the states.

        Returns:
            A new TurnState instance with loaded states.
        """
        conversation, user, temp = (
            ConversationState(storage),
            UserState(storage),
            TempState(),
        )

        await conversation.load(context)
        await user.load(context)
        await temp.load(context)

        self._scopes[ConversationState.__name__] = conversation
        self._scopes[UserState.__name__] = user
        self._scopes[TempState.SCOPE_NAME] = temp

    @staticmethod
    def _get_scope_and_path(name: str) -> tuple[str, str]:
        """
        Gets the scope and property name from a path.

        Args:
            name: The path to parse.

        Returns:
            A tuple containing the scope name and property name.
        """
        scope_end = name.find(".")
        if scope_end == -1:
            return TempState.SCOPE_NAME, name

        return name[:scope_end], name[scope_end + 1 :]
