# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import logging
from typing import Optional

from microsoft_agents.activity import Activity

from .header_value_provider import HeaderValueProvider

logger = logging.getLogger(__name__)

# Source of truth for the agent ID. Placeholder value per the v0.2 header spec.
AGENT_REGISTRAR = "A365"


class AgenticHeaderProvider(HeaderValueProvider):
    """Provides agent identity headers derived from the incoming Activity.

    The headers are only emitted when the Activity represents an agentic request
    (i.e. ``recipient.role`` is ``agenticUser`` or ``agenticAppInstance``). For
    non-agentic requests an empty mapping is returned so that no agent identity
    metadata leaks onto regular outgoing requests.

    The emitted headers are:

    * ``AgentRegistrar`` - source of truth for the agent ID (``A365``).
    * ``AgentID`` - the unique identifier registered in Entra, taken from the
      recipient's ``agentic_app_id``.
    * ``AgentName`` - the human-friendly agent name.
    * ``Agent-Referrer`` - the originator identifier, taken from the incoming
      channel ID.
    """

    def __init__(self, activity: Activity, agent_name: Optional[str] = None) -> None:
        """Initializes a new instance of :class:`AgenticHeaderProvider`.

        :param activity: The incoming activity to derive header values from.
        :type activity: :class:`microsoft_agents.activity.Activity`
        :param agent_name: The human-friendly agent name (typically the
            application class name).
        :type agent_name: Optional[str]
        """
        if activity is None:
            raise ValueError("activity is required")
        self._activity = activity
        self._agent_name = agent_name or ""

    def get_headers(self) -> dict[str, str]:
        """Returns the agent identity headers for agentic requests.

        :return: The agent identity headers, or an empty mapping when the
            activity is not an agentic request.
        :rtype: dict[str, str]
        """
        if not self._activity.is_agentic_request():
            return {}

        def _safe_header_value(value: object) -> str:
            text = "" if value is None else str(value)
            # Prevent CRLF/header injection and normalize whitespace.
            return text.replace("\r", "").replace("\n", "").strip()

        recipient = self._activity.recipient
        headers = {
            "AgentRegistrar": AGENT_REGISTRAR,
            "AgentID": _safe_header_value(
                recipient.agentic_app_id if recipient else None
            ),
            "AgentName": _safe_header_value(self._agent_name),
            "Agent-Referrer": _safe_header_value(self._activity.channel_id),
        }
        logger.debug("Resolved agentic headers: %s", list(headers.keys()))
        return headers
