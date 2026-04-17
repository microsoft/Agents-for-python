"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from microsoft_agents.activity import ConversationParameters
from microsoft_agents.hosting.core.authorization import ClaimsIdentity


@dataclass
class CreateConversationOptions:
    """
    Options for :meth:`~microsoft_agents.hosting.core.app.proactive.proactive.Proactive.create_conversation`.

    :param identity: The :class:`~microsoft_agents.hosting.core.authorization.ClaimsIdentity`
        used to authenticate the outbound call.
    :type identity: :class:`~microsoft_agents.hosting.core.authorization.ClaimsIdentity`
    :param channel_id: The target channel identifier (e.g. ``"msteams"``).
    :type channel_id: str
    :param parameters: The :class:`~microsoft_agents.activity.ConversationParameters`
        passed to the channel when creating the conversation.
    :type parameters: :class:`~microsoft_agents.activity.ConversationParameters`
    :param service_url: Optional override for the channel service URL.
    :type service_url: Optional[str]
    :param audience: Optional OAuth audience override.  When ``None`` the
        audience is derived from *identity*.
    :type audience: Optional[str]
    :param store_conversation: When ``True`` the newly created conversation is
        automatically stored via
        :meth:`~microsoft_agents.hosting.core.app.proactive.proactive.Proactive.store_conversation`
        so it can be resumed later.  Defaults to ``False``.
    :type store_conversation: bool
    """

    identity: ClaimsIdentity = field(default=None)
    channel_id: str = field(default="")
    parameters: Optional[ConversationParameters] = field(default=None)
    service_url: Optional[str] = field(default=None)
    audience: Optional[str] = field(default=None)
    store_conversation: bool = field(default=False)

    def validate(self) -> None:
        """
        Raise :exc:`ValueError` if required fields are missing.

        :raises ValueError: If ``identity``, ``channel_id``, ``parameters``,
            or ``service_url`` are absent.
        """
        if not self.identity:
            raise ValueError("CreateConversationOptions.identity is required.")
        if not self.channel_id:
            raise ValueError("CreateConversationOptions.channel_id is required.")
        if not self.parameters:
            raise ValueError("CreateConversationOptions.parameters is required.")
        if not self.service_url:
            raise ValueError("CreateConversationOptions.service_url is required.")
