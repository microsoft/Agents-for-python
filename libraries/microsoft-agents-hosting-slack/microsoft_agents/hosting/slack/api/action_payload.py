"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import ConfigDict

from .slack_model import SlackModel


class ActionPayload(SlackModel):
    """
    Interactive Message / Block Kit action payload from Slack. Sent when a user
    clicks a button or interacts with a block element.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    type: Optional[str] = None
    channel: Optional[Any] = None
    message: Optional[Any] = None
    actions: Optional[Any] = None
