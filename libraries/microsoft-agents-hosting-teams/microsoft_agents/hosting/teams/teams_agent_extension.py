"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import re
from http import HTTPStatus
from typing import Any, Callable, Generic, Optional, Pattern, TypeVar, Union

from microsoft_agents.activity import Activity, ActivityTypes, InvokeResponse
from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.core.app import AgentApplication, RouteRank
from microsoft_agents.hosting.core.app.state import TurnState

from microsoft_agents.activity.teams import (
    MeetingParticipantsEventDetails,
    ReadReceiptInfo,
)
from microsoft_teams.api.models import (
    AppBasedLinkQuery,
    FileConsentCardResponse,
    MeetingDetails,
    MessagingExtensionAction,
    MessagingExtensionQuery,
    O365ConnectorCardActionQuery,
    TaskModuleRequest,
)

StateT = TypeVar("StateT", bound=TurnState)

CommandSelector = Union[str, Pattern[str], None]


def _match_selector(selector: CommandSelector, value: Optional[str]) -> bool:
    if selector is None:
        return True
    if value is None:
        return False
    if isinstance(selector, str):
        return selector == value
    return bool(re.match(selector, value))


def _get_channel_event_type(context: TurnContext) -> Optional[str]:
    data = context.activity.channel_data
    if data is None:
        return None
    if isinstance(data, dict):
        return data.get("eventType") or data.get("event_type")
    return getattr(data, "event_type", None)


async def _send_invoke_response(context: TurnContext, body: Any = None) -> None:
    serialized_body = None
    if body is not None:
        if hasattr(body, "model_dump"):
            serialized_body = body.model_dump(
                mode="json", by_alias=True, exclude_none=True
            )
        else:
            serialized_body = body
    await context.send_activity(
        Activity(
            type=ActivityTypes.invoke_response,
            value=InvokeResponse(status=int(HTTPStatus.OK), body=serialized_body),
        )
    )


