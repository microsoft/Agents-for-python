# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Iterable

from microsoft_agents.hosting.dialogs.memory import (
    ComponentMemoryScopesBase,
    ComponentPathResolversBase,
    PathResolverBase,
)
from microsoft_agents.hosting.dialogs.memory.scopes import (
    TurnMemoryScope,
    SettingsMemoryScope,
    DialogMemoryScope,
    DialogContextMemoryScope,
    DialogClassMemoryScope,
    ClassMemoryScope,
    MemoryScope,
    ThisMemoryScope,
    ConversationMemoryScope,
    UserMemoryScope,
)

from microsoft_agents.hosting.dialogs.memory.path_resolvers import (
    AtAtPathResolver,
    AtPathResolver,
    DollarPathResolver,
    HashPathResolver,
    PercentPathResolver,
)


class DialogsComponentRegistration(
    ComponentMemoryScopesBase, ComponentPathResolversBase
):
    def get_memory_scopes(self) -> Iterable[MemoryScope]:
        yield TurnMemoryScope()
        yield SettingsMemoryScope()
        yield DialogMemoryScope()
        yield DialogContextMemoryScope()
        yield DialogClassMemoryScope()
        yield ClassMemoryScope()
        yield ThisMemoryScope()
        yield ConversationMemoryScope()
        yield UserMemoryScope()

    def get_path_resolvers(self) -> Iterable[PathResolverBase]:
        yield AtAtPathResolver()
        yield AtPathResolver()
        yield DollarPathResolver()
        yield HashPathResolver()
        yield PercentPathResolver()
