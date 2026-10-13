# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import ABC

from typing import Awaitable, Callable

from microsoft_agents.activity import (
    Activity,
    ResourceResponse,
    ConversationReference,
)

from microsoft_agents.hosting.core.turn_context import (
    TurnContext,
    OnSendActivitiesHandler,
    OnUpdateActivityHandler,
    OnDeleteActivityHandler,
)


class _TurnContextWrapper(TurnContext, ABC):
    """A base class for wrapping a TurnContext with additional functionality."""

    def __init__(self, context: TurnContext) -> None:
        """Initialise the turn context from a plain turn context.

        :param context: The base turn context provided by the core runtime.
        """
        super().__init__(context)

        self._original = context
        self._turn_state = context.turn_state
        self.buffered_reply_activities = context.buffered_reply_activities

    @property
    def responded(self) -> bool:
        return self._original.responded

    @responded.setter
    def responded(self, value: bool):
        self._original.responded = value

    @property
    def streaming_response(self):
        return self._original.streaming_response

    async def send_activity(
        self,
        activity_or_text: Activity | str,
        speak: str | None = None,
        input_hint: str | None = None,
    ) -> ResourceResponse:
        """
        Send an activity to the conversation.

        :param activity_or_text: The activity to send or a string representing the text of the activity.
        :param speak: Optional speech text for the activity.
        :param input_hint: Optional input hint for the activity.
        :return: A ResourceResponse representing the result of the send operation.
        """
        return await self._original.send_activity(
            activity_or_text, speak=speak, input_hint=input_hint
        )

    async def send_activities(
        self, activities: list[Activity]
    ) -> list[ResourceResponse]:
        """
        Send multiple activities to the conversation.

        :param activities: A list of activities to send.
        :return: A list of ResourceResponse objects representing the result of each send operation.
        """
        return await self._original.send_activities(activities)

    async def update_activity(self, activity: Activity):
        """
        Replaces an existing activity.
        :param activity:
        :return:
        """
        return await self._original.update_activity(activity)

    async def delete_activity(self, id_or_reference: str | ConversationReference):
        """
        Deletes an existing activity.
        :param id_or_reference:
        :return:
        """
        return await self._original.delete_activity(id_or_reference)

    def on_send_activities(self, handler: OnSendActivitiesHandler) -> TurnContext:
        """
        Registers a handler to be notified of and potentially intercept the sending of activities.
        :param handler: the handler to register
        :type handler: OnSendActivitiesHandler
        :return:
        """
        self._original.on_send_activities(handler)
        return self

    def on_update_activity(self, handler: OnUpdateActivityHandler) -> TurnContext:
        """
        Registers a handler to be notified of and potentially intercept an activity being updated.
        :param handler: the handler to register
        :type handler: OnUpdateActivityHandler
        :return:
        """
        self._original.on_update_activity(handler)
        return self

    def on_delete_activity(self, handler: OnDeleteActivityHandler) -> TurnContext:
        """
        Registers a handler to be notified of and potentially intercept an activity being deleted.
        :param handler: the handler to register
        :type handler: OnDeleteActivityHandler
        :return:
        """
        self._original.on_delete_activity(handler)
        return self

    async def send_trace_activity(
        self,
        name: str,
        value: object = None,
        value_type: str | None = None,
        label: str | None = None,
    ) -> ResourceResponse:
        return await self._original.send_trace_activity(
            name=name, value=value, value_type=value_type, label=label
        )

    async def _aclose(self) -> None:
        """
        Asynchronously close any resources associated with the turn context.

        :return: None
        """
        await self._original._aclose()

    def _on_aclose(self, handler: Callable[[TurnContext], Awaitable[None]]) -> None:
        """
        Register a handler to be called when the turn context is asynchronously closed.

        :param handler: A callable that takes the turn context and returns an awaitable.
        :return: None
        """
        self._original._on_aclose(handler)
