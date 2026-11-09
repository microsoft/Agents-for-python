# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from collections.abc import Mapping, MutableMapping

T = TypeVar("T")

_METADATA_PREFIX = "#metadata#"

def _META(s: str) -> str:
    return f"{_METADATA_PREFIX}{s}"

class _Metadata(ABC, Generic[T]):

    @classmethod
    @abstractmethod
    def get(cls, mapping: Mapping) -> T: ...

    @classmethod
    @abstractmethod
    def set(cls, mapping: MutableMapping, value: T) -> None: ...

    @staticmethod
    def is_metadata(key: str) -> bool:
        return key.startswith(_METADATA_PREFIX)

class _RootConfigMetadata(_Metadata[bool]):

    _KEY = _META("isrootconfig")

    @staticmethod
    def get(mapping: Mapping) -> bool:
        return mapping.get(_RootConfigMetadata._KEY, False)

    @staticmethod
    def set(mapping: MutableMapping, value: bool) -> None:
        mapping[_RootConfigMetadata._KEY] = value