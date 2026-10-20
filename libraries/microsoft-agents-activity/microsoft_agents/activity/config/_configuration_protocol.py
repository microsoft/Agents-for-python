# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import (
    Mapping,
    Protocol,
    runtime_checkable,
)
from typing_extensions import Self

@runtime_checkable
class _ConfigurationProtocol(Protocol):

    @classmethod
    def from_mapping(cls, mapping: Mapping) -> Self:
        ...

class _DictConfigurable(_ConfigurationProtocol, Protocol):

    def __init__(self, data: dict, *args, **kwargs) -> None:
        ...

    @classmethod
    def from_mapping(cls, mapping: Mapping) -> Self:
        return cls(dict(mapping))