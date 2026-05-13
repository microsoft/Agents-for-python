"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import ConfigDict

from .slack_model import SlackModel


class SlackResponse(SlackModel):
    """
    Response from a Slack Web API call.

    Named properties cover the fields common to every Slack response. Any
    additional fields returned by a specific method are accessible via
    :meth:`SlackModel.get` using dot-notation paths::

        response = await slack_api.call("chat.postMessage", options, token)
        channel = response.get("channel")
        msg_ts  = response.get("message.ts")
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    ok: bool = False
    error: Optional[str] = None
    warning: Optional[str] = None
    ts: Optional[str] = None
    response_metadata: Optional[Any] = None


class SlackResponseException(Exception):
    """Raised when a Slack Web API call returns a non-2xx status or ``ok=false``."""

    def __init__(self, message: str, response: Optional[SlackResponse] = None) -> None:
        super().__init__(message)
        self.response = response
