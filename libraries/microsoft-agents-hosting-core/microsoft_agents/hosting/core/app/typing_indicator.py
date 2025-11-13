"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.activity import Activity, ActivityTypes

logger = logging.getLogger(__name__)


class TypingIndicator:
    """
    Encapsulates the logic for sending "typing" activity to the user.

    Scoped to a single turn of conversation with the user.
    """

    def __init__(self, context: TurnContext, interval_seconds: float = 10.0) -> None:
        """Initializes a new instance of the TypingIndicator class.

        :param context: The turn context.
        :param interval_seconds: The interval in seconds between typing indicators.
        """
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than 0")
        self._context: TurnContext = context
        self._interval: float = interval_seconds
        self._task: Optional[asyncio.Task[None]] = None

    async def _run(self) -> None:
        """Sends typing indicators at regular intervals."""

        running_task = self._task
        try:
            while running_task is self._task:
                await self._context.send_activity(Activity(type=ActivityTypes.typing))
                await asyncio.sleep(self._interval)
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            pass

    def start(self) -> None:
        """Starts sending typing indicators."""

        if self._task is not None:
            logger.warning(
                "Typing indicator is already running for conversation %s",
                self._context.activity.conversation.id,
            )
            return

        logger.debug(
            "Starting typing indicator with interval: %s seconds in conversation %s",
            self._interval,
            self._context.activity.conversation.id,
        )
        self._task = asyncio.create_task(self._run())

    def stop(self) -> None:
        """Stops sending typing indicators."""

        if self._task is None:
            logger.warning(
                "Typing indicator is not running for conversation %s",
                self._context.activity.conversation.id,
            )
            return

        logger.debug(
            "Stopping typing indicator for conversation %s",
            self._context.activity.conversation.id,
        )
        self._task.cancel()
        self._task = None
