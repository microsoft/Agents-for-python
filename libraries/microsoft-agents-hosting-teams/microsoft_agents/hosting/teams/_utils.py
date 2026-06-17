import re

from typing import Any, Optional

from microsoft_agents.activity import Activity
from microsoft_agents.hosting.core import TurnContext

from .type_defs import (
    CommandSelector
)

def _match_selector(selector: CommandSelector, value: Optional[str]) -> bool:
    if selector is None:
        return True
    if value is None:
        return False
    if isinstance(selector, str):
        return selector == value
    return bool(re.match(selector, value))


def _get_channel_event_type(context: TurnContext) -> Optional[str]:
    data = context.activity.channel_data
    if data is None:
        return None
    if isinstance(data, dict):
        return data.get("eventType") or data.get("event_type")
    return getattr(data, "event_type", None)


async def _send_invoke_response(context: TurnContext, body: Any = None) -> None:
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
