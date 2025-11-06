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

    def __init__(self, intervalSeconds=1) -> None:
        self._intervalSeconds = intervalSeconds
        self._task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._lock = asyncio.Lock()

    async def start(self, context: TurnContext) -> None:
        async with self._lock:
            if self._running:
                return

            logger.debug(
                f"Starting typing indicator with interval: {self._intervalSeconds} seconds"
            )
            self._running = True
            self._task = asyncio.create_task(self._typing_loop(context))

    async def stop(self) -> None:
        async with self._lock:
            if not self._running:
                return

            logger.debug("Stopping typing indicator")
            self._running = False
            task = self._task
            self._task = None

        # Cancel outside the lock to avoid blocking
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def _typing_loop(self, context: TurnContext):
        """Continuously send typing indicators at the specified interval."""
        try:
            while True:
                # Check running status under lock
                async with self._lock:
                    if not self._running:
                        break

                try:
                    logger.debug("Sending typing activity")
                    await context.send_activity(Activity(type=ActivityTypes.typing))
                except Exception as e:
                    logger.error(f"Error sending typing activity: {e}")
                    async with self._lock:
                        self._running = False
                    break

                await asyncio.sleep(self._intervalSeconds)
        except asyncio.CancelledError:
            logger.debug("Typing indicator loop cancelled")
