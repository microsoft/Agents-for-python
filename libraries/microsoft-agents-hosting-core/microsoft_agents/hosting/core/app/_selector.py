# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import re

from microsoft_agents.activity import ActivityTypes, ChannelId
from microsoft_agents.hosting.core import TurnContext
from ._type_defs import RouteSelector, TextSelector
from ._utils import _matches_text


def _text_selector(
    select: str | re.Pattern[str] | list[str | re.Pattern[str]],
) -> RouteSelector:
    """Creates a route selector that matches the activity text against the selection criteria.

    Strings must match the text exactly; regex patterns must fully match it.

    :param select: A string, regex pattern, or a list of strings/regex patterns to match against.
    :return: A route selector function that returns True if the activity text matches any of the selection criteria.
    """

    def __selector(context: TurnContext) -> bool:
        """Selector function that checks if the given text matches the selection criteria."""
        return _matches_text(select, context.activity.text or "")

    return __selector


def _event_selector(event_selector: TextSelector | None) -> RouteSelector:
    """Creates a route selector that matches the given event name.

    :param event_selector: The text selector for the event name to match against.
    :return: A route selector function that matches the specified event name.
    """

    def __selector(context: TurnContext) -> bool:
        """Selector function that checks if the given event name matches the selection criteria."""
        if not context.activity.type == ActivityTypes.event:
            return False
        return event_selector is None or _matches_text(
            event_selector, context.activity.name or ""
        )

    return __selector


def _invoke_event_selector(event_selector: TextSelector | None) -> RouteSelector:
    """Creates a route selector that matches the given invoke event name.

    :param event_selector: The text selector for the invoke event name to match against.
    :return: A route selector function that matches the specified invoke event name.
    """

    def __selector(context: TurnContext) -> bool:
        """Selector function that checks if the given invoke event name matches the selection criteria."""
        if not context.activity.type == ActivityTypes.invoke:
            return False
        return event_selector is None or _matches_text(
            event_selector, context.activity.name or ""
        )

    return __selector


def _activity_type_selector(activity_type: str | list[str]) -> RouteSelector:
    """Creates a route selector that matches the given activity type.

    :param activity_type: The activity type or list of activity types to match against.
    :return: A route selector function that matches the specified activity type.
    """
    if isinstance(activity_type, list):
        return lambda context: context.activity.type in activity_type
    return lambda context: context.activity.type == activity_type


def _channel_selector(channel_id: str | ChannelId | None) -> RouteSelector:
    """Creates a route selector that matches the given channel ID.

    :param channel_id: The channel ID to match against.
    :return: A route selector function that matches the specified channel ID.
    """

    norm_channel_id = ChannelId(channel_id) if channel_id is not None else None

    if norm_channel_id is None:
        return lambda context: True
    else:

        def __selector(context: TurnContext) -> bool:
            """Selector function that checks if the given channel ID matches the selection criteria."""
            if context.activity.channel_id is None:
                return False
            return norm_channel_id.includes(context.activity.channel_id)

        return __selector


def _all_selector(*selectors: RouteSelector) -> RouteSelector:
    """Combines multiple route selectors into one that only passes if all selectors pass.

    :param selectors: A variable number of route selector functions to combine.
    :return: A new route selector function that only passes if all provided selectors pass.
    """

    def selector(context: TurnContext) -> bool:
        return all(sel(context) for sel in selectors)

    return selector


class _SimpleRouteSelector:
    """A simple route selector that combines multiple selection criteria such as channel ID, activity type, and text pattern."""

    def __init__(
        self,
        *,
        channel_id: str | ChannelId | None = None,
        activity_type: str | list[str] | None = None,
        text_pattern: str | re.Pattern[str] | list[str | re.Pattern[str]] | None = None,
    ) -> None:
        """Initializes a simple route selector with optional channel ID, activity type, and text pattern.

        :param channel_id: The channel ID to match against, or None to match any channel.
        :param activity_type: The activity type to match against, or None to match any activity type.
        :param text_pattern: A text pattern or list of patterns to match against the activity text, or None to match any text.
        """

        self._selectors = []
        if channel_id is not None:
            self._selectors.append(_channel_selector(channel_id))
        if activity_type is not None:
            self._selectors.append(_activity_type_selector(activity_type))
        if text_pattern is not None:
            self._selectors.append(_text_selector(text_pattern))

    def __call__(self, context: TurnContext) -> bool:
        """Calls the route selector with the given context.

        :param context: The turn context to evaluate.
        :return: True if all selectors pass for the given context, False otherwise.
        """
        return all(selector(context) for selector in self._selectors)
