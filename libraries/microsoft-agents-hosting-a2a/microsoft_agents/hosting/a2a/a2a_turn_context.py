# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams-specific turn context wrapper."""

from __future__ import annotations

from typing import cast

from microsoft_agents.activity import Activity
from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnContext,
    ChannelServiceAdapter,
    ClaimsIdentity,
)

from .activity import A2AActivity

from .a2a_client import A2AClient

class A2ATurnContext(TurnContext):
    """A context object for handling A2A-specific turn functionality.

    Wraps a plain :class:`TurnContext` so that Teams-aware route handlers
    receive a typed context without changing the core routing engine.
    """

    def __init__(
        self,
        adapter_or_context: ChannelServiceAdapter | TurnContext,
        app: AgentApplication,
        activity: Activity | None = None,
        identity: ClaimsIdentity | None = None,
    ) -> None:

        if isinstance(adapter_or_context, TurnContext):
            super().__init__(adapter_or_context)
            self._original = adapter_or_context
        else:
            super().__init__(adapter_or_context, activity, identity)
            self._original = self

        self._app = app
        self._turn_state = self.turn_state
        self._set_a2a_activity()
        self._client = A2AClient(self)

    def _set_a2a_activity(self) -> None:
        self._activity.__class__ = A2AActivity
        self._a2a_activity = cast(A2AActivity, self._activity)

    @property
    def client(self) -> A2AClient:
        return self._client

    @property
    def responded(self) -> bool:
        return self._original.responded

    @responded.setter
    def responded(self, value: bool):
        self._original.responded = value

    @property
    def streaming_response(self):
        return self._original.streaming_response

    @property
    def activity(self) -> A2AActivity:
        return self._a2a_activity