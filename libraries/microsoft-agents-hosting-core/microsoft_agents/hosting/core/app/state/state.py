"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations
import logging

import json
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, Callable, List, Optional, Type, TypeVar, Union, overload

from microsoft_agents.hosting.core.state.state_property_accessor import (
    StatePropertyAccessor as _StatePropertyAccessor,
)
from microsoft_agents.hosting.core.storage import Storage, StoreItem
from microsoft_agents.hosting.core.turn_context import TurnContext

logger = logging.getLogger(__name__)

T = TypeVar("T")


@overload
def state(_cls: None = ...) -> Callable[[Type[T]], Type[T]]: ...


@overload
def state(_cls: Type[T]) -> Type[T]: ...


def state(
    _cls: Optional[Type[T]] = None,
) -> Union[Callable[[Type[T]], Type[T]], Type[T]]:
    """
    @state\n
    class Example(State):
        ...
    """

    def wrap(cls: Type[T]) -> Type[T]:
        init = cls.__init__

        def __init__(self, *args, **kwargs) -> None:
            State.__init__(self, *args, **kwargs)

            if init is not None:
                init(self, *args, **kwargs)

        cls.__init__ = __init__  # type: ignore[method-assign]

        if not hasattr(cls, "save"):
            cls.save = State.save  # type: ignore[attr-defined]

        return cls

    if _cls is None:
        return wrap

    return wrap(_cls)


class State(dict[str, StoreItem], ABC):
    """
    State
    """

    __key__: str
    """
    The Storage Key
    """

    __deleted__: List[str]
    """
    Deleted Keys
    """

    def __init__(self, *args, **kwargs) -> None:  # pylint: disable=unused-argument
        super().__init__()
        self.__key__ = ""
        self.__deleted__ = []

        # copy public attributes that are not functions
        for name in dir(self):
            value = object.__getattribute__(self, name)

            if not name.startswith("_") and not callable(value):
                self[name] = deepcopy(value)

        for key, value in kwargs.items():
            self[key] = value

    async def save(
        self, _context: TurnContext, storage: Optional[Storage] = None
    ) -> None:
        """
        Saves The State to Storage

        :param _context: the turn context.
        :type _context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        :param storage: storage to save to.
        :type storage: Optional[:class:`microsoft_agents.hosting.core.storage.Storage`]
        """

        if not storage or self.__key__ == "":
            return

        data = self.copy()
        del data["__key__"]

        logger.info(f"Saving state {self.__key__}")
        await storage.delete(self.__deleted__)
        await storage.write(
            {
                self.__key__: data,
            }
        )

        self.__deleted__ = []

    @classmethod
    @abstractmethod
    async def load(
        cls, context: TurnContext, storage: Optional[Storage] = None
    ) -> "State":
        """
        Loads The State from Storage

        :param context: the turn context.
        :type context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        :param storage: storage to read from.
        :type storage: Optional[:class:`microsoft_agents.hosting.core.storage.Storage`]
        :return: The loaded state instance.
        :rtype: :class:`microsoft_agents.hosting.core.app.state.state.State`
        """
        return cls()

    def create_property(self, name: str) -> _StatePropertyAccessor:
        """
        Create a property accessor for the given name.

        :param name: The name of the property.
        :type name: str
        :return: A state property accessor for the named property.
        :rtype: :class:`microsoft_agents.hosting.core.state.state_property_accessor.StatePropertyAccessor`
        """
        return StatePropertyAccessor(self, name)

    def __setitem__(self, key: str, item: Any) -> None:
        super().__setitem__(key, item)

        if key in self.__deleted__:
            self.__deleted__.remove(key)

    def __delitem__(self, key: str) -> None:
        if key in self and isinstance(self[key], State):
            self.__deleted__.append(self[key].__key__)

        super().__delitem__(key)

    def __setattr__(self, key: str, value: Any) -> None:
        if key.startswith("_") or callable(value):
            object.__setattr__(self, key, value)
            return

        self[key] = value

    def __getattr__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{key}'"
            ) from exc

    def __getattribute__(self, key: str) -> Any:
        if key in self:
            return self[key]

        return object.__getattribute__(self, key)

    def __delattr__(self, key: str) -> None:
        del self[key]

    def __str__(self) -> str:
        return str({key: value.store_item_to_json() for key, value in self.items()})


class StatePropertyAccessor(_StatePropertyAccessor):
    _name: str
    _state: State

    def __init__(self, state: State, name: str) -> None:
        """
        Initialize the StatePropertyAccessor.

        :param state: The state object to access properties from.
        :type state: :class:`microsoft_agents.hosting.core.app.state.state.State`
        :param name: The name of the property to access.
        :type name: str
        """
        self._name = name
        self._state = state

    async def get(
        self,
        turn_context: TurnContext,
        default_value_or_factory: Optional[
            Union[Any, Callable[[], Optional[Any]]]
        ] = None,
    ) -> Optional[Any]:
        """
        Get the property value from the state.

        :param turn_context: The turn context.
        :type turn_context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        :param default_value_or_factory: Default value or factory function to use if property doesn't exist.
        :type default_value_or_factory: Optional[Union[Any, Callable[[], Optional[Any]]]]
        :return: The property value or default value if not found.
        :rtype: Optional[Any]
        """
        value = self._state[self._name] if self._name in self._state else None

        if value is None and default_value_or_factory is not None:
            if callable(default_value_or_factory):
                value = default_value_or_factory()
            else:
                value = default_value_or_factory

        return value

    async def delete(self, turn_context: TurnContext) -> None:
        """
        Delete the property from the state.

        :param turn_context: The turn context.
        :type turn_context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        """
        del self._state[self._name]

    async def set(self, turn_context: TurnContext, value: Any) -> None:
        """
        Set the property value in the state.

        :param turn_context: The turn context.
        :type turn_context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        :param value: The value to set for the property.
        :type value: Any
        """
        self._state[self._name] = value
