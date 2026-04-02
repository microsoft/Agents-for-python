"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from typing import Optional

from microsoft_agents.activity import (
    ChannelAccount,
    Channels,
    ConversationAccount,
    ConversationReference,
)


def _service_url_for_channel(channel_id: str) -> str:
    """Return the default service URL for a given channel.

    :param channel_id: The channel identifier (e.g. ``"msteams"``).
    :type channel_id: str
    :return: The service URL for that channel.
    :rtype: str
    """
    if channel_id == Channels.ms_teams or channel_id == "msteams":
        return "https://smba.trafficmanager.net/teams/"
    return f"https://{channel_id}.botframework.com/"


class ConversationReferenceBuilder:
    """
    Fluent builder for :class:`~microsoft_agents.activity.ConversationReference`.

    Typical usage::

        reference = (
            ConversationReferenceBuilder
            .create("msteams", "19:conversation-id@thread.v2")
            .with_agent("28:agent-app-id", "My Agent")
            .with_user("user-aad-oid", "User Display Name")
            .with_locale("en-US")
            .build()
        )
    """

    def __init__(self) -> None:
        self._channel_id: Optional[str] = None
        self._conversation_id: Optional[str] = None
        self._service_url: Optional[str] = None
        self._agent_id: Optional[str] = None
        self._agent_name: Optional[str] = None
        self._user_id: Optional[str] = None
        self._user_name: Optional[str] = None
        self._activity_id: Optional[str] = None
        self._locale: Optional[str] = None

    # ------------------------------------------------------------------
    # Entry-point factories
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        channel_id: str,
        conversation_id: str,
    ) -> "ConversationReferenceBuilder":
        """
        Start building a :class:`~microsoft_agents.activity.ConversationReference`
        from a channel ID and an existing conversation ID.

        :param channel_id: The channel identifier (e.g. ``"msteams"``).
        :type channel_id: str
        :param conversation_id: The existing conversation ID.
        :type conversation_id: str
        :return: A builder pre-populated with the channel and conversation.
        :rtype: :class:`ConversationReferenceBuilder`
        """
        builder = cls()
        builder._channel_id = channel_id
        builder._conversation_id = conversation_id
        return builder

    @classmethod
    def create_for_agent(
        cls,
        agent_client_id: str,
        channel_id: str,
        service_url: Optional[str] = None,
    ) -> "ConversationReferenceBuilder":
        """
        Start building a :class:`~microsoft_agents.activity.ConversationReference`
        from an agent application ID and channel.

        For the ``msteams`` channel the agent ID is automatically prefixed with
        ``28:`` as required by Teams.

        :param agent_client_id: The agent's AAD application ID.
        :type agent_client_id: str
        :param channel_id: The channel identifier.
        :type channel_id: str
        :param service_url: Override the service URL.  When ``None`` the default
            URL for the channel is used.
        :type service_url: Optional[str]
        :return: A builder pre-populated for the agent.
        :rtype: :class:`ConversationReferenceBuilder`
        """
        builder = cls()
        builder._channel_id = channel_id
        builder._service_url = service_url or _service_url_for_channel(channel_id)

        # Teams requires the "28:" prefix on agent IDs.
        if channel_id == Channels.ms_teams or channel_id == "msteams":
            builder._agent_id = f"28:{agent_client_id}"
        else:
            builder._agent_id = agent_client_id

        return builder

    # ------------------------------------------------------------------
    # Fluent setters
    # ------------------------------------------------------------------

    def with_agent(
        self,
        agent_id: str,
        agent_name: Optional[str] = None,
    ) -> "ConversationReferenceBuilder":
        """
        Set the agent (bot) account on the reference.

        :param agent_id: The agent's channel account ID.
        :type agent_id: str
        :param agent_name: Optional display name.
        :type agent_name: Optional[str]
        :return: ``self`` for chaining.
        :rtype: :class:`ConversationReferenceBuilder`
        """
        self._agent_id = agent_id
        self._agent_name = agent_name
        return self

    def with_user(
        self,
        user_id: str,
        user_name: Optional[str] = None,
    ) -> "ConversationReferenceBuilder":
        """
        Set the user account on the reference.

        :param user_id: The user's channel account ID.
        :type user_id: str
        :param user_name: Optional display name.
        :type user_name: Optional[str]
        :return: ``self`` for chaining.
        :rtype: :class:`ConversationReferenceBuilder`
        """
        self._user_id = user_id
        self._user_name = user_name
        return self

    def with_service_url(self, service_url: str) -> "ConversationReferenceBuilder":
        """
        Override the service URL.

        :param service_url: The service URL to use.
        :type service_url: str
        :return: ``self`` for chaining.
        :rtype: :class:`ConversationReferenceBuilder`
        """
        self._service_url = service_url
        return self

    def with_activity_id(self, activity_id: str) -> "ConversationReferenceBuilder":
        """
        Set the activity ID on the reference.

        :param activity_id: The activity ID.
        :type activity_id: str
        :return: ``self`` for chaining.
        :rtype: :class:`ConversationReferenceBuilder`
        """
        self._activity_id = activity_id
        return self

    def with_locale(self, locale: str) -> "ConversationReferenceBuilder":
        """
        Set the locale on the reference.

        :param locale: BCP-47 locale string (e.g. ``"en-US"``).
        :type locale: str
        :return: ``self`` for chaining.
        :rtype: :class:`ConversationReferenceBuilder`
        """
        self._locale = locale
        return self

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self) -> ConversationReference:
        """
        Construct the :class:`~microsoft_agents.activity.ConversationReference`.

        :raises ValueError: If ``channel_id`` has not been set.
        :return: The built conversation reference.
        :rtype: :class:`~microsoft_agents.activity.ConversationReference`
        """
        if not self._channel_id:
            raise ValueError("ConversationReferenceBuilder: channel_id is required.")

        service_url = self._service_url or _service_url_for_channel(self._channel_id)

        agent = (
            ChannelAccount(id=self._agent_id, name=self._agent_name)
            if self._agent_id
            else None
        )
        user = (
            ChannelAccount(id=self._user_id, name=self._user_name)
            if self._user_id
            else None
        )

        return ConversationReference(
            channel_id=self._channel_id,
            conversation=ConversationAccount(id=self._conversation_id or ""),
            service_url=service_url,
            bot=agent,
            user=user,
            activity_id=self._activity_id,
            locale=self._locale,
        )
