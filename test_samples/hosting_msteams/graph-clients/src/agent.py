# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams sample that creates and uses app-only and delegated Graph clients."""

import logging
from os import environ

from dotenv import load_dotenv

from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    AgentApplication,
    Authorization,
    MemoryStorage,
    TurnState,
)
from microsoft_agents.hosting.msteams import TeamsAgentExtension
from microsoft_agents.hosting.msteams.teams_turn_context import TeamsTurnContext

logger = logging.getLogger(__name__)
load_dotenv()

agents_sdk_config = load_configuration_from_env(environ)

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE,
    adapter=ADAPTER,
    authorization=AUTHORIZATION,
    **agents_sdk_config,
)

teams = TeamsAgentExtension[TurnState](AGENT_APP)


def _none_if_empty(value: str | None) -> str | None:
    return value if value else None


@teams.message("/appgraph apps")
async def on_app_graph_apps(context: TeamsTurnContext, state: TurnState) -> None:
    """Create an app-only Graph client and read one application registration."""
    graph = context.get_app_graph_client()
    query = graph.applications.ApplicationsRequestBuilderGetQueryParameters(
        top=1,
        select=["id", "appId", "displayName"],
    )
    config_cls = graph.applications.ApplicationsRequestBuilderGetRequestConfiguration
    request_config = config_cls(query_parameters=query)
    response = await graph.applications.get(request_config)
    applications = response.value if response and response.value else []

    if not applications:
        await context.send_activity("No application registrations were returned.")
        return

    app = applications[0]
    display_name = _none_if_empty(app.display_name) or "(no display name)"
    await context.send_activity(
        "App Graph client returned an application:\n\n"
        f"- Display name: {display_name}\n"
        f"- App ID: {_none_if_empty(app.app_id) or '(none)'}\n"
        f"- Object ID: {_none_if_empty(app.id) or '(none)'}"
    )


@teams.message("/usergraph me", auth_handlers=["GRAPH"])
async def on_user_graph_me(context: TeamsTurnContext, state: TurnState) -> None:
    """Create a delegated user Graph client and read the signed-in user."""
    graph = context.get_graph_client("GRAPH")
    query = graph.me.UserItemRequestBuilderGetQueryParameters(
        select=["id", "displayName", "userPrincipalName", "mail"],
    )
    request_config = graph.me.UserItemRequestBuilderGetRequestConfiguration(
        query_parameters=query
    )
    user = await graph.me.get(request_config)

    if not user:
        await context.send_activity("Microsoft Graph did not return a user.")
        return

    display_name = _none_if_empty(user.display_name) or "(no display name)"
    user_principal_name = _none_if_empty(user.user_principal_name) or "(no UPN)"
    mail = _none_if_empty(user.mail) or "(no mail)"
    await context.send_activity(
        "User Graph client returned the signed-in user:\n\n"
        f"- Display name: {display_name}\n"
        f"- UPN: {user_principal_name}\n"
        f"- Mail: {mail}\n"
        f"- Object ID: {_none_if_empty(user.id) or '(none)'}"
    )


@teams.message("/signout")
async def on_sign_out(context: TeamsTurnContext, state: TurnState) -> None:
    await AGENT_APP.auth.sign_out(context, "GRAPH")
    await context.send_activity(f"Signed out of GRAPH.")


@teams.activity("message")
async def on_message(context: TeamsTurnContext, state: TurnState) -> None:
    await context.send_activity(
        "Graph clients sample commands:\n\n"
        "- `/appgraph apps` - app-only Graph client call to /applications\n"
        "- `/usergraph me` - delegated user Graph client call to /me\n"
        "- `/signout` - sign out of the delegated Graph auth handler"
    )
