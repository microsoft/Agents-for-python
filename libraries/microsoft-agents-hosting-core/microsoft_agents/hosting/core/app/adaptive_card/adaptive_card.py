# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from dataclasses import asdict
from http import HTTPStatus
from typing import TYPE_CHECKING, Callable, Pattern

import pydantic

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    AdaptiveCardInvokeResponse,
    AdaptiveCardInvokeValue,
    AdaptiveCardSearchInvokeValue,
    Channels,
    ChannelId,
    InvokeResponse,
)
from microsoft_agents.hosting.core.turn_context import TurnContext

from ..state import TurnState
from . import factory
from ._type_defs import (
    ActionExecuteHandler,
    ActionSubmitHandler,
    SearchHandler,
)
from .models import AdaptiveCardSearchParams, Query

if TYPE_CHECKING:
    from ..agent_application import AgentApplication

_ACTION_EXECUTE_TYPE = "Action.Execute"
_ACTION_INVOKE_NAME = "adaptiveCard/action"
_SEARCH_INVOKE_NAME = "application/search"


class AdaptiveCard:
    """Register handlers for Adaptive Card activities."""

    def __init__(self, app: AgentApplication):
        """Initialize an Adaptive Card route registrar for an application."""
        self._app = app

    def action_execute(
        self,
        verb: str | Pattern[str],
        *,
        auth_handlers: list[str] | None = None,
        **kwargs,
    ) -> Callable[[ActionExecuteHandler], ActionExecuteHandler]:
        """Register an ``Action.Execute`` handler that receives the action data."""

        def selector(context: TurnContext) -> bool:
            activity = context.activity
            if (
                activity.type != ActivityTypes.invoke
                or activity.name != _ACTION_INVOKE_NAME
            ):
                return False

            try:
                invoke_value = AdaptiveCardInvokeValue.model_validate(activity.value)
            except pydantic.ValidationError:
                return False

            verb_value = (
                invoke_value.action.verb if invoke_value.action is not None else None
            )
            return self._matches(verb, verb_value)

        def register(func: Callable) -> Callable:
            async def handler(context: TurnContext, state: TurnState) -> None:
                invoke_value, response = self._validate_action_execute_value(context)

                if invoke_value is not None:
                    response = await func(context, state, invoke_value.action.data)

                response = response or AdaptiveCardInvokeResponse(
                    status_code=HTTPStatus.OK
                )

                await self._send_invoke_response(
                    context, response, status_code=HTTPStatus.OK
                )

            kwargs.pop("is_invoke", None)
            self._app.add_route(
                selector,
                handler,
                is_invoke=True,
                auth_handlers=auth_handlers,
                **kwargs,
            )
            return func

        return register

    def action_submit(
        self,
        verb: str | Pattern[str],
        *,
        auth_handlers: list[str] | None = None,
        submit_filter: str = "verb",
        **kwargs,
    ) -> Callable[[ActionSubmitHandler], ActionSubmitHandler]:
        """Register an Adaptive Card ``Action.Submit`` handler."""

        def selector(context: TurnContext) -> bool:
            activity = context.activity
            if (
                activity.type != ActivityTypes.message
                or activity.text
                or activity.value is None
            ):
                return False

            verb_value = None
            if isinstance(activity.value, dict):
                verb_value = activity.value.get(submit_filter)
            return self._matches(verb, verb_value)

        def register(func: ActionSubmitHandler) -> ActionSubmitHandler:
            async def handler(context: TurnContext, state: TurnState) -> None:
                await func(context, state, context.activity.value)

            self._app.add_route(
                selector,
                handler,
                is_invoke=False,
                auth_handlers=auth_handlers,
                **kwargs,
            )
            return func

        return register

    def search(
        self,
        dataset: str | Pattern[str],
        *,
        auth_handlers: list[str] | None = None,
        **kwargs,
    ) -> Callable[[SearchHandler], SearchHandler]:
        """Register an Adaptive Card dynamic-search handler."""

        def selector(context: TurnContext) -> bool:
            activity = context.activity
            if (
                activity.type != ActivityTypes.invoke
                or activity.name != _SEARCH_INVOKE_NAME
            ):
                return False

            try:
                invoke_value = AdaptiveCardSearchInvokeValue.model_validate(
                    activity.value
                )
            except pydantic.ValidationError:
                return False

            return self._matches(dataset, invoke_value.dataset)

        def register(func: SearchHandler) -> SearchHandler:
            async def handler(context: TurnContext, state: TurnState) -> None:
                value, response = self._validate_search_value(context)
                if value is not None:
                    options = value.query_options
                    query = Query(
                        count=options.top,
                        skip=options.skip,
                        parameters=AdaptiveCardSearchParams(
                            query_text=value.query_text,
                            dataset=value.dataset or "",
                        ),
                    )
                    results = await func(context, state, query)
                    response = factory.search_response(
                        {"results": [asdict(result) for result in results]}
                    )

                await self._send_invoke_response(
                    context, response, response.status_code or HTTPStatus.OK
                )

            kwargs.pop("is_invoke", None)
            self._app.add_route(
                selector,
                handler,
                is_invoke=True,
                auth_handlers=auth_handlers,
                **kwargs,
            )
            return func

        return register

    def _validate_action_execute_value(
        self, context: TurnContext
    ) -> tuple[AdaptiveCardInvokeValue | None, AdaptiveCardInvokeResponse]:
        if context.activity.value is None:
            return None, factory.bad_request("Missing value property for Invoke Action")

        try:
            value = AdaptiveCardInvokeValue.model_validate(context.activity.value)
        except pydantic.ValidationError:
            return None, factory.bad_request(
                "Value property is not a properly formed Invoke Action"
            )

        if value.action is None:
            return None, factory.bad_request("Missing action property")
        if value.action.type != _ACTION_EXECUTE_TYPE:
            return None, factory.not_supported(
                f"The Invoke Action '{value.action.type}' was not expected."
            )

        return value, AdaptiveCardInvokeResponse()

    def _validate_search_value(
        self, context: TurnContext
    ) -> tuple[AdaptiveCardSearchInvokeValue | None, AdaptiveCardInvokeResponse]:
        value = context.activity.value
        if value is None:
            return None, factory.bad_request("Missing value property for search")

        try:
            search_invoke_value = AdaptiveCardSearchInvokeValue.model_validate(value)
        except pydantic.ValidationError:
            return None, factory.bad_request(
                "Value property is not a properly formed search invoke value"
            )

        missing = []
        if not search_invoke_value.kind:
            if ChannelId.get_channel(context.activity.channel_id) == Channels.ms_teams:
                search_invoke_value.kind = "search"
            else:
                missing.append("kind")

        if not search_invoke_value.query_text:
            missing.append("queryText")

        if missing:
            return None, factory.bad_request(
                f"Missing '{', '.join(missing)}' property for search"
            )
        return search_invoke_value, AdaptiveCardInvokeResponse()

    @staticmethod
    def _matches(selector: str | Pattern[str], value: object) -> bool:
        if not isinstance(value, str):
            return False
        if isinstance(selector, str):
            return selector == value
        return selector.search(value) is not None

    @staticmethod
    async def _send_invoke_response(
        context: TurnContext,
        body: AdaptiveCardInvokeResponse,
        status_code: int | HTTPStatus = HTTPStatus.OK,
    ) -> None:
        await context.send_activity(
            Activity(
                type=ActivityTypes.invoke_response,
                value=InvokeResponse(
                    status=int(status_code),
                    body=body.model_dump(mode="json", by_alias=True, exclude_none=True),
                ),
            )
        )
