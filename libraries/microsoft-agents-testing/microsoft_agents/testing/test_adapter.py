# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""In-memory channel adapter for exercising agent turns in tests.

The objects in this module intentionally model only the parts of a channel that
unit tests usually need: inbound activities are normalized with a test
conversation reference, outbound activities are captured in an in-memory queue,
and OAuth/token operations are backed by a mock user-token client unless a test
provides its own implementation.
"""

import asyncio

from typing import Awaitable, Any

from uuid import uuid4

from datetime import datetime, timezone

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    ChannelId,
    Channels,
    ConversationAccount,
    ConversationParameters,
    ConversationReference,
    InvokeResponse,
    ResourceResponse,
    RoleTypes,
)

from microsoft_agents.hosting.core import (
    ChannelAdapter,
    ClaimsIdentity,
    UserTokenClientBase,
    TurnContext,
)
from .auth import MockUserTokenClient
from .type_def import AgentCallbackHandler, T

from . import _defaults as _DEFAULTS


class TestAdapter(ChannelAdapter):
    """A lightweight adapter for unit-testing agent logic without a real channel.

    ``TestAdapter`` behaves like a channel adapter at the turn-processing
    boundary, but it does not call Connector Service, Teams, or any external
    token service. Instead, it:

    * fills in missing activity fields from a single in-memory
      :class:`ConversationReference`;
    * runs the activity through the normal middleware/agent pipeline;
    * stores activities sent by the agent in :attr:`activity_queue`;
    * exposes a mock :class:`UserTokenClientBase` through ``TurnContext.services``
      so OAuth flows can be tested without a live token service.

    The Python adapter is intentionally smaller than the .NET TestAdapter. It
    does not maintain multiple conversations, does not create real proactive
    conversations, and does not simulate channel-specific delivery behavior
    beyond assigning IDs/timestamps and queueing replies.
    """

    claims_identity: ClaimsIdentity | None
    _activity_queue: list[Activity]
    _queued_requests: list[asyncio.Future[Activity]]

    def __init__(
        self,
        *,
        channel_id: str | ChannelId | None = None,
        conversation: ConversationReference | None = None,
        user_token_client: UserTokenClientBase | None = None
    ) -> None:
        """Create a test adapter with a default or caller-provided conversation.

        :param channel_id: Channel ID to use when creating the default test
            conversation. Ignored when ``conversation`` is supplied.
        :param conversation: Optional conversation reference used to stamp
            inbound activities and create turn contexts.
        :param user_token_client: Optional user-token client test double. When
            omitted, the adapter uses :class:`MockUserTokenClient`.
        """

        channel_id = channel_id or Channels.test

        self._id_counter = 0
        self._user_token_client = user_token_client or MockUserTokenClient()

        if conversation:
            self._conversation = conversation
        else:
            self._conversation = TestAdapter.create_conversation_model(
                channel_id=channel_id,
            )

        self._locale = _DEFAULTS._LOCALE

        self._activity_queue = []
        self._queued_requests = []

    @property
    def conversation(self) -> ConversationReference:
        """Conversation reference used to populate incoming test activities."""
        return self._conversation

    @property
    def locale(self) -> str:
        """Locale copied onto activities created by :meth:`create_activity`."""
        return self._locale

    @locale.setter
    def locale(self, value: str) -> None:
        self._locale = value

    @property
    def activity_queue(self) -> list[Activity]:
        """Activities sent by the agent and captured instead of sent to a channel."""
        return self._activity_queue

    def _gen_id(self) -> str:
        """Return the next deterministic activity ID for this adapter instance."""
        self._id_counter += 1
        return str(self._id_counter)

    @staticmethod
    def create_conversation_model(
        *,
        channel_id: str | ChannelId = Channels.test,
        conv_id: str = _DEFAULTS._CONV_ID,
        conv_name: str = _DEFAULTS._CONV_NAME,
        user_id: str = _DEFAULTS._USER_ID,
        user_name: str = _DEFAULTS._USER_NAME,
        bot_id: str = _DEFAULTS._BOT_ID,
        bot_name: str = _DEFAULTS._BOT_NAME,
        locale: str = _DEFAULTS._LOCALE
    ) -> ConversationReference:
        """Create a conversation reference for tests.

        The returned reference uses the testing service URL and caller-provided
        user, bot, conversation, locale, and channel values. The adapter uses
        this reference to fill activity ``from``, ``recipient``, ``conversation``,
        ``service_url``, and ``channel_id`` fields when a test activity omits
        them.
        """
        return ConversationReference(
            channel_id=ChannelId(channel_id),
            service_url=_DEFAULTS._SERVICE_URL,
            user=ChannelAccount(id=user_id, name=user_name),
            agent=ChannelAccount(id=bot_id, name=bot_name),
            conversation=ConversationAccount(
                is_group=False, id=conv_id, name=conv_name
            ),
            locale=locale,
        )

    def create_turn_context(
        self, activity: Activity, claims_identity: ClaimsIdentity | None = None
    ) -> TurnContext:
        """Create the turn context used by the test adapter.

        The context uses this adapter, the supplied activity, and either the
        supplied identity or :attr:`claims_identity`. It also registers the
        adapter's user-token client in ``context.services`` so OAuth-related
        code can retrieve a token client without contacting a real service.

        :param activity: Activity for the current test turn.
        :param claims_identity: Optional identity for the turn.
        :return: A ``TurnContext`` ready to run through middleware and agent
            logic.
        """

        context = TurnContext(
            self,
            activity,
            identity=claims_identity or self.claims_identity,
        )
        context.services.set(UserTokenClientBase, self._user_token_client)
        return context

    async def process_activity(
        self,
        claims_identity: ClaimsIdentity,
        activity: Activity,
        callback: AgentCallbackHandler,
    ) -> InvokeResponse | None:
        """Process an inbound activity through the test pipeline.

        Missing channel-like fields are populated from :attr:`conversation`:
        activity type defaults to ``message``, channel ID defaults to the test
        conversation channel, ``from`` defaults to the test user, and
        ``recipient``, ``conversation``, and ``service_url`` are replaced with
        the test conversation values. The adapter assigns an activity ID and
        timestamps before invoking middleware and the callback.

        No HTTP request is made and no real channel response is produced; sent
        activities are captured by :meth:`send_activities`.

        :param claims_identity: Identity associated with the inbound activity.
        :param activity: Activity to deliver to the agent.
        :param callback: Turn logic to invoke.
        :return: ``None``; invoke response behavior is not simulated here.
        """

        if not activity.type:
            activity.type = ActivityTypes.message

        if not activity.channel_id:
            activity.channel_id = self.conversation.channel_id

        if (
            not activity.from_property
            or not activity.from_property.id
            or activity.from_property.role == RoleTypes.agent
        ):
            if not self._conversation.user:
                raise ValueError(
                    "Activity must have a 'from' property with a valid user ID and role."
                )
            activity.from_property = self._conversation.user

        activity.recipient = self._conversation.agent
        activity.conversation = self._conversation.conversation
        activity.service_url = self._conversation.service_url
        activity.id = self._gen_id()

        if not activity.timestamp:
            activity.timestamp = datetime.now(timezone.utc)

        if not activity.local_timestamp:
            activity.local_timestamp = datetime.now()

        context = self.create_turn_context(activity, claims_identity)
        await self.run_pipeline(context, callback)
        return None

    async def process_proactive(
        self,
        claims_identity: ClaimsIdentity,
        continuation_activity: Activity,
        audience: str,
        callback: AgentCallbackHandler,
    ):
        """Run proactive turn logic against a supplied continuation activity.

        This simplified implementation creates a turn context and runs the
        pipeline. It does not create a conversation, validate ``audience``, or
        call a channel service.

        :param claims_identity: Identity for the proactive turn.
        :param continuation_activity: Activity used to create the turn context.
        :param audience: Accepted for interface compatibility; not used.
        :param callback: Turn logic to invoke.
        """
        context = self.create_turn_context(continuation_activity, claims_identity)
        await self.run_pipeline(context, callback)

    async def send_activities(
        self,
        context: TurnContext,
        activities: list[Activity],
    ) -> list[ResourceResponse]:
        """Capture outgoing activities in the adapter queue.

        Activities sent by the agent are assigned IDs and timestamps when
        missing, then appended to :attr:`activity_queue` or delivered to a
        pending :meth:`get_next_reply_async` waiter. This replaces sending to a
        real channel.

        :param context: Current turn context.
        :param activities: Activities sent by the agent.
        :return: Resource responses containing the assigned activity IDs.
        """

        if not activities:
            raise ValueError("Activities list cannot be empty.")

        responses: list[ResourceResponse] = []

        for activity in activities:

            if not activity.id:
                activity.id = self._gen_id()

            if not activity.timestamp:
                activity.timestamp = datetime.now(timezone.utc)

            self._enqueue(activity)

            responses.append(ResourceResponse(id=activity.id))

        return responses

    async def update_activity(
        self,
        context: TurnContext,
        activity: Activity,
    ) -> ResourceResponse:
        """Replace a queued activity with the same ID.

        This simulates channel update behavior by editing the in-memory queue.
        If no queued activity has the requested ID, an empty
        :class:`ResourceResponse` is returned.
        """

        if activity.id:
            replies = list(self._activity_queue)
            for i, reply in enumerate(replies):
                if reply.id == activity.id:
                    replies[i] = activity
                    self._activity_queue.clear()
                    for reply in replies:
                        self._activity_queue.append(reply)

                    return ResourceResponse(id=activity.id)
        return ResourceResponse()

    async def delete_activity(
        self,
        context: TurnContext,
        reference: ConversationReference,
    ) -> None:
        """Remove a queued activity identified by ``reference.activity_id``.

        Deletion is limited to the adapter's in-memory queue and does not call a
        channel service.
        """

        if not reference.activity_id:
            return

        replies = list(self._activity_queue)
        for i, reply in enumerate(replies):
            if reply.id == reference.activity_id:
                del replies[i]
                self._activity_queue.clear()
                for reply in replies:
                    self._activity_queue.append(reply)
                return

    async def create_conversation(
        self,
        agent_app_id: str,
        channel_id: str,
        service_url: str,
        audience: str,
        conversation_parameters: ConversationParameters,
        callback: AgentCallbackHandler[T],
    ) -> Awaitable[Any]:
        raise NotImplementedError()

    def get_activity_snapshot(self) -> list[Activity]:
        """Return a shallow copy of the currently queued bot replies."""
        return list(self._activity_queue)

    def get_next_reply(self) -> Activity | None:
        """Dequeue and return the next captured activity, or ``None`` if empty."""
        if len(self._activity_queue) > 0:
            return self._activity_queue.pop(0)
        return None

    async def get_next_reply_async(self) -> Activity | None:
        """Return the next captured activity from the queue.

        This asynchronous form mirrors the adapter interface used by test
        helpers. In the current Python implementation it returns immediately
        with the next queued reply, or ``None`` when no reply is available.
        """
        if not self._queued_requests:
            return self.get_next_reply()

        future = asyncio.Future()
        self._queued_requests.append(future)

        return await future

    def create_activity(
        self,
        text: str,
    ) -> Activity:
        """Create a message activity from text and the test conversation.

        The returned activity is shaped like a user message in the current test
        conversation and is suitable for :meth:`process_activity` or
        :meth:`send_text_to_bot`.
        """
        return Activity(
            type=ActivityTypes.message,
            text=text,
            locale=self.locale or _DEFAULTS._LOCALE,
            recipient=self._conversation.agent,
            from_property=self._conversation.user,
            conversation=self._conversation.conversation,
            service_url=self._conversation.service_url,
            id=self._gen_id(),
        )

    async def send_text_to_bot(
        self, user_says: str, callback: AgentCallbackHandler
    ) -> InvokeResponse | None:
        """Send text as a user message through the test adapter.

        This helper creates a message activity using :meth:`create_activity` and
        processes it through the normal test pipeline. A claims identity must be
        configured on :attr:`claims_identity` before calling this method.
        """
        if not self.claims_identity:
            raise ValueError(
                "ClaimsIdentity is not set. Please set it before sending activities."
            )

        return await self.process_activity(
            self.claims_identity,
            self.create_activity(user_says),
            callback,
        )

    def add_user_token(
        self,
        connection_name: str,
        channel_id: str,
        user_id: str,
        token: str,
        magic_code: str | None = None,
    ) -> None:
        """Add a fake user token to the adapter's mock token client.

        The token can later be returned by OAuth flows that request the same
        connection, channel, and user. If ``magic_code`` is supplied, the token
        is returned only when that code is provided.
        """
        if isinstance(self._user_token_client, MockUserTokenClient):
            self._user_token_client.add_user_token(
                connection_name=connection_name,
                channel_id=channel_id,
                user_id=user_id,
                token=token,
                magic_code=magic_code,
            )
        else:
            raise TypeError(
                "UserTokenClient is not a MockUserTokenClient. Cannot add user token."
            )

    def add_exchangeable_token(
        self,
        connection_name: str,
        channel_id: str,
        user_id: str,
        exchangeable_item: str,
        token: str,
    ) -> None:
        """Add a fake token exchange result to the mock token client.

        OAuth token-exchange tests can provide a token or URI as
        ``exchangeable_item`` and receive ``token`` when the same item is
        exchanged.
        """
        if isinstance(self._user_token_client, MockUserTokenClient):
            self._user_token_client.add_exchangeable_token(
                connection_name=connection_name,
                channel_id=channel_id,
                user_id=user_id,
                exchangeable_item=exchangeable_item,
                token=token,
            )
        else:
            raise TypeError(
                "UserTokenClient is not a MockUserTokenClient. Cannot add exchangeable token."
            )

    def raise_on_exchange_request(
        self,
        connection_name: str,
        channel_id: str,
        user_id: str,
        exchangeable_item: str,
    ) -> None:
        """Configure the mock token client to raise during token exchange.

        This is useful for testing error handling paths where the exchangeable
        token or URI should fail instead of returning a fake token.
        """
        if isinstance(self._user_token_client, MockUserTokenClient):
            self._user_token_client.raise_on_exchange_request(
                connection_name=connection_name,
                channel_id=channel_id,
                user_id=user_id,
                exchangeable_item=exchangeable_item,
            )
        else:
            raise TypeError(
                "UserTokenClient is not a MockUserTokenClient. Cannot set to raise on exchange request."
            )

    def _enqueue(self, activity: Activity) -> None:
        """Queue a captured activity or fulfill the oldest pending waiter.

        This is the in-memory replacement for sending an activity to a channel.
        """

        while len(self._queued_requests) > 0:

            future = self._queued_requests.pop(0)
            if not future.done():
                future.set_result(activity)
                return

        self._activity_queue.append(activity)
