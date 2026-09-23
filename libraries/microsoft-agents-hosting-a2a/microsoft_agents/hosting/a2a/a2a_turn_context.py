# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

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
        """Initialize the A2A turn context.

        :param adapter_or_context: The channel service adapter or existing turn context.
        :param app: The agent application instance.
        :param activity: The activity for the turn context.
        :param identity: The claims identity for the turn context.
        """

        if isinstance(adapter_or_context, TurnContext):
            super().__init__(adapter_or_context)
            self._original = adapter_or_context
        else:
            super().__init__(adapter_or_context, activity, identity)
            self._original = self

        self._app = app
        self._turn_state = self.turn_state
        self._activity.__class__ = A2AActivity
        self._a2a_activity = cast(A2AActivity, self._activity)
        self._client = A2AClient(self)

    @property
    def client(self) -> A2AClient:
        """Get the A2A client associated with this turn context."""
        return self._client

    @property
    def responded(self) -> bool:
        """Check if the turn context has already sent a response."""
        return self._original.responded

    @responded.setter
    def responded(self, value: bool):
        """Set the responded status for the turn context."""
        self._original.responded = value

    @property
    def streaming_response(self):
        """Get the streaming response associated with the turn context."""
        return self._original.streaming_response

    @property
    def activity(self) -> A2AActivity:
        """Get the A2A activity associated with the turn context."""
        return self._a2a_activity
