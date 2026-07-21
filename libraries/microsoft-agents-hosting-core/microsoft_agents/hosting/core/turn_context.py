# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import Optional, Awaitable, TypeVar, Protocol

from copy import deepcopy
from collections.abc import Callable
from datetime import datetime, timezone
from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ConversationReference,
    DeliveryModes,
    InputHints,
    Mention,
    ResourceResponse,
    TurnContextProtocol,
)
from microsoft_agents.activity._model_utils import pick_model, SkipNone
from microsoft_agents.hosting.core.authorization.claims_identity import ClaimsIdentity
import microsoft_agents.hosting.core.telemetry.turn_context.spans as spans

OnSendActivitiesHandler = Callable[
    ["TurnContext", list[Activity], Callable[[], Awaitable[list[ResourceResponse]]]],
    Awaitable[list[ResourceResponse]],
]
OnUpdateActivityHandler = Callable[
    ["TurnContext", Activity, Callable[[], Awaitable[ResourceResponse]]],
    Awaitable[ResourceResponse],
]
OnDeleteActivityHandler = Callable[
    ["TurnContext", ConversationReference, Callable[[], Awaitable[None]]],
    Awaitable[None],
]

T = TypeVar("T")
_ArgT = TypeVar("_ArgT")


class _AsyncFunc(Protocol[T]):
    def __call__(self) -> Awaitable[T]: ...


