# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
from os import environ
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

from microsoft_agents.activity import (
    ActivityTypes,
    AdaptiveCardInvokeResponse,
    ContentTypes,
    load_configuration_from_env,
)
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    AgentApplication,
    Authorization,
    MemoryStorage,
    TurnContext,
    TurnState,
)
from microsoft_agents.hosting.core.app.adaptive_card.models import (
    AdaptiveCardSearchResult,
)

from card_commands import handle_card_command, send_card_commands
from start_server import start_server

_ROOT = Path(__file__).parent
_RESOURCES = _ROOT / "resources"
_PYPI_PACKAGES = (
    "microsoft-agents-activity",
    "microsoft-agents-hosting-core",
    "microsoft-agents-hosting-aiohttp",
    "microsoft-agents-hosting-fastapi",
    "microsoft-agents-authentication-msal",
    "microsoft-agents-hosting-msteams",
    "microsoft-agents-storage-blob",
    "microsoft-agents-storage-cosmos",
    "microsoft-agents-copilotstudio-client",
)

load_dotenv(_ROOT / ".env")
config = load_configuration_from_env(environ)

storage = MemoryStorage()
connection_manager = MsalConnectionManager(**config)
adapter = CloudAdapter(connection_manager=connection_manager)
authorization = Authorization(storage, connection_manager, **config)

app = AgentApplication[TurnState](
    storage=storage,
    adapter=adapter,
    authorization=authorization,
    start_typing_timer=False,
    remove_recipient_mention=False,
    **config,
)


def _resource_text(name: str) -> str:
    return (_RESOURCES / name).read_text(encoding="utf-8")


@app.conversation_update("membersAdded")
async def on_members_added(context: TurnContext, _state: TurnState) -> None:
    await context.send_activity(
        "Hello and welcome! This sample demonstrates Adaptive Cards and "
        "activity-protocol cards."
    )
    await send_card_commands(context)


@app.adaptive_card.action_submit("StaticSubmit")
async def on_static_submit(
    context: TurnContext, _state: TurnState, data: object
) -> None:
    selection = data.get("choiceSelect") if isinstance(data, dict) else None
    await context.send_activity(f"Statically selected option: {selection}")


@app.adaptive_card.action_submit("DynamicSubmit")
async def on_dynamic_submit(
    context: TurnContext, _state: TurnState, data: object
) -> None:
    selection = data.get("choiceSelect") if isinstance(data, dict) else None
    await context.send_activity(f"Dynamically selected option: {selection}")


@app.adaptive_card.action_execute("refresh")
async def on_refresh(
    _context: TurnContext, _state: TurnState, _data: object
) -> AdaptiveCardInvokeResponse:
    return AdaptiveCardInvokeResponse(
        status_code=200,
        type=ContentTypes.adaptive_card,
        value=_resource_text("ActionExecuteSignIn.json"),
    )


@app.adaptive_card.action_execute("signin")
async def on_sign_in(
    context: TurnContext, _state: TurnState, _data: object
) -> AdaptiveCardInvokeResponse:
    await context.send_activity("Action.Execute sign-in handler called.")
    return AdaptiveCardInvokeResponse(
        status_code=200,
        type=ContentTypes.adaptive_card,
        value=_resource_text("ActionExecuteSignOut.json"),
    )


@app.adaptive_card.action_execute("signout")
async def on_sign_out(
    context: TurnContext, _state: TurnState, _data: object
) -> AdaptiveCardInvokeResponse:
    await context.send_activity("Action.Execute sign-out handler called.")
    return AdaptiveCardInvokeResponse(status_code=200)


async def _get_pypi_result(
    session: aiohttp.ClientSession, package_name: str
) -> AdaptiveCardSearchResult | None:
    async with session.get(
        f"https://pypi.org/pypi/{package_name}/json"
    ) as response:
        if response.status == 404:
            return None
        response.raise_for_status()
        payload = await response.json()

    info = payload.get("info", {})
    name = info.get("name") or package_name
    version = info.get("version") or ""
    summary = info.get("summary") or "No description available."
    return AdaptiveCardSearchResult(
        title=name,
        value=f"{name} {version} - {summary}".strip(),
    )


@app.adaptive_card.search("pypipackages")
async def on_search(
    _context: TurnContext, _state: TurnState, query
) -> list[AdaptiveCardSearchResult]:
    query_text = query.parameters.query_text.strip().lower().replace("_", "-")
    candidates = [
        package_name
        for package_name in _PYPI_PACKAGES
        if query_text in package_name
    ]
    if query_text and query_text not in candidates:
        candidates.append(query_text)

    start = query.skip
    stop = start + query.count
    candidates = candidates[start:stop]

    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            *(_get_pypi_result(session, name) for name in candidates)
        )

    return [result for result in results if result is not None]


@app.activity(ActivityTypes.message)
async def on_message(context: TurnContext, _state: TurnState) -> None:
    await handle_card_command(context)


if __name__ == "__main__":
    start_server(
        agent_application=app,
        auth_configuration=(
            connection_manager.get_default_connection_configuration()
        ),
    )
