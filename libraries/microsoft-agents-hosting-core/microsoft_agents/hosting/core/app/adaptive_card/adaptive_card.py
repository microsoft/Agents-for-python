# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import asdict
from http import HTTPStatus
import re
from typing import TYPE_CHECKING, Callable, Pattern

from microsoft_agents.activity import (
    AgentsModel,
    Activity,
    ActivityTypes,
    AdaptiveCardInvokeResponse,
    AdaptiveCardInvokeValue,
    Channels,
    InvokeResponse,
)
from microsoft_agents.hosting.core.turn_context import TurnContext

from .._type_defs import RouteSelector
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
_DEFAULT_ACTION_SUBMIT_FILTER = "verb"

Selector = str | Pattern[str] | RouteSelector


class AdaptiveCard:
    """Register handlers for Adaptive Card activities."""

    def __init__(self, app: "AgentApplication"):
        """Initialize an Adaptive Card route registrar for an application."""
        self._app = app

    def action_execute(
        self,
        verb_or_selector: Selector,
        *,
        auth_handlers: list[str] | None = None,
        **kwargs,
    ) -> Callable[[ActionExecuteHandler], ActionExecuteHandler]:
        """Register an ``Action.Execute`` handler that receives the action data."""
        return self._action_execute(
            verb_or_selector,
            auth_handlers=auth_handlers,
            **kwargs,
        )

    def action_submit(
        self,
        verb_or_selector: Selector,
        *,
        auth_handlers: list[str] | None = None,
        **kwargs,
    ) -> Callable[[ActionSubmitHandler], ActionSubmitHandler]:
        """Register an Adaptive Card ``Action.Submit`` handler."""
        submit_filter = self._action_submit_filter()

        def selector(context: TurnContext) -> bool:
            activity = context.activity
            if (
                activity.type != ActivityTypes.message
                or activity.text
                or activity.value is None
            ):
                return False

            if callable(verb_or_selector) and not isinstance(
                verb_or_selector, re.Pattern
            ):
                return verb_or_selector(context)

            value = self._as_mapping(activity.value)
            verb = value.get(submit_filter) if value else None
            return self._matches(verb_or_selector, verb)

        def register(func: ActionSubmitHandler) -> ActionSubmitHandler:
            async def handler(context: TurnContext, state: TurnState) -> None:
                await func(context, state, context.activity.value)

            kwargs.pop("is_invoke", None)
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
        dataset_or_selector: Selector,
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

            if callable(dataset_or_selector) and not isinstance(
                dataset_or_selector, re.Pattern
            ):
                return dataset_or_selector(context)

            value = self._as_mapping(activity.value)
            dataset = value.get("dataset") if value else None
            return self._matches(dataset_or_selector, dataset)

        def register(func: SearchHandler) -> SearchHandler:
            async def handler(context: TurnContext, state: TurnState) -> None:
                value, response = self._validate_search_value(context)
                if value is not None:
                    options = self._as_mapping(value.get("queryOptions")) or {}
                    query = Query(
                        count=self._as_int(options.get("top")),
                        skip=self._as_int(options.get("skip")),
                        parameters=AdaptiveCardSearchParams(
                            query_text=value["queryText"],
                            dataset=value.get("dataset") or "",
                        ),
                    )
                    results = await func(context, state, query)
                    response = factory.search_response(
                        {"results": [asdict(result) for result in results]}
                    )

                await self._send_invoke_response(
                    context,
                    response,
                    response.status_code or HTTPStatus.OK,
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

    def _action_execute(
        self,
        verb_or_selector: Selector,
        *,
        auth_handlers: list[str] | None,
        **kwargs,
    ) -> Callable:
        def selector(context: TurnContext) -> bool:
            activity = context.activity
            if (
                activity.type != ActivityTypes.invoke
                or activity.name != _ACTION_INVOKE_NAME
            ):
                return False

            value = self._as_mapping(activity.value)
            action = self._as_mapping(value.get("action")) if value else None

            if callable(verb_or_selector) and not isinstance(
                verb_or_selector, re.Pattern
            ):
                return verb_or_selector(context)

            return self._matches(
                verb_or_selector, action.get("verb") if action else None
            )

        def register(func: Callable) -> Callable:
            async def handler(context: TurnContext, state: TurnState) -> None:
                invoke_value, response = self._validate_action_execute_value(context)
                if invoke_value is not None:
                    response = await func(context, state, invoke_value.action.data)

                await self._send_invoke_response(context, response, HTTPStatus.OK)

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
        except (TypeError, ValueError):
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
    ) -> tuple[dict | None, AdaptiveCardInvokeResponse]:
        value = self._as_mapping(context.activity.value)
        if value is None:
            return None, factory.bad_request("Missing value property for search")

        missing = []
        if not value.get("kind"):
            if self._is_teams(context):
                value["kind"] = "search"
            else:
                missing.append("kind")
        if not value.get("queryText"):
            missing.append("queryText")

        if missing:
            return None, factory.bad_request(
                f"Missing '{', '.join(missing)}' property for search"
            )
        return value, AdaptiveCardInvokeResponse()

    def _action_submit_filter(self) -> str:
        options = getattr(self._app.options, "adaptive_cards", None)
        return (
            getattr(options, "action_submit_filter", None)
            or _DEFAULT_ACTION_SUBMIT_FILTER
        )

    @staticmethod
    def _as_mapping(value: object) -> dict | None:
        if isinstance(value, dict):
            return value.copy()
        if isinstance(value, AgentsModel):
            result = value.model_dump(mode="json", by_alias=True, exclude_none=True)
            return result if isinstance(result, dict) else None
        return None

    @staticmethod
    def _matches(selector: str | Pattern[str], value: object) -> bool:
        if not isinstance(value, str):
            return False
        if isinstance(selector, str):
            return selector == value
        return re.fullmatch(selector, value) is not None

    @staticmethod
    def _as_int(value: object) -> int:
        return value if isinstance(value, int) and not isinstance(value, bool) else 0

    @staticmethod
    def _is_teams(context: TurnContext) -> bool:
        channel_id = context.activity.channel_id
        channel = getattr(channel_id, "channel", channel_id)
        return channel == Channels.ms_teams or channel == Channels.ms_teams.value

    @staticmethod
    async def _send_invoke_response(
        context: TurnContext,
        body: AdaptiveCardInvokeResponse,
        status: int,
    ) -> None:
        await context.send_activity(
            Activity(
                type=ActivityTypes.invoke_response,
                value=InvokeResponse(
                    status=int(status),
                    body=body.model_dump(mode="json", by_alias=True, exclude_none=True),
                ),
            )
        )
