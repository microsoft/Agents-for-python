# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from abc import abstractmethod
from copy import deepcopy
from typing import Callable, Dict, Union, Type

from microsoft.agents.hosting.core.storage import Storage, StoreItem

from .state_property_accessor import StatePropertyAccessor
from ..turn_context import TurnContext


class CachedAgentState(StoreItem):
    """
    Internal cached bot state.
    """

    def __init__(self, state: Dict[str, StoreItem | dict] = None):
        if state:
            self.state = state
            self.hash = self.compute_hash()
        else:
            self.state = {}
            self.hash = hash(str({}))

    @property
    def has_state(self) -> bool:
        return bool(self.state)

    @property
    def is_changed(self) -> bool:
        return self.hash != self.compute_hash()

    def compute_hash(self) -> str:
        return hash(str(self.store_item_to_json()))

    def store_item_to_json(self) -> dict:
        if not self.state:
            return {}
        # TODO: Might need to change this check to include Types that implement but not inherit.
        serialized = {
            key: value.store_item_to_json() if isinstance(value, StoreItem) else value
            for key, value in self.state.items()
        }
        return serialized

    @staticmethod
    def from_json_to_store_item(json_data: dict) -> StoreItem:
        return CachedAgentState(json_data)


class AgentState:
    """
    Defines a state management object and automates the reading and writing of
    associated state properties to a storage layer.

    .. remarks::
        Each state management object defines a scope for a storage layer.
        State properties are created within a state management scope, and the Bot Framework
        defines these scopes: :class:`ConversationState`, :class:`UserState`, and :class:`PrivateConversationState`.
        You can define additional scopes for your bot.
    """

    def __init__(self, storage: Storage, context_service_key: str):
        """
        Initializes a new instance of the :class:`BotState` class.

        :param storage: The storage layer this state management object will use to store and retrieve state
        :type storage:  :class:`bptbuilder.activity.Storage`
        :param context_service_key: The key for the state cache for this :class:`BotState`
        :type context_service_key: str

        .. remarks::
            This constructor creates a state management object and associated scope. The object uses
            the :param storage: to persist state property values and the :param context_service_key: to cache state
            within the context for each turn.

        :raises: It raises an argument null exception.
        """
        self.state_key = "state"
        self._storage = storage
        self._context_service_key = context_service_key
        self._cached_state: CachedAgentState = None

    def get_cached_state(self, turn_context: TurnContext) -> CachedAgentState:
        """
        Gets the cached bot state instance that wraps the raw cached data for this "BotState"
        from the turn context.

        :param turn_context: The context object for this turn.
        :type turn_context: :class:`TurnContext`
        :return: The cached bot state instance.
        """
        return turn_context.turn_state.get(self._context_service_key)

    def create_property(self, name: str) -> StatePropertyAccessor:
        """
        Creates a property definition and registers it with this :class:`BotState`.

        :param name: The name of the property
        :type name: str
        :return: If successful, the state property accessor created
        :rtype: :class:`StatePropertyAccessor`
        """
        if not name or not name.strip():
            raise ValueError(
                "AgentState.create_property(): name cannot be None or empty."
            )
        return BotStatePropertyAccessor(self, name)

    def get(self, turn_context: TurnContext) -> Dict[str, StoreItem]:
        cached = self.get_cached_state(turn_context)

        return getattr(cached, "state", None)

    async def load(self, turn_context: TurnContext, force: bool = False) -> None:
        """
        Reads the current state object and caches it in the context object for this turn.

        :param turn_context: The context object for this turn
        :type turn_context: :class:`TurnContext`
        :param force: Optional, true to bypass the cache
        :type force: bool
        """
        storage_key = self.get_storage_key(turn_context)

        if force or not self._cached_state:
            items = await self._storage.read([storage_key], target_cls=CachedAgentState)
            val = items.get(storage_key, CachedAgentState())
            self._cached_state = val
            turn_context.turn_state[self._context_service_key] = val

    async def save(self, turn_context: TurnContext, force: bool = False) -> None:
        """
        Saves the state cached in the current context for this turn.
        If the state has changed, it saves the state cached in the current context for this turn.

        :param turn_context: The context object for this turn
        :type turn_context: :class:`TurnContext`
        :param force: Optional, true to save state to storage whether or not there are changes
        :type force: bool
        """

        if force or (self._cached_state is not None and self._cached_state.is_changed):
            storage_key = self.get_storage_key(turn_context)
            changes: Dict[str, StoreItem] = {storage_key: self._cached_state}
            await self._storage.write(changes)
            self._cached_state.hash = self._cached_state.compute_hash()

    def clear(self, turn_context: TurnContext):
        """
        Clears any state currently stored in this state scope.

        :param turn_context: The context object for this turn
        :type turn_context: :class:`TurnContext`

        :return: None

        .. remarks::
            This function must be called in order for the cleared state to be persisted to the underlying store.
        """
        #  Explicitly setting the hash will mean IsChanged is always true. And that will force a Save.
        cache_value = CachedAgentState()
        cache_value.hash = ""
        self._cached_state = cache_value

    async def delete(self, turn_context: TurnContext) -> None:
        """
        Deletes any state currently stored in this state scope.

        :param turn_context: The context object for this turn
        :type turn_context: :class:`TurnContext`

        :return: None
        """
        turn_context.turn_state.pop(self._context_service_key)

        storage_key = self.get_storage_key(turn_context)
        await self._storage.delete({storage_key})

    @abstractmethod
    def get_storage_key(
        self, turn_context: TurnContext, *, target_cls: Type[StoreItem] = None
    ) -> str:
        raise NotImplementedError()

    def get_value(
        self,
        property_name: str,
        default_value_factory: Callable[[], StoreItem] = None,
        *,
        target_cls: Type[StoreItem] = None,
    ) -> StoreItem:
        """
        Gets the value of the specified property in the turn context.

        :param turn_context: The context object for this turn
        :type turn_context: :class:`TurnContext`
        :param property_name: The property name
        :type property_name: str

        :return: The value of the property
        """
        if not property_name:
            raise TypeError("BotState.get_value(): property_name cannot be None.")

        # if there is no value, this will throw, to signal to IPropertyAccesor that a default value should be computed
        # This allows this to work with value types
        value = (
            self._cached_state.state.get(property_name, None)
            if self._cached_state
            else None
        )

        if not value and default_value_factory:
            # If the value is None and a factory is provided, call the factory to get a default value
            return default_value_factory()

        if target_cls and value:
            # Attempt to deserialize the value if it is not None
            try:
                return target_cls.from_json_to_store_item(value)
            except AttributeError:
                # If the value is not a StoreItem, just return it as is
                pass

        return value

    def delete_value(self, property_name: str) -> None:
        """
        Deletes a property from the state cache in the turn context.

        :param turn_context: The context object for this turn
        :type turn_context: :TurnContext`
        :param property_name: The name of the property to delete
        :type property_name: str

        :return: None
        """
        if not property_name:
            raise TypeError("BotState.delete_property(): property_name cannot be None.")

        if self._cached_state.state.get(property_name):
            del self._cached_state.state[property_name]

    def set_value(self, property_name: str, value: StoreItem) -> None:
        """
        Sets a property to the specified value in the turn context.

        :param turn_context: The context object for this turn
        :type turn_context: :class:`TurnContext`
        :param property_name: The property name
        :type property_name: str
        :param value: The value to assign to the property
        :type value: StoreItem

        :return: None
        """
        if not property_name:
            raise TypeError("BotState.delete_property(): property_name cannot be None.")
        self._cached_state.state[property_name] = value


