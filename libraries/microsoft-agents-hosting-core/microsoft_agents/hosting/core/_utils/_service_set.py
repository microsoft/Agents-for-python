# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import TypeVar, cast, Any

T = TypeVar("T")


class _ServiceSet:
    """
    A class that represents a collection of services, allowing for the storage and retrieval of service instances by their type.
    """

    def __init__(self, service_set: _ServiceSet | None = None) -> None:
        """
        Initializes a new instance of the _ServiceSet class.

        :param service_set: An optional _ServiceSet instance to copy the state from.
        """
        self._state: dict[type, Any] = {}
        if service_set is not None:
            self._state.update(service_set._state)

    def get(self, key: type[T]) -> T | None:
        """
        Gets a value from the state collection.
        :param key:
        :return:
        """
        val = self._state.get(key)
        if val is not None:
            if not isinstance(val, key):
                raise TypeError(
                    f"Value for key '{key.__name__}' is not of type {key.__name__} (got {type(val).__name__})"
                )
            return cast(T, val)
        return None

    def has(self, key: type) -> bool:
        """
        Checks if a value exists in the state collection.
        :param key: Type of the value to check for.
        :return: True if the value exists, False otherwise.
        """
        return key in self._state

    def set(self, key: type[T], value: T) -> None:
        """
        Sets a value in the state collection.
        :param key: Type of the value to set.
        :param value: The value to set.
        """
        self._state[key] = value
