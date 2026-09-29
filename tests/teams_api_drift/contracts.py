# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Mypy-only contracts for the upstream types consumed and exposed by the SDK."""

from typing import Any, assert_type

from microsoft_teams.api import ApiClient
from microsoft_teams.common import ClientOptions
from microsoft_teams.api.models import (
    AppBasedLinkQuery,
    ChannelData,
    ChannelInfo,
    ConfigResponse,
    FeedbackLoop,
    FileConsentCardResponse,
    MeetingInfo,
    MessagingExtensionAction,
    MessagingExtensionActionResponse,
    MessagingExtensionQuery,
    MessagingExtensionResponse,
    NotificationInfo,
    O365ConnectorCardActionQuery,
    TaskModuleRequest,
    TaskModuleResponse,
    TeamInfo,
)
from microsoft_teams.api.models.meetings import MeetingDetails

from microsoft_agents.activity import Activity
from microsoft_agents.hosting.core import TurnState
from microsoft_agents.hosting.msteams.teams_activity import TeamsActivity
from microsoft_agents.hosting.msteams.teams_turn_context import TeamsTurnContext
from microsoft_agents.hosting.msteams.task_module.route_handlers import FetchHandler
from microsoft_agents.hosting.msteams.message_extension.route_handlers import (
    QueryHandler,
)


async def token() -> str:
    return "contract-token"


def client_contract(context: TeamsTurnContext) -> ApiClient:
    options = ClientOptions(
        base_url="https://service.example.com",
        headers={"Accept": "application/json"},
        token=token,
    )
    client = ApiClient("https://service.example.com", options)
    assert_type(client.service_url, str)
    assert_type(context.api_client, ApiClient)
    return client


def model_contract(
    activity: TeamsActivity,
    query: MessagingExtensionQuery,
    action: MessagingExtensionAction,
    link: AppBasedLinkQuery,
    request: TaskModuleRequest,
) -> None:
    assert_type(activity.get_channel_id(), str | None)
    assert_type(activity.get_meeting_info(), MeetingInfo | None)
    assert_type(activity.get_team_info(), TeamInfo | None)
    data = ChannelData.model_validate({})
    assert_type(data.channel, ChannelInfo | None)
    assert_type(data.team, TeamInfo | None)
    assert_type(data.event_type, str | None)
    if data.settings and data.settings.selected_channel:
        channel_id: str | None = data.settings.selected_channel.id
        consume(channel_id)
    data.notification = NotificationInfo(
        alert=True, alert_in_meeting=False, external_resource_url="https://example.com"
    )
    data.feedback_loop = FeedbackLoop(type="default")
    consume(
        query.command_id,
        query.parameters,
        query.query_options,
        query.state,
        action.data,
        action.bot_activity_preview,
        link.url,
        link.state,
        request.data,
    )
    if query.parameters:
        consume(query.parameters[0].name, query.parameters[0].value)
    if query.query_options:
        consume(query.query_options.count, query.query_options.skip)


async def handler_contract(
    context: TeamsTurnContext,
    state: TurnState,
    fetch: FetchHandler[TurnState],
    query: QueryHandler[TurnState],
    request: TaskModuleRequest,
    payload: MessagingExtensionQuery,
) -> None:
    task_response: TaskModuleResponse = await fetch(context, state, request)
    query_response: MessagingExtensionResponse = await query(context, state, payload)
    consume(
        task_response.model_dump(mode="json", by_alias=True, exclude_none=True),
        query_response,
    )


def forwarded_contract(
    config: ConfigResponse,
    consent: FileConsentCardResponse,
    meeting: MeetingDetails,
    action: MessagingExtensionActionResponse,
    connector: O365ConnectorCardActionQuery,
    activity: Activity,
) -> None:
    consume(config, consent, meeting, action, connector, activity)


def consume(*values: Any) -> None:
    pass
