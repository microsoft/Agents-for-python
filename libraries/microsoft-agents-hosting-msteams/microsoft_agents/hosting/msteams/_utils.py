"""Internal utility helpers for the Teams hosting layer."""

import re

from typing import Any, Optional

from http import HTTPStatus

from microsoft_teams.api.models.channel_data import ChannelData

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    InvokeResponse,
)
from microsoft_agents.hosting.core import TurnContext

from .type_defs import CommandSelector


def _get_channel_data(context: TurnContext) -> ChannelData:
    """Extract and parse Teams channel data from the activity's channel_data.

    :param context: The current turn context.
    :return: A :class:`ChannelData` instance parsed from channel_data.
    :raises ValueError: If channel_data is absent.
    :raises pydantic.ValidationError: If channel_data cannot be deserialized.
    """
    data = context.activity.channel_data
    if data is None:
        raise ValueError("channel_data is required")
    if isinstance(data, ChannelData):
        return data
    return ChannelData.model_validate(data)


def _match_selector(selector: CommandSelector, value: Optional[str]) -> bool:
    """Return True if *value* matches *selector*.

    :param selector: A literal string, compiled regex, or None. None matches anything.
    :param value: The string to test. None never matches a non-None selector.
    """
    if selector is None:
        return True
    if value is None:
        return False
    if isinstance(selector, str):
        return selector == value
    return bool(re.fullmatch(selector, value))


def _get_channel_event_type(context: TurnContext) -> Optional[str]:
    """Extract the Teams channel event type from the activity's channel_data.

    :param context: The current turn context.
    :return: The event type string (e.g. ``"channelCreated"``), or None if absent.
    """
    data = context.activity.channel_data
    if data is None:
        return None
    if isinstance(data, dict):
        return data.get("eventType") or data.get("event_type")
    return getattr(data, "event_type", None)


async def _send_invoke_response(context: TurnContext, body: Any = None) -> None:
    """Send an invoke response activity with HTTP 200 and an optional body.

    Pydantic models are serialised via ``model_dump``; all other values are passed
    through as-is.

    :param context: The current turn context.
    :param body: Optional response payload. Pydantic models are auto-serialised to JSON.
    """
    serialized_body = None
    if body is not None:
        if hasattr(body, "model_dump"):
            serialized_body = body.model_dump(
                mode="json", by_alias=True, exclude_none=True
            )
        else:
            serialized_body = body
    await context.send_activity(
        Activity(
            type=ActivityTypes.invoke_response,
            value=InvokeResponse(status=int(HTTPStatus.OK), body=serialized_body),
        )
    )