class BotStatePropertyAccessor(StatePropertyAccessor):
    """
    Defines methods for accessing a state property created in a :class:`BotState` object.
    """

    def __init__(self, bot_state: AgentState, name: str):
        """
        Initializes a new instance of the :class:`BotStatePropertyAccessor` class.

        :param bot_state: The state object to access
        :type bot_state:  :class:`BotState`
        :param name: The name of the state property to access
        :type name: str

        """
        if not bot_state:
            raise TypeError("BotStatePropertyAccessor: bot_state cannot be None.")
        if not name or not name.strip():
            raise ValueError("BotStatePropertyAccessor: name cannot be None or empty.")
        self._bot_state = bot_state
        self._name = name

    @property
    def name(self) -> str:
        """
        The name of the property.
        """
        return self._name

    async def delete(self, turn_context: TurnContext) -> None:
        """
        Deletes the property.

        :param turn_context: The context object for this turn
        :type turn_context: :class:`TurnContext`
        """
        await self._bot_state.load(turn_context, False)
        self._bot_state.delete_value(self._name)

    async def get(
        self,
        turn_context: TurnContext,
        default_value_or_factory: Union[Callable, StoreItem] = None,
        *,
        target_cls: Type[StoreItem] = None,
    ) -> StoreItem:
        """
        Gets the property value.

        :param turn_context: The context object for this turn
        :type turn_context: :class:`TurnContext`
        :param default_value_or_factory: Defines the default value for the property
        """
        await self._bot_state.load(turn_context, False)

        def default_value_factory():
            if callable(default_value_or_factory):
                return default_value_or_factory()
            return deepcopy(default_value_or_factory)

        try:
            result = self._bot_state.get_value(
                self._name,
                default_value_factory=default_value_factory,
                target_cls=target_cls,
            )
            return result
        except:
            # ask for default value from factory
            if not default_value_or_factory:
                return None
            result = (
                default_value_or_factory()
                if callable(default_value_or_factory)
                else deepcopy(default_value_or_factory)
            )
            # save default value for any further calls
            self.set(result)
            return result

    async def set(self, turn_context: TurnContext, value: StoreItem) -> None:
        """
        Sets the property value.

        :param turn_context: The context object for this turn
        :type turn_context: :class:`TurnContext`

        :param value: The value to assign to the property
        """
        await self._bot_state.load(turn_context, False)
        self._bot_state.set_value(self._name, value)
