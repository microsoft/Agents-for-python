from dataclasses import dataclass, field

from .scopes.memory_scope import MemoryScope
from .path_resolver_base import PathResolverBase


@dataclass
class DialogStateManagerConfiguration:

    path_resolvers: list[PathResolverBase] = field(default_factory=list)
    memory_scopes: list[MemoryScope] = field(default_factory=list)