class TurnContext(TurnContextProtocol):
    # Same constant as in the BF Adapter, duplicating here to avoid circular dependency
    _INVOKE_RESPONSE_KEY = "TurnContext.InvokeResponse"

    _activity: Activity

    _on_send_activities: list[OnSendActivitiesHandler]
    _on_update_activity: list[OnUpdateActivityHandler]
    _on_delete_activity: list[OnDeleteActivityHandler]

    def __init__(
        self,
        adapter_or_context,
        request: Activity | None = None,
        identity: ClaimsIdentity | None = None,
    ):
        """
        Creates a new TurnContext instance.
        :param adapter_or_context: The adapter instance or an existing TurnContext.
        :param request: The incoming Activity.
        :param identity: The ClaimsIdentity associated with the request.
        """
        if isinstance(adapter_or_context, TurnContext):
            adapter_or_context.copy_to(self)
            self._identity = adapter_or_context.identity
        else:
            self.adapter = adapter_or_context
            self._activity = request  # exception thrown if None further down
            self.responses: list[Activity] = []
            self._services: dict = {}
            self._on_send_activities = []
            self._on_update_activity = []
            self._on_delete_activity = []
            self._responded: bool = False
            self._identity = identity

        if self.adapter is None:
            raise TypeError("TurnContext must be instantiated with an adapter.")
        if self._activity is None:
            raise TypeError(
                "TurnContext must be instantiated with a request parameter of type Activity."
            )

        self._turn_state = {}

        # A list of activities to send when `context.Activity.DeliveryMode == 'expectReplies'`
        self.buffered_reply_activities = []

    @property
    def turn_state(self) -> dict[str, object]:
        return self._turn_state

    def copy_to(self, context: "TurnContext") -> None:
        """
        Called when this TurnContext instance is passed into the constructor of a new TurnContext
        instance. Can be overridden in derived classes.
        :param context:
        :return:
        """
        for attribute in [
            "adapter",
            "_activity",
            "_responded",
            "_services",
            "_on_send_activities",
            "_on_update_activity",
            "_on_delete_activity",
        ]:
            setattr(context, attribute, getattr(self, attribute))

    @property
    def activity(self) -> Activity:
        """
        The received activity.
        :return:
        """
        return self._activity  # type: ignore[return-value]

    @activity.setter
    def activity(self, value):
        """
        Used to set TurnContext._activity when a context object is created. Only takes instances of Activities.
        :param value:
        :return:
        """
        if not isinstance(value, Activity):
            raise TypeError(
                "TurnContext: cannot set `activity` to a type other than Activity."
            )
        self._activity = value

    @property
    def responded(self) -> bool:
        """
        If `true` at least one response has been sent for the current turn of conversation.
        :return:
        """
        return self._responded

    @responded.setter
    def responded(self, value: bool):
        if not value:
            raise ValueError("TurnContext: cannot set TurnContext.responded to False.")
        self._responded = True

    @property
    def services(self):
        """
        Map of services and other values cached for the lifetime of the turn.
        :return:
        """
        return self._services

    @property
    def streaming_response(self):
        """
        Gets a StreamingResponse instance for this turn context.
        This allows for streaming partial responses to the client.
        """
        # Use lazy import to avoid circular dependency
        if not hasattr(self, "_streaming_response"):
            from microsoft_agents.hosting.core.app.streaming import StreamingResponse

            self._streaming_response = StreamingResponse(self)
        return self._streaming_response

    @property
    def identity(self) -> Optional[ClaimsIdentity]:
        return self._identity

    def get(self, key: str) -> object:
        if not key or not isinstance(key, str):
            raise TypeError('"key" must be a valid string.')
        try:
            return self._services[key]
        except KeyError:
            raise KeyError("%s not found in TurnContext._services." % key)

    def has(self, key: str) -> bool:
        """
        Returns True is set() has been called for a key. The cached value may be of type 'None'.
        :param key:
        :return:
        """
        if key in self._services:
            return True
        return False

    def set(self, key: str, value: object) -> None:
        """
        Caches a value for the lifetime of the current turn.
        :param key:
        :param value:
        :return:
        """
        if not key or not isinstance(key, str):
            raise KeyError('"key" must be a valid string.')

        self._services[key] = value

    async def send_activity(
        self,
        activity_or_text: Activity | str,
        speak: str | None = None,
        input_hint: str | None = None,
    ) -> ResourceResponse:
        """
        Sends a single activity or message to the user.
        :param activity_or_text:
        :return:
        """
        if isinstance(activity_or_text, str):
            activity_or_text = Activity(
                type=ActivityTypes.message,
                text=activity_or_text,
                input_hint=input_hint or InputHints.accepting_input,
            )
            if speak:
                activity_or_text.speak = speak

        result = await self.send_activities([activity_or_text])
        return result[0] if result else ResourceResponse()

    async def send_activities(
        self, activities: list[Activity]
    ) -> list[ResourceResponse]:
        sent_non_trace_activity = False
        # TODO: Check activity serialization
        ref = self.activity.get_conversation_reference()

        with spans.TurnContextSendActivities(self):

            def activity_validator(activity: Activity) -> Activity:
                if not getattr(activity, "type", None):
                    activity.type = ActivityTypes.message
                if activity.type != ActivityTypes.trace:
                    nonlocal sent_non_trace_activity
                    sent_non_trace_activity = True
                if not activity.input_hint:
                    activity.input_hint = "acceptingInput"
                activity.id = None
                return activity

            output = [
                activity_validator(
                    TurnContext.apply_conversation_reference(deepcopy(act), ref)
                )
                for act in activities
            ]

            # send activities through adapter
            async def logic() -> list[ResourceResponse]:
                nonlocal sent_non_trace_activity

                if self.activity.delivery_mode == DeliveryModes.expect_replies:
                    responses = []
                    for activity in output:
                        self.buffered_reply_activities.append(activity)
                        # Ensure the TurnState has the InvokeResponseKey, since this activity
                        # is not being sent through the adapter, where it would be added to TurnState.
                        if activity.type == ActivityTypes.invoke_response:
                            self.turn_state[TurnContext._INVOKE_RESPONSE_KEY] = activity

                        responses.append(ResourceResponse())

                    if sent_non_trace_activity:
                        self.responded = True

                    return responses

                responses = await self.adapter.send_activities(self, output)
                if sent_non_trace_activity:
                    self.responded = True
                return responses

            return await self._emit(self._on_send_activities, output, logic)

    async def update_activity(self, activity: Activity):
        """
        Replaces an existing activity.
        :param activity:
        :return:
        """
        reference = self.activity.get_conversation_reference()

        return await self._emit(
            self._on_update_activity,
            TurnContext.apply_conversation_reference(activity, reference),
            lambda: self.adapter.update_activity(self, activity),
        )

    async def delete_activity(self, id_or_reference: str | ConversationReference):
        """
        Deletes an existing activity.
        :param id_or_reference:
        :return:
        """
        if isinstance(id_or_reference, str):
            reference = self.activity.get_conversation_reference()
            reference.activity_id = id_or_reference
        else:
            reference = id_or_reference

        return await self._emit(
            self._on_delete_activity,
            reference,
            lambda: self.adapter.delete_activity(self, reference),
        )

    def on_send_activities(self, handler: OnSendActivitiesHandler) -> TurnContext:
        """
        Registers a handler to be notified of and potentially intercept the sending of activities.
        :param handler: the handler to register
        :type handler: OnSendActivitiesHandler
        :return:
        """
        self._on_send_activities.append(handler)
        return self

    def on_update_activity(self, handler: OnUpdateActivityHandler) -> TurnContext:
        """
        Registers a handler to be notified of and potentially intercept an activity being updated.
        :param handler: the handler to register
        :type handler: OnUpdateActivityHandler
        :return:
        """
        self._on_update_activity.append(handler)
        return self

    def on_delete_activity(self, handler: OnDeleteActivityHandler) -> TurnContext:
        """
        Registers a handler to be notified of and potentially intercept an activity being deleted.
        :param handler: the handler to register
        :type handler: OnDeleteActivityHandler
        :return:
        """
        self._on_delete_activity.append(handler)
        return self

    async def _emit(
        self,
        handlers: list[Callable[[TurnContext, _ArgT, _AsyncFunc[T]], Awaitable[T]]],
        arg: _ArgT,
        logic: _AsyncFunc[T],
    ) -> T:
        """Emits an event to the registered handlers, allowing them to intercept and modify the behavior of the logic function.

        :param handlers: The list of registered handlers to invoke.
        :param arg: The argument to pass to the handlers.
        :param logic: The logic function to invoke after all handlers have been called.
        :return: The result of the logic function, potentially modified by the handlers.
        """

        handlers = list(handlers)

        async def emit_next(i: int) -> T:
            call_next: _AsyncFunc[T]
            if i + 1 < len(handlers):
                call_next = lambda: emit_next(i + 1)
            else:
                call_next = logic

            return await handlers[i](self, arg, call_next)

        if len(handlers) > 0:
            return await emit_next(0)

        return await logic()

    async def send_trace_activity(
        self,
        name: str,
        value: object = None,
        value_type: str | None = None,
        label: str | None = None,
    ) -> ResourceResponse:
        trace_activity = pick_model(
            Activity,
            type=ActivityTypes.trace,
            timestamp=datetime.now(timezone.utc),
            name=name,
            value=value,
            value_type=SkipNone(value_type),
            label=SkipNone(label),
        )

        return await self.send_activity(trace_activity)

    @staticmethod
    def apply_conversation_reference(
        activity: Activity, reference: ConversationReference, is_incoming: bool = False
    ) -> Activity:
        """
        Updates an activity with the delivery information from a conversation reference. Calling
        this after get_conversation_reference on an incoming activity
        will properly address the reply to a received activity.
        :param activity:
        :param reference:
        :param is_incoming:
        :return:
        """
        activity.channel_id = reference.channel_id
        if reference.locale:
            activity.locale = reference.locale
        activity.service_url = reference.service_url
        activity.conversation = reference.conversation
        if is_incoming:
            activity.from_property = reference.user
            activity.recipient = reference.agent
            if reference.activity_id:
                activity.id = reference.activity_id
        else:
            activity.from_property = reference.agent
            activity.recipient = reference.user
            if reference.activity_id:
                activity.reply_to_id = reference.activity_id

        return activity

    @staticmethod
    def get_reply_conversation_reference(
        activity: Activity, reply: ResourceResponse
    ) -> ConversationReference:
        reference: ConversationReference = activity.get_conversation_reference()

        # Update the reference with the new outgoing Activity's id.
        reference.activity_id = reply.id

        return reference

    @staticmethod
    def remove_recipient_mention(activity: Activity) -> str:
        """
        Removes the recipient's mention text from the activity's text.

        :param activity: The activity to remove the recipient mention from.
        :return: The updated activity text.
        """
        return activity.remove_recipient_mention()

    @staticmethod
    def remove_mention_text(activity: Activity, identifier: str) -> str:
        """
        Removes the mention text for the given account id from the activity's text.

        :param activity: The activity to remove the mention text from.
        :param identifier: The id of the account whose mention text should be removed.
        :return: The updated activity text.
        """
        return activity.remove_mention_text(identifier)

    @staticmethod
    def get_mentions(activity: Activity) -> list[Mention]:
        """
        Returns all the mentions in the activity.

        :param activity: the activity to get mentions from
        :return: A list of Mention objects representing all mentions in the activity.
        """
        return activity.get_mentions()
