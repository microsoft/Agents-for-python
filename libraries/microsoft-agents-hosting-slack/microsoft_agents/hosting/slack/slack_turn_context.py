"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from typing import cast

from microsoft_agents.hosting.core import AgentApplication, TurnContext

from .api import SlackApi
from .slack_activity import SlackActivity


class SlackTurnContext(TurnContext):
    """A context object for handling Slack-specific turn functionality.

    Wraps a plain :class:`TurnContext` so that Slack-aware route handlers
    receive a typed context without changing the core routing engine.
    Turn state and buffered replies are shared with the original context.
    """

    def __init__(self, context: TurnContext, app: AgentApplication) -> None:
        """Initialise the Slack turn context from a plain turn context.

        :param context: The base turn context provided by the core runtime.
        :param app: The agent application that is handling the turn.
        """
        super().__init__(context)
        self._app = app
        self._turn_state = context.turn_state
        self.buffered_reply_activities = context.buffered_reply_activities

        self._original = context

        self._activity.__class__ = SlackActivity
        self._slack_activity = cast(SlackActivity, self._activity)

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
    def activity(self) -> SlackActivity:
        """The current activity, typed as a :class:`SlackActivity`.

        :return: The turn's activity exposing Slack-specific accessors.
        """
        return self._slack_activity

    @property
    def client(self) -> SlackApi | None:
        """The :class:`SlackApi` client bound to this turn, if any.

        :return: The per-turn :class:`SlackApi` registered on
            ``services`` by :class:`SlackAgentExtension`, or ``None`` if none
            was registered.
        """
        if self.services.has(SlackApi):
            return self.services.get(SlackApi)
        return None
