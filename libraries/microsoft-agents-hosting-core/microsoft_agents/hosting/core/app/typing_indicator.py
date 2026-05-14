"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import asyncio
import logging
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.activity import Activity, ActivityTypes, Channels, EntityTypes

logger = logging.getLogger(__name__)

DEFAULT_INITIAL_DELAY_MS = 500
DEFAULT_INTERVAL_MS = 2000


@dataclass
class TypingChannelStrategy:
    """Per-channel timing parameters for the typing indicator.

    :param initial_delay_ms: Delay in milliseconds before the first typing activity.
    :param interval_ms: Interval in milliseconds between subsequent typing activities.
    """

    initial_delay_ms: int = DEFAULT_INITIAL_DELAY_MS
    interval_ms: int = DEFAULT_INTERVAL_MS


@dataclass
class TypingOptions:
    """Configuration options for the automatic typing indicator.

    :param initial_delay_ms: Default delay in milliseconds before the first typing activity.
    :param interval_ms: Default interval in milliseconds between subsequent typing activities.
    :param channel_strategies: Optional per-channel timing overrides keyed by channel ID.
    """

    initial_delay_ms: int = DEFAULT_INITIAL_DELAY_MS
    interval_ms: int = DEFAULT_INTERVAL_MS
    channel_strategies: Dict[str, TypingChannelStrategy] = field(default_factory=dict)

    def __post_init__(self):
        # Apply default channel overrides (matching .NET's M365Copilot default)
        if Channels.copilot_studio.value not in self.channel_strategies:
            self.channel_strategies[Channels.copilot_studio.value] = (
                TypingChannelStrategy(initial_delay_ms=250, interval_ms=1000)
            )

    def get_strategy_for_channel(self, channel_id: str) -> TypingChannelStrategy:
        """Returns the timing strategy for the given channel, falling back to defaults."""
        if channel_id and channel_id in self.channel_strategies:
            return self.channel_strategies[channel_id]
        return TypingChannelStrategy(
            initial_delay_ms=self.initial_delay_ms,
            interval_ms=self.interval_ms,
        )


class TypingIndicator:
    """
    Encapsulates the logic for sending "typing" activity to the user.

    Scoped to a single turn of conversation with the user.

    Automatically stops when a message or streaming activity is about to be
    sent on the same turn, preventing bare typing activities from overlapping
    with real responses.
    """

    _UNSET = object()

    def __init__(
        self,
        context: TurnContext,
        interval_seconds: float = _UNSET,  # type: ignore[assignment]
        typing_options: Optional[TypingOptions] = None,
    ) -> None:
        """Initializes a new instance of the TypingIndicator class.

        :param context: The turn context.
        :param interval_seconds: Interval in seconds between typing indicators.
            When set, overrides the interval from ``typing_options``.
        :param typing_options: Typing timing options including per-channel
            strategies. If not provided, defaults are used. An explicit
            ``interval_seconds`` value takes precedence over the interval
            in ``typing_options`` for backward compatibility.
        """
        options = typing_options or TypingOptions()

        channel_id = (
            context.activity.channel_id.channel if context.activity.channel_id else ""
        ) or ""
        strategy = options.get_strategy_for_channel(channel_id)

        # Legacy parameter overrides the resolved strategy when explicitly set
        interval = (
            interval_seconds
            if interval_seconds is not self._UNSET
            else strategy.interval_ms / 1000.0
        )
        initial_delay = strategy.initial_delay_ms / 1000.0

        if interval <= 0:
            raise ValueError("interval_seconds must be greater than 0")

        self._context: TurnContext = context
        self._interval: float = interval
        self._initial_delay: float = initial_delay
        self._task: Optional[asyncio.Task[None]] = None
        self._last_send: Optional[asyncio.Task[None]] = None
        self._stopped = False

    async def _send_typing(self) -> None:
        """Sends a single typing activity via the adapter, bypassing middleware."""
        ref = self._context.activity.get_conversation_reference()
        typing_activity = TurnContext.apply_conversation_reference(
            deepcopy(Activity(type=ActivityTypes.typing)), ref
        )
        await self._context.adapter.send_activities(self._context, [typing_activity])

    async def _run(self) -> None:
        """Sends typing indicators at regular intervals after an initial delay."""
        try:
            if self._initial_delay > 0:
                await asyncio.sleep(self._initial_delay)

            while not self._stopped:
                send_task = asyncio.ensure_future(self._send_typing())
                self._last_send = send_task
                await send_task
                await asyncio.sleep(self._interval)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.debug(
                "Typing indicator send failed for conversation %s",
                self._context.activity.conversation.id,
                exc_info=True,
            )

    @staticmethod
    def _has_streaminfo(activity: Activity) -> bool:
        """Check if an activity contains a streaminfo entity."""
        if not activity.entities:
            return False
        for entity in activity.entities:
            entity_type = getattr(entity, "type", None)
            if entity_type is None and isinstance(entity, dict):
                entity_type = entity.get("type")
            if entity_type == EntityTypes.STREAM_INFO.value:
                return True
        return False

    def start(self) -> None:
        """Starts sending typing indicators and registers a send-activity hook
        that auto-stops the indicator when a real response is about to be sent."""

        if self._task is not None:
            logger.warning(
                "Typing indicator is already running for conversation %s",
                self._context.activity.conversation.id,
            )
            return

        logger.debug(
            "Starting typing indicator (initial_delay=%.1fs, interval=%.1fs) "
            "for conversation %s",
            self._initial_delay,
            self._interval,
            self._context.activity.conversation.id,
        )

        self._stopped = False
        self._task = asyncio.create_task(self._run())

        # Register hook to auto-stop when a message or streaming activity is sent.
        async def _on_send_activities_handler(ctx, activities, next_handler):
            should_stop = any(
                a.type == ActivityTypes.message or self._has_streaminfo(a)
                for a in activities
            )
            if should_stop:
                await self.stop()
            return await next_handler()

        self._context.on_send_activities(_on_send_activities_handler)

    async def stop(self) -> None:
        """Stops sending typing indicators and waits for any in-flight send."""

        if self._stopped:
            return

        self._stopped = True

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

        # Wait for any in-flight typing send to complete before proceeding.
        if self._last_send and not self._last_send.done():
            try:
                await asyncio.shield(self._last_send)
            except (asyncio.CancelledError, Exception):
                pass
        self._last_send = None
