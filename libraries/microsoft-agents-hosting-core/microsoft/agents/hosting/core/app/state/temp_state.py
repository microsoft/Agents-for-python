"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from typing import Dict, List, Optional, TypeVar, Callable, Any, Generic

from microsoft.agents.hosting.core.storage import Storage

from microsoft.agents.hosting.core.turn_context import TurnContext
from microsoft.agents.hosting.core.app.input_file import InputFile
from microsoft.agents.hosting.core.state import AgentState

T = TypeVar("T")


class TempState(AgentState):
    """
    Default Temp State
    """

    INPUT_FILES_KEY = "inputFiles"
    """Name of the input files key"""

    AUTH_TOKEN_KEY = "authTokens"
    """Name of the auth tokens property"""

    SCOPE_NAME = "temp"
    """State scope name"""

    def __init__(self):
        super().__init__(None, context_service_key=self.SCOPE_NAME)
        self._state: Dict[str, Any] = {}

    @property
    def name(self) -> str:
        """Gets the name of this state scope"""
        return self.SCOPE_NAME

    @property
    def input_files(self) -> List[InputFile]:
        """Downloaded files included in the Activity"""
        return self.get_value(self.INPUT_FILES_KEY, lambda: [])

    @input_files.setter
    def input_files(self, value: List[InputFile]) -> None:
        self.set_value(self.INPUT_FILES_KEY, value)

    def clear(self) -> None:
        """Clears all state values"""
        self._state.clear()

    async def delete_state(self, turn_context: TurnContext, **_) -> None:
        """Deletes all state values asynchronously"""
        self._state.clear()

    def has_value(self, name: str) -> bool:
        """Checks if a value exists in the state with the given name"""
        return name in self._state

    def delete_value(self, name: str) -> None:
        """Removes a value from the state"""
        if name in self._state:
            del self._state[name]

    def get_value(
        self, name: str, default_value_factory: Optional[Callable[[], T]] = None
    ) -> T:
        """Gets a value from the state with the given name, using a factory for default values if not found"""
        if name not in self._state and default_value_factory is not None:
            value = default_value_factory()
            self.set_value(name, value)
            return value
        return self._state.get(name)

    def set_value(self, name: str, value: Any) -> None:
        """Sets a value in the state with the given name"""
        self._state[name] = value

    def get_typed_value(self, type_cls: type) -> Any:
        """Gets a value from the state using the type's full name as the key"""
        return self.get_value(type_cls.__module__ + "." + type_cls.__qualname__)

    def set_typed_value(self, value: Any) -> None:
        """Sets a value in the state using the type's full name as the key"""
        type_cls = type(value)
        self.set_value(type_cls.__module__ + "." + type_cls.__qualname__, value)

    def is_loaded(self) -> bool:
        """Checks if the state is loaded"""
        return True

    async def load(self, turn_context: TurnContext, force: bool = False, **_) -> None:
        """Loads the state asynchronously"""
        pass

    async def save_changes(
        self, turn_context: TurnContext, force: bool = False, **_
    ) -> None:
        """Saves the state changes asynchronously"""
        pass
