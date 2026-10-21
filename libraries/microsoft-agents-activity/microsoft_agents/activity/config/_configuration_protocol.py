# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import ABC, abstractmethod
from typing import (
    Mapping,
    Protocol,
    runtime_checkable,
)
from typing_extensions import Self


@runtime_checkable
class _ConfigurationProtocol(Protocol):

    @classmethod
    def from_mapping(cls, _mapping: Mapping) -> Self: ...

class _DictConfigurableProtocol(_ConfigurationProtocol, Protocol):

    def __init__(self, data: dict, *args, **kwargs) -> None: ...

    @classmethod
    def from_mapping(cls, mapping: Mapping) -> Self: ...

class _DictConfigurable(ABC):

    @abstractmethod
    def __init__(self, data: dict, *args, **kwargs) -> None: ...

    @classmethod
    def from_mapping(cls, mapping: Mapping) -> Self:
        return cls(dict(mapping))