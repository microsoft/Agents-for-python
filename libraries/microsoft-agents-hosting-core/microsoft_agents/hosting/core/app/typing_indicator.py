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
    """

    _intervalMs: float
    _task: Optional[asyncio.Task] = None
    _running: bool = False

    def __init__(self, intervalSeconds=1) -> None:
        # Convert milliseconds to seconds for asyncio.sleep
        self._intervalMs = intervalSeconds / 1000.0

    async def start(self, context: TurnContext) -> None:
        if self._running:
            return

        logger.debug(f"Starting typing indicator with interval: {self._intervalMs} ms")
        self._running = True
        self._task = asyncio.create_task(self._typing_loop(context))

    async def stop(self) -> None:
        if self._running:
            logger.debug("Stopping typing indicator")
            self._running = False
            if self._task and not self._task.done():
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            self._task = None

    async def _typing_loop(self, context: TurnContext):
        """Continuously send typing indicators at the specified interval."""
        try:
            while self._running:
                try:
                    logger.debug("Sending typing activity")
                    await context.send_activity(Activity(type=ActivityTypes.typing))
                except Exception as e:
                    logger.error(f"Error sending typing activity: {e}")
                    self._running = False
                    break

                # Check _running again before sleeping to ensure clean shutdown
                if self._running:
                    # Wait for the interval before sending the next typing indicator
                    await asyncio.sleep(self._intervalMs)
        except asyncio.CancelledError:
            logger.debug("Typing indicator loop cancelled")
            raise
            raise
