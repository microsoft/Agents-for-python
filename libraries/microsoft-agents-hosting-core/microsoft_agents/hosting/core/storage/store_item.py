# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import ABC
from typing import Protocol, runtime_checkable

from ._type_aliases import JSON


class StoreItem(ABC):
    def store_item_to_json(self) -> JSON:
        pass

    @staticmethod
    def from_json_to_store_item(json_data: JSON) -> "StoreItem":
        pass
