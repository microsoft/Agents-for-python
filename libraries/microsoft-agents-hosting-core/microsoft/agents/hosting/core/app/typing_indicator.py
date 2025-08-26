"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations
import logging

from threading import Timer
from typing import Optional

from microsoft.agents.hosting.core import TurnContext
from microsoft.agents.activity import Activity, ActivityTypes

logger = logging.getLogger(__name__)


class TypingIndicator:
    """
    Encapsulates the logic for sending "typing" activity to the user.
    """

    _interval: int
    _timer: Optional[Timer] = None

    def __init__(self, interval=1000) -> None:
        self._interval = interval

    async def start(self, context: TurnContext) -> None:
        if self._timer is not None:
            return

        logger.debug(f"Starting typing indicator with interval: {self._interval} ms")
        func = self._on_timer(context)
        self._timer = Timer(self._interval, func)
        self._timer.start()
        await func()

    def stop(self) -> None:
        if self._timer:
            logger.debug("Stopping typing indicator")
            self._timer.cancel()
            self._timer = None

    def _on_timer(self, context: TurnContext):
        async def __call__():
            try:
                logger.debug("Sending typing activity")
                await context.send_activity(Activity(type=ActivityTypes.typing))
            except Exception as e:
                # TODO: Improve when adding logging
                logger.error(f"Error sending typing activity: {e}")
                self.stop()

        return __call__
