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
from microsoft_agents.hosting.core.authorization import ClaimsIdentity

from .conversation import Conversation
from .conversation_reference_builder import _service_url_for_channel


class ConversationBuilder:
    """
    Fluent builder for :class:`~microsoft_agents.hosting.core.app.proactive.conversation.Conversation`.

    Typical usage — building from a minimal set of claims::

        conversation = (
            ConversationBuilder
            .create("agent-app-id", "msteams", service_url="https://smba.trafficmanager.net/teams/")
            .with_user("user-aad-oid", "User Display Name")
            .with_conversation("19:thread-id@thread.v2")
            .build()
        )

    Or from an existing :class:`~microsoft_agents.hosting.core.authorization.ClaimsIdentity`::

        conversation = (
            ConversationBuilder
            .create_from_identity(claims_identity, "msteams")
            .with_conversation("19:thread-id@thread.v2")
            .build()
        )
    """

    def __init__(self) -> None:
        self._claims: dict[str, str] = {}
        self._channel_id: Optional[str] = None
        self._service_url: Optional[str] = None
        self._agent_id: Optional[str] = None
        self._agent_name: Optional[str] = None
        self._user_id: Optional[str] = None
        self._user_name: Optional[str] = None
        self._conversation_id: Optional[str] = None
        self._conversation_name: Optional[str] = None
        self._tenant_id: Optional[str] = None
        self._activity_id: Optional[str] = None

    # ------------------------------------------------------------------
    # Entry-point factories
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        agent_client_id: str,
        channel_id: str,
        service_url: Optional[str] = None,
        requestor_id: Optional[str] = None,
    ) -> "ConversationBuilder":
        """
        Start building a :class:`~microsoft_agents.hosting.core.app.proactive.conversation.Conversation`
        from a minimal set of claims.

        :param agent_client_id: The agent's AAD application ID (becomes the ``aud``
            claim and optionally the ``appid`` claim).
        :type agent_client_id: str
        :param channel_id: The channel identifier (e.g. ``"msteams"``).
        :type channel_id: str
        :param service_url: Override the service URL.  Defaults to the canonical
            URL for *channel_id*.
        :type service_url: Optional[str]
        :param requestor_id: If provided, stored as the ``appid`` claim (useful
            when the requestor differs from the audience).
        :type requestor_id: Optional[str]
        :return: A builder pre-populated with the supplied claims.
        :rtype: :class:`ConversationBuilder`
        """
        builder = cls()
        builder._channel_id = channel_id
        builder._service_url = service_url or _service_url_for_channel(channel_id)
        builder._claims["aud"] = agent_client_id
        if requestor_id:
            builder._claims["appid"] = requestor_id

        # Set agent ID with Teams prefix if needed.
        if channel_id == Channels.ms_teams or channel_id == "msteams":
            builder._agent_id = f"28:{agent_client_id}"
        else:
            builder._agent_id = agent_client_id

        return builder

    @classmethod
    def create_from_identity(
        cls,
        identity: ClaimsIdentity,
        channel_id: str,
        service_url: Optional[str] = None,
    ) -> "ConversationBuilder":
        """
        Start building a :class:`~microsoft_agents.hosting.core.app.proactive.conversation.Conversation`
        from a full :class:`~microsoft_agents.hosting.core.authorization.ClaimsIdentity`.

        :param identity: The claims identity to extract claims from.
        :type identity: :class:`~microsoft_agents.hosting.core.authorization.ClaimsIdentity`
        :param channel_id: The channel identifier.
        :type channel_id: str
        :param service_url: Override the service URL.
        :type service_url: Optional[str]
        :return: A builder pre-populated with the identity's claims.
        :rtype: :class:`ConversationBuilder`
        """
        builder = cls()
        builder._channel_id = channel_id
        builder._service_url = service_url or _service_url_for_channel(channel_id)
        builder._claims = Conversation.claims_from_identity(identity)

        app_id = identity.get_app_id()
        if app_id:
            if channel_id == Channels.ms_teams or channel_id == "msteams":
                builder._agent_id = f"28:{app_id}"
            else:
                builder._agent_id = app_id

        return builder

    # ------------------------------------------------------------------
    # Fluent setters
    # ------------------------------------------------------------------

    def with_user(
        self,
        user_id: str,
        user_name: Optional[str] = None,
    ) -> "ConversationBuilder":
        """
        Set the user account.

        :param user_id: The user's channel account ID.
        :type user_id: str
        :param user_name: Optional display name.
        :type user_name: Optional[str]
        :return: ``self`` for chaining.
        :rtype: :class:`ConversationBuilder`
        """
        self._user_id = user_id
        self._user_name = user_name
        return self

    def with_conversation(
        self,
        conversation_id: str,
        conversation_name: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> "ConversationBuilder":
        """
        Set the conversation account details.

        :param conversation_id: The conversation ID.
        :type conversation_id: str
        :param conversation_name: Optional conversation name.
        :type conversation_name: Optional[str]
        :param tenant_id: Optional tenant ID.
        :type tenant_id: Optional[str]
        :return: ``self`` for chaining.
        :rtype: :class:`ConversationBuilder`
        """
        self._conversation_id = conversation_id
        self._conversation_name = conversation_name
        self._tenant_id = tenant_id
        return self

    def with_activity_id(self, activity_id: str) -> "ConversationBuilder":
        """
        Set the activity ID on the underlying conversation reference.

        :param activity_id: The activity ID.
        :type activity_id: str
        :return: ``self`` for chaining.
        :rtype: :class:`ConversationBuilder`
        """
        self._activity_id = activity_id
        return self

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self) -> Conversation:
        """
        Construct the :class:`~microsoft_agents.hosting.core.app.proactive.conversation.Conversation`.

        :raises ValueError: If required fields (``channel_id``, ``conversation_id``) are missing.
        :return: The built :class:`~microsoft_agents.hosting.core.app.proactive.conversation.Conversation`.
        :rtype: :class:`~microsoft_agents.hosting.core.app.proactive.conversation.Conversation`
        """
        if not self._channel_id:
            raise ValueError("ConversationBuilder: channel_id is required.")
        if not self._conversation_id:
            raise ValueError("ConversationBuilder: conversation_id is required.")

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

        reference = ConversationReference(
            channel_id=self._channel_id,
            service_url=self._service_url or _service_url_for_channel(self._channel_id),
            conversation=ConversationAccount(
                id=self._conversation_id,
                name=self._conversation_name,
                tenant_id=self._tenant_id,
            ),
            bot=agent,
            user=user,
            activity_id=self._activity_id,
        )

        return Conversation(claims=self._claims, conversation_reference=reference)