class MessageExtension(Generic[StateT]):
    """
    Route registration for Teams Message Extension (composeExtension) invoke activities.
    Access via TeamsAgentExtension.message_extension.
    """

    def __init__(self, app: AgentApplication[StateT]) -> None:
        self._app = app

    def on_query(
        self,
        command_id: CommandSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for composeExtension/query invokes."""

        def __selector(context: TurnContext) -> bool:
            value = context.activity.value or {}
            parameters = value.get("parameters") or [{}]
            selected_command_id = value.get("commandId")
            if selected_command_id is None:
                selected_command_id = parameters[0].get("value")

            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/query"
                and _match_selector(
                    command_id,
                    selected_command_id,
                )
            )

        def __call(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                query = MessagingExtensionQuery.model_validate(
                    context.activity.value or {}
                )
                response = await func(context, state, query)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

    def on_select_item(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for composeExtension/selectItem invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/selectItem"
            )

        def __register(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                response = await func(context, state, context.activity.value)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    def on_submit_action(
        self,
        command_id: CommandSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for composeExtension/submitAction invokes (not bot message preview)."""

        def __selector(context: TurnContext) -> bool:
            if (
                context.activity.type != ActivityTypes.invoke
                or context.activity.name != "composeExtension/submitAction"
            ):
                return False
            value = context.activity.value or {}
            if value.get("botMessagePreviewAction"):
                return False
            return _match_selector(command_id, value.get("commandId"))

        def __call(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                action = MessagingExtensionAction.model_validate(
                    context.activity.value or {}
                )
                response = await func(context, state, action)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

    def on_agent_message_preview_edit(
        self,
        command_id: CommandSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for composeExtension/submitAction with botMessagePreviewAction == 'edit'."""

        def __selector(context: TurnContext) -> bool:
            if (
                context.activity.type != ActivityTypes.invoke
                or context.activity.name != "composeExtension/submitAction"
            ):
                return False
            value = context.activity.value or {}
            if value.get("botMessagePreviewAction") != "edit":
                return False
            return _match_selector(command_id, value.get("commandId"))

        def __call(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                action = MessagingExtensionAction.model_validate(
                    context.activity.value or {}
                )
                response = await func(context, state, action)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

    def on_agent_message_preview_send(
        self,
        command_id: CommandSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for composeExtension/submitAction with botMessagePreviewAction == 'send'."""

        def __selector(context: TurnContext) -> bool:
            if (
                context.activity.type != ActivityTypes.invoke
                or context.activity.name != "composeExtension/submitAction"
            ):
                return False
            value = context.activity.value or {}
            if value.get("botMessagePreviewAction") != "send":
                return False
            return _match_selector(command_id, value.get("commandId"))

        def __call(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                action = MessagingExtensionAction.model_validate(
                    context.activity.value or {}
                )
                response = await func(context, state, action)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

    def on_fetch_task(
        self,
        command_id: CommandSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for composeExtension/fetchTask invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/fetchTask"
                and _match_selector(
                    command_id,
                    (context.activity.value or {}).get("commandId"),
                )
            )

        def __call(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                action = MessagingExtensionAction.model_validate(
                    context.activity.value or {}
                )
                response = await func(context, state, action)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

    def on_query_link(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for composeExtension/queryLink invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/queryLink"
            )

        def __register(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                query = AppBasedLinkQuery.model_validate(context.activity.value or {})
                response = await func(context, state, query)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    def on_anonymous_query_link(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for composeExtension/anonymousQueryLink invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/anonymousQueryLink"
            )

        def __register(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                query = AppBasedLinkQuery.model_validate(context.activity.value or {})
                response = await func(context, state, query)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    def on_query_url_setting(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for composeExtension/querySettingUrl invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/querySettingUrl"
            )

        def __register(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                query = MessagingExtensionQuery.model_validate(
                    context.activity.value or {}
                )
                response = await func(context, state, query)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    def on_configure_settings(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for composeExtension/setting invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/setting"
            )

        def __register(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                await func(context, state, context.activity.value)
                await _send_invoke_response(context)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    def on_card_button_clicked(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for composeExtension/onCardButtonClicked invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "composeExtension/onCardButtonClicked"
            )

        def __register(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                await func(context, state, context.activity.value)
                await _send_invoke_response(context)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register


class TaskModule(Generic[StateT]):
    """
    Route registration for Teams Task Module (task/fetch, task/submit) invoke activities.
    Access via TeamsAgentExtension.task_module.
    """

    def __init__(self, app: AgentApplication[StateT]) -> None:
        self._app = app

    @staticmethod
    def _get_verb(value: Optional[Any]) -> Optional[str]:
        if not isinstance(value, dict):
            return None
        data = value.get("data")
        if isinstance(data, dict):
            return data.get("verb")
        return None

    def on_fetch(
        self,
        verb: CommandSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for task/fetch invokes.

        :param verb: Optional verb string or regex to match against task data.
            If None, matches all task/fetch invokes.
        """

        def __selector(context: TurnContext) -> bool:
            if (
                context.activity.type != ActivityTypes.invoke
                or context.activity.name != "task/fetch"
            ):
                return False
            return _match_selector(verb, TaskModule._get_verb(context.activity.value))

        def __call(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                request = TaskModuleRequest.model_validate(context.activity.value or {})
                response = await func(context, state, request)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call

    def on_submit(
        self,
        verb: CommandSelector = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for task/submit invokes.

        :param verb: Optional verb string or regex to match against task data.
            If None, matches all task/submit invokes.
        """

        def __selector(context: TurnContext) -> bool:
            if (
                context.activity.type != ActivityTypes.invoke
                or context.activity.name != "task/submit"
            ):
                return False
            return _match_selector(verb, TaskModule._get_verb(context.activity.value))

        def __call(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                request = TaskModuleRequest.model_validate(context.activity.value or {})
                response = await func(context, state, request)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        return __call


class Meeting(Generic[StateT]):
    """
    Route registration for Teams Meeting event activities.
    Access via TeamsAgentExtension.meeting.
    """

    def __init__(self, app: AgentApplication[StateT]) -> None:
        self._app = app

    def on_start(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for meeting start events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.event
                and context.activity.name == "application/vnd.microsoft.meetingStart"
            )

        def __register(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                meeting = MeetingDetails.model_validate(context.activity.value or {})
                await func(context, state, meeting)

            self._app.add_route(
                __selector,
                __handler,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    def on_end(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for meeting end events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.event
                and context.activity.name == "application/vnd.microsoft.meetingEnd"
            )

        def __register(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                meeting = MeetingDetails.model_validate(context.activity.value or {})
                await func(context, state, meeting)

            self._app.add_route(
                __selector,
                __handler,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    def on_participants_join(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for meeting participant join events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.event
                and context.activity.name
                == "application/vnd.microsoft.meetingParticipantJoin"
            )

        def __register(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                details = MeetingParticipantsEventDetails.model_validate(
                    context.activity.value or {}
                )
                await func(context, state, details)

            self._app.add_route(
                __selector,
                __handler,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    def on_participants_leave(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for meeting participant leave events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.event
                and context.activity.name
                == "application/vnd.microsoft.meetingParticipantLeave"
            )

        def __register(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                details = MeetingParticipantsEventDetails.model_validate(
                    context.activity.value or {}
                )
                await func(context, state, details)

            self._app.add_route(
                __selector,
                __handler,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register


class TeamsAgentExtension(Generic[StateT]):
    """
    Adds Teams-specific route registration to an AgentApplication.

    Usage::

        app = AgentApplication(options)
        teams = TeamsAgentExtension(app)

        @teams.task_module.on_fetch("myVerb")
        async def handle_fetch(context, state, request: TaskModuleRequest):
            return TaskModuleResponse(...)

        @teams.message_extension.on_query("searchCmd")
        async def handle_query(context, state, query: MessagingExtensionQuery):
            return MessagingExtensionResponse(...)

        @teams.meeting.on_start
        async def handle_meeting_start(context, state, meeting: MeetingDetails):
            ...
    """

    def __init__(self, app: AgentApplication[StateT]) -> None:
        self._app = app
        self._message_extension: MessageExtension[StateT] = MessageExtension(app)
        self._task_module: TaskModule[StateT] = TaskModule(app)
        self._meeting: Meeting[StateT] = Meeting(app)

    @property
    def message_extension(self) -> MessageExtension[StateT]:
        """Route registration for Message Extension (composeExtension) invokes."""
        return self._message_extension

    @property
    def task_module(self) -> TaskModule[StateT]:
        """Route registration for Task Module (task/fetch, task/submit) invokes."""
        return self._task_module

    @property
    def meeting(self) -> Meeting[StateT]:
        """Route registration for Meeting lifecycle events."""
        return self._meeting

    # ── Message update / delete ────────────────────────────────────────────

    def on_message_edit(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams editMessage events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.message_update
                and context.activity.channel_id == "msteams"
                and _get_channel_event_type(context) == "editMessage"
            )

        def __register(func: Callable) -> Callable:
            self._app.add_route(
                __selector, func, rank=rank, auth_handlers=auth_handlers
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    def on_message_undelete(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams undeleteMessage events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.message_update
                and context.activity.channel_id == "msteams"
                and _get_channel_event_type(context) == "undeleteMessage"
            )

        def __register(func: Callable) -> Callable:
            self._app.add_route(
                __selector, func, rank=rank, auth_handlers=auth_handlers
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    def on_message_soft_delete(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams softDeleteMessage events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.message_delete
                and context.activity.channel_id == "msteams"
                and _get_channel_event_type(context) == "softDeleteMessage"
            )

        def __register(func: Callable) -> Callable:
            self._app.add_route(
                __selector, func, rank=rank, auth_handlers=auth_handlers
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    # ── Read receipt ───────────────────────────────────────────────────────

    def on_read_receipt(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams readReceipt events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.event
                and context.activity.name == "application/vnd.microsoft.readReceipt"
            )

        def __register(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                receipt = ReadReceiptInfo.model_validate(context.activity.value or {})
                await func(context, state, receipt)

            self._app.add_route(
                __selector, __handler, rank=rank, auth_handlers=auth_handlers
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    # ── Config ─────────────────────────────────────────────────────────────

    def on_config_fetch(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for config/fetch invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "config/fetch"
            )

        def __register(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                response = await func(context, state, context.activity.value)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    def on_config_submit(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for config/submit invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "config/submit"
            )

        def __register(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                response = await func(context, state, context.activity.value)
                if response is not None:
                    await _send_invoke_response(context, response)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    # ── File consent ───────────────────────────────────────────────────────

    def on_file_consent_accept(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for fileConsent/invoke with action == 'accept'."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "fileConsent/invoke"
                and isinstance(context.activity.value, dict)
                and context.activity.value.get("action") == "accept"
            )

        def __register(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                file_consent = FileConsentCardResponse.model_validate(
                    context.activity.value or {}
                )
                await func(context, state, file_consent)
                await _send_invoke_response(context)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    def on_file_consent_decline(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for fileConsent/invoke with action == 'decline'."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "fileConsent/invoke"
                and isinstance(context.activity.value, dict)
                and context.activity.value.get("action") == "decline"
            )

        def __register(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                file_consent = FileConsentCardResponse.model_validate(
                    context.activity.value or {}
                )
                await func(context, state, file_consent)
                await _send_invoke_response(context)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    # ── O365 Connector ─────────────────────────────────────────────────────

    def on_o365_connector_card_action(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for actionableMessage/executeAction invokes."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "actionableMessage/executeAction"
            )

        def __register(func: Callable) -> Callable:
            async def __handler(context: TurnContext, state: StateT) -> None:
                query = O365ConnectorCardActionQuery.model_validate(
                    context.activity.value or {}
                )
                await func(context, state, query)
                await _send_invoke_response(context)

            self._app.add_route(
                __selector,
                __handler,
                is_invoke=True,
                rank=rank,
                auth_handlers=auth_handlers,
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    # ── Conversation update events ─────────────────────────────────────────

    def on_members_added(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams membersAdded conversation update events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.conversation_update
                and context.activity.channel_id == "msteams"
                and isinstance(context.activity.members_added, list)
                and len(context.activity.members_added) > 0
            )

        def __register(func: Callable) -> Callable:
            self._app.add_route(
                __selector, func, rank=rank, auth_handlers=auth_handlers
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    def on_members_removed(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams membersRemoved conversation update events."""

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.conversation_update
                and context.activity.channel_id == "msteams"
                and isinstance(context.activity.members_removed, list)
                and len(context.activity.members_removed) > 0
            )

        def __register(func: Callable) -> Callable:
            self._app.add_route(
                __selector, func, rank=rank, auth_handlers=auth_handlers
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register

    def on_channel_created(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams channelCreated conversation update events."""
        return self._on_teams_channel_event(
            "channelCreated", handler, auth_handlers=auth_handlers, rank=rank
        )

    def on_channel_deleted(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams channelDeleted conversation update events."""
        return self._on_teams_channel_event(
            "channelDeleted", handler, auth_handlers=auth_handlers, rank=rank
        )

    def on_channel_renamed(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams channelRenamed conversation update events."""
        return self._on_teams_channel_event(
            "channelRenamed", handler, auth_handlers=auth_handlers, rank=rank
        )

    def on_channel_restored(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams channelRestored conversation update events."""
        return self._on_teams_channel_event(
            "channelRestored", handler, auth_handlers=auth_handlers, rank=rank
        )

    def on_team_archived(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams teamArchived conversation update events."""
        return self._on_teams_channel_event(
            "teamArchived", handler, auth_handlers=auth_handlers, rank=rank
        )

    def on_team_deleted(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams teamDeleted conversation update events."""
        return self._on_teams_channel_event(
            "teamDeleted", handler, auth_handlers=auth_handlers, rank=rank
        )

    def on_team_hard_deleted(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams teamHardDeleted conversation update events."""
        return self._on_teams_channel_event(
            "teamHardDeleted", handler, auth_handlers=auth_handlers, rank=rank
        )

    def on_team_renamed(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams teamRenamed conversation update events."""
        return self._on_teams_channel_event(
            "teamRenamed", handler, auth_handlers=auth_handlers, rank=rank
        )

    def on_team_restored(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams teamRestored conversation update events."""
        return self._on_teams_channel_event(
            "teamRestored", handler, auth_handlers=auth_handlers, rank=rank
        )

    def on_team_unarchived(
        self,
        handler: Optional[Callable] = None,
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        """Register a handler for Teams teamUnarchived conversation update events."""
        return self._on_teams_channel_event(
            "teamUnarchived", handler, auth_handlers=auth_handlers, rank=rank
        )

    def _on_teams_channel_event(
        self,
        event_type: str,
        handler: Optional[Callable],
        *,
        auth_handlers: Optional[list[str]] = None,
        rank: RouteRank = RouteRank.DEFAULT,
    ) -> Callable:
        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.conversation_update
                and context.activity.channel_id == "msteams"
                and _get_channel_event_type(context) == event_type
            )

        def __register(func: Callable) -> Callable:
            self._app.add_route(
                __selector, func, rank=rank, auth_handlers=auth_handlers
            )
            return func

        if handler is not None:
            return __register(handler)
        return __register
