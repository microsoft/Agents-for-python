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

    def __init__(self, context: TurnContext, interval: float = 10.0) -> None:
        self._context: TurnContext = context
        self._interval: float = interval
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
            raise RuntimeError("Typing indicator is already running.")

        logger.debug(
            "Starting typing indicator with interval: %s seconds", self._interval
        )
        self._task = asyncio.create_task(self._run())

    def stop(self) -> None:
        """Stops sending typing indicators."""

        if self._task is None:
            raise RuntimeError("Typing indicator is not running.")

        logger.debug("Stopping typing indicator")
        self._task.cancel()
        self._task = None
