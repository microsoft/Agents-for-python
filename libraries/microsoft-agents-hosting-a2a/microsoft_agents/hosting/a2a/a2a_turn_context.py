# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams-specific turn context wrapper."""

from __future__ import annotations

from typing import cast

from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnContext,
)

from .activity import A2AActivity


class A2ATurnContext(TurnContext):
    """A context object for handling A2A-specific turn functionality.

    Wraps a plain :class:`TurnContext` so that Teams-aware route handlers
    receive a typed context without changing the core routing engine.
    """

    def __init__(self, context: TurnContext, app: AgentApplication) -> None:
        """Initialise the Teams turn context from a plain turn context.

        :param context: The base turn context provided by the core runtime.
        :param app: The agent application that is handling the turn.
        """
        super().__init__(context)
        self._app = app
        self._turn_state = context.turn_state

        self._original = context

        self._set_a2a_activity()

    def _set_a2a_activity(self) -> None:
        self._activity.__class__ = A2AActivity
        self._a2a_activity = cast(A2AActivity, self._activity)

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