# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import ABC, abstractmethod
from collections.abc import Iterable

from .scopes.memory_scope import MemoryScope


class ComponentMemoryScopesBase(ABC):
    
    @abstractmethod
    def get_memory_scopes(self) -> Iterable[MemoryScope]:
        raise NotImplementedError()
