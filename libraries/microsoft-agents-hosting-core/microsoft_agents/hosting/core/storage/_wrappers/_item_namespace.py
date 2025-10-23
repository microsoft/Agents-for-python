# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import TypeVar

from ._item_storage import _ItemStorage
from ._storage_namespace import _StorageNamespace

from ..store_item import StoreItem
from ..storage import Storage

StoreItemT = TypeVar("StoreItemT", bound=StoreItem)

class _ItemNamespace(_ItemStorage[StoreItemT]):
    """Wrapper around StorageNamespace to handle single item operations within a namespace."""

    def __init__(self, base_key: str, storage: Storage, item_cls: type[StoreItemT]):
        super().__init__(
            _StorageNamespace(base_key, storage),
            item_cls
        )
