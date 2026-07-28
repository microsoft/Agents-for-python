# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from abc import ABC, abstractmethod

from ._type_aliases import JSON


class StoreItem(ABC):
    """Abstract base class for items stored in the storage system."""

    @abstractmethod
    def store_item_to_json(self) -> JSON:
        """Serializes the StoreItem to a JSON-compatible dictionary.

        :return: A JSON-compatible dictionary representation of the StoreItem.
        """
        pass

    @staticmethod
    @abstractmethod
    def from_json_to_store_item(json_data: JSON) -> StoreItem:
        """Deserializes a JSON-compatible dictionary to a StoreItem.

        :param json_data: A JSON-compatible dictionary representation of the StoreItem.
        :return: A StoreItem instance.
        """
        pass
