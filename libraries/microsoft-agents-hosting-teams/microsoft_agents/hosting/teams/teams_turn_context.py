# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams-specific turn context wrapper."""

from microsoft_agents.hosting.core import AgentApplication, TurnContext


class TeamsTurnContext(TurnContext):
    """A context object for handling Teams-specific turn functionality.

    Wraps a plain :class:`TurnContext` so that Teams-aware route handlers
    receive a typed context without changing the core routing engine.
    """

    def __init__(self, context: TurnContext, app: AgentApplication) -> None:
        """Initialise the Teams turn context from a plain turn context.

        :param context: The base turn context provided by the core runtime.
        :param app: The agent application that is handling the turn.
        """
        super().__init__(context)
        self._context = context
        self._app = app
