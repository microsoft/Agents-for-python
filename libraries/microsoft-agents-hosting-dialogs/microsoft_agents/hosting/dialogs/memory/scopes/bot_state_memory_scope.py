# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...dialog_context import DialogContext

from microsoft_agents.hosting.core import AgentState

from .memory_scope import MemoryScope


class BotStateMemoryScope(MemoryScope):
    def __init__(self, agent_state_type: type[AgentState], name: str):
        super().__init__(name, include_in_snapshot=True)
        self.agent_state_type = agent_state_type

    def get_memory(self, dialog_context: "DialogContext") -> object:
        if not dialog_context:
            raise TypeError(f"Expecting: DialogContext, but received None")

        # In the new SDK, after AgentState.load() is called, turn_state contains
        # a CachedAgentState (not the AgentState itself) at the context_service_key.
        # Handle both cases: AgentState (before load) and CachedAgentState (after load).
        turn_state_value = dialog_context.context.turn_state.get(
            self.agent_state_type.__name__
        )
        if turn_state_value is None:
            return None
        if isinstance(turn_state_value, AgentState):
            cached_state = turn_state_value.get_cached_state(dialog_context.context)
            # If get_cached_state() returned AgentState itself (load() skipped turn_state update)
            # or None, the state memory is not yet available.
            if cached_state is None or isinstance(cached_state, AgentState):
                return None
            return cached_state.state
        # It's a CachedAgentState (stored after load() was called)
        return getattr(turn_state_value, "state", None)

    def set_memory(self, dialog_context: "DialogContext", memory: object):
        raise RuntimeError("You cannot replace the root AgentState object")

    async def load(self, dialog_context: "DialogContext", force: bool = False):
        agent_state: AgentState | None = self._get_agent_state(dialog_context)

        if agent_state:
            await agent_state.load(dialog_context.context, force)

    async def save_changes(self, dialog_context: "DialogContext", force: bool = False):
        agent_state: AgentState | None = self._get_agent_state(dialog_context)

        if agent_state:
            await agent_state.save(dialog_context.context, force)

    def _get_agent_state(self, dialog_context: "DialogContext") -> AgentState | None:
        value = dialog_context.context.turn_state.get(
            self.agent_state_type.__name__, None
        )
        # After AgentState.load(), the turn_state key holds CachedAgentState, not AgentState.
        # Return None in that case so callers don't try to call AgentState methods on it.
        if isinstance(value, AgentState):
            return value
        return None
