"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import logging
from typing import Awaitable, Callable, Generic, Optional, TypeVar, TYPE_CHECKING

from microsoft_agents.activity import Activity, ResourceResponse

from microsoft_agents.hosting.core.app.state.turn_state import TurnState
from microsoft_agents.hosting.core.storage import Storage

from .conversation import Conversation
from .create_conversation_options import CreateConversationOptions
from .proactive_options import ProactiveOptions

if TYPE_CHECKING:
    from microsoft_agents.hosting.core.turn_context import TurnContext
    from microsoft_agents.hosting.core.channel_service_adapter import ChannelServiceAdapter
    from microsoft_agents.hosting.core.app.agent_application import AgentApplication

logger = logging.getLogger(__name__)

StateT = TypeVar("StateT", bound=TurnState)

_STORAGE_KEY_PREFIX = "proactive/conversations/"

RouteHandler = Callable[["TurnContext", StateT], Awaitable[None]]


class Proactive(Generic[StateT]):
    """
    Proactive messaging support for :class:`~microsoft_agents.hosting.core.app.agent_application.AgentApplication`.

    This class is attached to :attr:`AgentApplication.proactive` automatically when
    :attr:`~microsoft_agents.hosting.core.app.app_options.ApplicationOptions.proactive` options are
    provided.  It provides methods to:

    * **Persist** a conversation reference so it can be resumed later
      (:meth:`store_conversation`, :meth:`get_conversation`,
      :meth:`delete_conversation`).
    * **Continue** an existing conversation proactively
      (:meth:`continue_conversation`).
    * **Send** a single activity into an existing conversation
      (:meth:`send_activity`).
    * **Create** a brand-new conversation with a user
      (:meth:`create_conversation`).

    Example — store then resume::

        # During a normal turn, save the conversation for later:
        await app.proactive.store_conversation(context)

        # Later (e.g. from a webhook), resume it:
        async def notify(context, state):
            await context.send_activity("Here is your notification!")

        await app.proactive.continue_conversation(adapter, conversation_id, notify)
    """

    def __init__(
        self,
        app: "AgentApplication[StateT]",
        options: ProactiveOptions,
    ) -> None:
        self._app = app
        self._options = options

    # ------------------------------------------------------------------
    # Storage helpers
    # ------------------------------------------------------------------

    @property
    def _storage(self) -> Storage:
        storage = self._options.storage or self._app.options.storage
        if not storage:
            raise RuntimeError(
                "Proactive messaging requires a Storage instance.  "
                "Configure ProactiveOptions.storage or ApplicationOptions.storage."
            )
        return storage

    @staticmethod
    def _storage_key(conversation_id: str) -> str:
        return f"{_STORAGE_KEY_PREFIX}{conversation_id}"

    # ------------------------------------------------------------------
    # Conversation persistence
    # ------------------------------------------------------------------

    async def store_conversation(
        self,
        context_or_conversation: "TurnContext | Conversation",
    ) -> None:
        """
        Persist a :class:`~microsoft_agents.hosting.core.app.proactive.conversation.Conversation`
        to storage so it can be resumed later.

        Accepts either:

        * A :class:`~microsoft_agents.hosting.core.turn_context.TurnContext` — the
          :class:`~microsoft_agents.hosting.core.app.proactive.conversation.Conversation`
          is built automatically from the current turn.
        * A :class:`~microsoft_agents.hosting.core.app.proactive.conversation.Conversation`
          — stored directly.

        :param context_or_conversation: The turn context or an already-built
            :class:`~microsoft_agents.hosting.core.app.proactive.conversation.Conversation`.
        :raises ValueError: If required fields on the conversation are missing.
        """
        from microsoft_agents.hosting.core.turn_context import TurnContext

        if isinstance(context_or_conversation, TurnContext):
            conversation = Conversation.from_turn_context(context_or_conversation)
        else:
            conversation = context_or_conversation

        conversation.validate()
        key = self._storage_key(conversation.conversation_reference.conversation.id)
        logger.debug("Storing conversation with key: %s", key)
        await self._storage.write({key: conversation})

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Retrieve a previously stored
        :class:`~microsoft_agents.hosting.core.app.proactive.conversation.Conversation`.

        :param conversation_id: The conversation ID used as the storage key.
        :type conversation_id: str
        :return: The stored :class:`~microsoft_agents.hosting.core.app.proactive.conversation.Conversation`,
            or ``None`` if not found.
        :rtype: Optional[:class:`~microsoft_agents.hosting.core.app.proactive.conversation.Conversation`]
        """
        key = self._storage_key(conversation_id)
        results = await self._storage.read([key], target_cls=Conversation)
        return results.get(key)

    async def delete_conversation(self, conversation_id: str) -> None:
        """
        Delete a previously stored conversation.

        :param conversation_id: The conversation ID to delete.
        :type conversation_id: str
        """
        key = self._storage_key(conversation_id)
        logger.debug("Deleting conversation with key: %s", key)
        await self._storage.delete([key])

    # ------------------------------------------------------------------
    # Send a single activity
    # ------------------------------------------------------------------

    async def send_activity(
        self,
        adapter: "ChannelServiceAdapter",
        conversation_id_or_conversation: "str | Conversation",
        activity: Activity,
    ) -> Optional[ResourceResponse]:
        """
        Send a single activity into an existing conversation.

        :param adapter: The channel service adapter.
        :type adapter: :class:`~microsoft_agents.hosting.core.channel_service_adapter.ChannelServiceAdapter`
        :param conversation_id_or_conversation: Either a conversation ID string
            (the conversation is loaded from storage) or a
            :class:`~microsoft_agents.hosting.core.app.proactive.conversation.Conversation`
            object.
        :type conversation_id_or_conversation: str or
            :class:`~microsoft_agents.hosting.core.app.proactive.conversation.Conversation`
        :param activity: The activity to send.
        :type activity: :class:`~microsoft_agents.activity.Activity`
        :return: The :class:`~microsoft_agents.activity.ResourceResponse` from the
            channel, or ``None``.
        :rtype: Optional[:class:`~microsoft_agents.activity.ResourceResponse`]
        :raises KeyError: If *conversation_id_or_conversation* is a string and the
            conversation is not found in storage.
        """
        conversation = await self._resolve_conversation(conversation_id_or_conversation)
        return await Proactive._send_activity_impl(adapter, conversation, activity)

    @staticmethod
    async def _send_activity_impl(
        adapter: "ChannelServiceAdapter",
        conversation: Conversation,
        activity: Activity,
    ) -> Optional[ResourceResponse]:
        result: Optional[ResourceResponse] = None
        captured_exc: Optional[BaseException] = None

        claims = Conversation.identity_from_claims(conversation.claims)
        continuation = conversation.conversation_reference.get_continuation_activity()

        async def _callback(context: "TurnContext") -> None:
            nonlocal result, captured_exc
            try:
                result = await context.send_activity(activity)
            except Exception as exc:  # noqa: BLE001
                captured_exc = exc

        await adapter.continue_conversation_with_claims(claims, continuation, _callback)

        if captured_exc is not None:
            raise captured_exc
        return result

    # ------------------------------------------------------------------
    # Continue a conversation
    # ------------------------------------------------------------------

    async def continue_conversation(
        self,
        adapter: "ChannelServiceAdapter",
        conversation_id_or_conversation: "str | Conversation",
        handler: RouteHandler,
        *,
        continuation_activity: Optional[Activity] = None,
        token_handlers: Optional[list[str]] = None,
    ) -> None:
        """
        Continue an existing conversation by invoking *handler* inside a full
        turn with state loaded/saved.

        :param adapter: The channel service adapter.
        :type adapter: :class:`~microsoft_agents.hosting.core.channel_service_adapter.ChannelServiceAdapter`
        :param conversation_id_or_conversation: Conversation ID (loaded from
            storage) or a direct
            :class:`~microsoft_agents.hosting.core.app.proactive.conversation.Conversation`.
        :type conversation_id_or_conversation: str or
            :class:`~microsoft_agents.hosting.core.app.proactive.conversation.Conversation`
        :param handler: Async callable ``(context, state) -> None`` that performs
            the proactive work.
        :type handler: Callable
        :param continuation_activity: Optional override for the continuation activity
            sent to the channel.  When ``None`` the default continuation event from
            :meth:`~microsoft_agents.activity.ConversationReference.get_continuation_activity`
            is used.  Supply a custom activity to carry additional payload (e.g. the
            original message) into the proactive turn via ``context.activity.value``.
        :type continuation_activity: Optional[:class:`~microsoft_agents.activity.Activity`]
        :param token_handlers: Optional list of OAuth connection names whose
            tokens must be available before *handler* is invoked.  When
            :attr:`~ProactiveOptions.fail_on_unsigned_in_connections` is ``True``
            (the default) and a token is missing a :exc:`RuntimeError` is raised.
        :type token_handlers: Optional[list[str]]
        :raises KeyError: If *conversation_id_or_conversation* is a string and the
            conversation is not found in storage.
        :raises RuntimeError: If a required OAuth token is not available and
            :attr:`~ProactiveOptions.fail_on_unsigned_in_connections` is ``True``.
        """
        conversation = await self._resolve_conversation(conversation_id_or_conversation)

        captured_exc: Optional[BaseException] = None
        claims = Conversation.identity_from_claims(conversation.claims)
        continuation = (
            continuation_activity
            or conversation.conversation_reference.get_continuation_activity()
        )

        async def _callback(context: "TurnContext") -> None:
            nonlocal captured_exc
            try:
                await self._on_turn(context, handler, token_handlers)
            except Exception as exc:  # noqa: BLE001
                captured_exc = exc

        await adapter.continue_conversation_with_claims(claims, continuation, _callback)

        if captured_exc is not None:
            raise captured_exc

    # ------------------------------------------------------------------
    # Create a new conversation
    # ------------------------------------------------------------------

    async def create_conversation(
        self,
        adapter: "ChannelServiceAdapter",
        options: CreateConversationOptions,
        handler: Optional[RouteHandler] = None,
    ) -> Conversation:
        """
        Create a brand-new conversation with a user and optionally run *handler*.

        :param adapter: The channel service adapter.
        :type adapter: :class:`~microsoft_agents.hosting.core.channel_service_adapter.ChannelServiceAdapter`
        :param options: Options specifying the identity, channel, conversation
            parameters, etc.
        :type options: :class:`~microsoft_agents.hosting.core.app.proactive.create_conversation_options.CreateConversationOptions`
        :param handler: Optional async callable invoked inside the new
            conversation's first turn.
        :type handler: Optional[Callable]
        :return: A :class:`~microsoft_agents.hosting.core.app.proactive.conversation.Conversation`
            representing the newly created conversation.
        :rtype: :class:`~microsoft_agents.hosting.core.app.proactive.conversation.Conversation`
        :raises ValueError: If required fields in *options* are missing.
        """
        options.validate()

        new_conversation: Optional[Conversation] = None
        captured_exc: Optional[BaseException] = None

        audience = options.audience or options.identity.get_token_audience()

        async def _callback(context: "TurnContext") -> None:
            nonlocal new_conversation, captured_exc
            try:
                reference = context.activity.get_conversation_reference()
                new_conversation = Conversation(
                    claims=options.identity,
                    conversation_reference=reference,
                )

                if options.store_conversation:
                    await self.store_conversation(new_conversation)

                if handler is not None:
                    state = await self._load_state(context)
                    await handler(context, state)
                    await state.save(context)
            except Exception as exc:  # noqa: BLE001
                captured_exc = exc

        await adapter.create_conversation(
            options.identity.get_app_id() or "",
            options.channel_id,
            options.service_url or "",
            audience,
            options.parameters,
            _callback,
        )

        if captured_exc is not None:
            raise captured_exc

        return new_conversation

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _on_turn(
        self,
        context: "TurnContext",
        handler: RouteHandler,
        token_handlers: Optional[list[str]] = None,
    ) -> None:
        """Run a proactive turn: load state → optional OAuth check → handler → save state."""
        state = await self._load_state(context)

        if token_handlers and self._app._auth:
            for handler_id in token_handlers:
                result = await self._app._auth._start_or_continue_sign_in(
                    context, state, handler_id
                )
                if not result.sign_in_complete():
                    if self._options.fail_on_unsigned_in_connections:
                        raise RuntimeError(
                            f"Proactive continuation aborted: user is not signed in "
                            f"for OAuth connection '{handler_id}'."
                        )
                    logger.warning(
                        "Proactive continuation skipped: user not signed in for '%s'.",
                        handler_id,
                    )
                    return

        await handler(context, state)
        await state.save(context)

    async def _load_state(self, context: "TurnContext") -> StateT:
        if self._app._turn_state_factory:
            state = self._app._turn_state_factory()
        else:
            state = TurnState.with_storage(self._storage)
        await state.load(context, self._storage)
        return state

    async def _resolve_conversation(
        self,
        conversation_id_or_conversation: "str | Conversation",
    ) -> Conversation:
        if isinstance(conversation_id_or_conversation, str):
            conversation = await self.get_conversation(conversation_id_or_conversation)
            if conversation is None:
                raise KeyError(
                    f"Proactive conversation not found in storage: "
                    f"'{conversation_id_or_conversation}'"
                )
            return conversation
        return conversation_id_or_conversation
