# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import TypeVar, cast, Any

T = TypeVar("T")


class _ServiceSet:
    """
    Analog of .NET's TurnContextStateCollection
    """

    def __init__(self, service_set: _ServiceSet | None = None) -> None:
        self._state: dict[str, Any] = {}
        if service_set is not None:
            self._state.update(service_set._state)

    def get(self, key: type[T]) -> T | None:
        """
        Gets a value from the state collection.
        :param key:
        :return:
        """
        lookup_key = key.__name__

        val = self._state.get(lookup_key)
        if val is not None:
            if not isinstance(val, key):
                raise TypeError(
                    f"Value for key '{lookup_key}' is not of type {key.__name__}"
                )
            return cast(T, val)
        return None

    def has(self, key: type) -> bool:
        """
        Checks if a value exists in the state collection.
        :param key: Type of the value to check for.
        :return: True if the value exists, False otherwise.
        """
        return key.__name__ in self._state

    def set(self, key: type[T], value: T) -> None:
        """
        Sets a value in the state collection.
        :param key: Type of the value to set.
        :param value: The value to set.
        """
        self._state[key.__name__] = value
