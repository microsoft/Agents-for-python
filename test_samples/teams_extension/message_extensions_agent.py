# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Teams Message Extensions sample.

Mirrors the AgentApplication-based MessageExtensions sample from
microsoft/Agents-for-net PR #740 (src/samples/Teams/MessageExtensions),
adapted to Python's TeamsAgentExtension and using the Teams SDK Pydantic
models from microsoft_teams.api.models.
"""

import logging
from os import environ, path
from dotenv import load_dotenv

from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState,
)
from microsoft_agents.hosting.core.app.oauth.authorization import Authorization
from microsoft_agents.hosting.teams import TeamsAgentExtension
from microsoft_teams.api.models import (
    MessagingExtensionAction,
    MessagingExtensionActionResponse,
    MessagingExtensionAttachment,
    MessagingExtensionAttachmentLayout,
    MessagingExtensionQuery,
    MessagingExtensionResponse,
    MessagingExtensionResult,
    MessagingExtensionResultType,
    AppBasedLinkQuery,
)

from shared import start_server

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

load_dotenv(path.join(path.dirname(__file__), ".env"))
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
TEAMS = TeamsAgentExtension[TurnState](AGENT_APP)


def _adaptive_card(title: str, body_text: str) -> dict:
    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {"type": "TextBlock", "text": title, "weight": "Bolder", "size": "Large"},
            {"type": "TextBlock", "text": body_text, "wrap": True, "isSubtle": True},
        ],
    }


def _thumbnail(title: str, text: str, tap_value: dict) -> dict:
    return {
        "title": title,
        "text": text,
        "tap": {"type": "invoke", "value": tap_value},
    }


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, _state: TurnState):
    await context.send_activity(
        f"Echo: {context.activity.text}\n\n"
        "This is a message extension sample. Use the message extension commands "
        "in Teams to test functionality."
    )


# ── composeExtension/query (search-based) ──────────────────────────────────

@TEAMS.message_extension.on_query("searchQuery")
async def on_search_query(
    context: TurnContext, _state: TurnState, query: MessagingExtensionQuery
) -> MessagingExtensionResponse:
    params = {p.name: p.value for p in (query.parameters or [])}
    if str(params.get("initialRun", "")).lower() == "true":
        return MessagingExtensionResponse(
            compose_extension=MessagingExtensionResult(
                type=MessagingExtensionResultType.MESSAGE,
                text="Enter search query",
            )
        )

    search_text = str(params.get("searchQuery", "") or "")
    log.info("Search query received: %s", search_text)

    attachments = []
    for i in range(1, 6):
        card = _adaptive_card(
            f"Search Result {i}",
            f"Query: '{search_text}' — result description for item {i}",
        )
        preview = _thumbnail(
            title=f"Result {i}",
            text=f"Preview of result {i} for query '{search_text}'.",
            tap_value={"index": str(i), "query": search_text},
        )
        attachments.append(
            MessagingExtensionAttachment(
                content_type="application/vnd.microsoft.card.adaptive",
                content=card,
                preview=MessagingExtensionAttachment(
                    content_type="application/vnd.microsoft.card.thumbnail",
                    content=preview,
                ),
            )
        )

    return MessagingExtensionResponse(
        compose_extension=MessagingExtensionResult(
            type=MessagingExtensionResultType.RESULT,
            attachment_layout=MessagingExtensionAttachmentLayout.LIST,
            attachments=attachments,
        )
    )


# ── composeExtension/selectItem (item tap from a search result) ────────────

@TEAMS.message_extension.on_select_item
async def on_select_item(
    context: TurnContext, _state: TurnState, item
) -> MessagingExtensionResponse:
    item = item or {}
    index = item.get("index", "No Index")
    query = item.get("query", "No Query")
    log.info("Item selected: %s:%s", index, query)

    card = _adaptive_card(
        "Item Selected",
        f"You selected item {index} for query '{query}'.",
    )
    return MessagingExtensionResponse(
        compose_extension=MessagingExtensionResult(
            type=MessagingExtensionResultType.RESULT,
            attachment_layout=MessagingExtensionAttachmentLayout.LIST,
            attachments=[
                MessagingExtensionAttachment(
                    content_type="application/vnd.microsoft.card.adaptive",
                    content=card,
                )
            ],
        )
    )


# ── composeExtension/submitAction (action-based, "createCard") ─────────────

@TEAMS.message_extension.on_submit_action("createCard")
async def on_create_card(
    context: TurnContext, _state: TurnState, action: MessagingExtensionAction
) -> MessagingExtensionResponse:
    data = action.data if isinstance(action.data, dict) else {}
    title = data.get("title") or "Default Title"
    description = data.get("description") or "Default Description"
    log.info("Creating card: title=%s description=%s", title, description)

    card = _adaptive_card(title, description)
    return MessagingExtensionResponse(
        compose_extension=MessagingExtensionResult(
            type=MessagingExtensionResultType.RESULT,
            attachment_layout=MessagingExtensionAttachmentLayout.LIST,
            attachments=[
                MessagingExtensionAttachment(
                    content_type="application/vnd.microsoft.card.adaptive",
                    content=card,
                )
            ],
        )
    )


# ── composeExtension/queryLink (link unfurling) ────────────────────────────

@TEAMS.message_extension.on_query_link
async def on_query_link(
    context: TurnContext, _state: TurnState, query: AppBasedLinkQuery
) -> MessagingExtensionResponse:
    url = query.url or ""
    log.info("Link query: %s", url)

    if not url:
        return MessagingExtensionResponse(
            compose_extension=MessagingExtensionResult(
                type=MessagingExtensionResultType.MESSAGE,
                text="No URL provided",
            )
        )

    card = _adaptive_card("Link Preview", f"URL: {url}")
    return MessagingExtensionResponse(
        compose_extension=MessagingExtensionResult(
            type=MessagingExtensionResultType.RESULT,
            attachment_layout=MessagingExtensionAttachmentLayout.LIST,
            attachments=[
                MessagingExtensionAttachment(
                    content_type="application/vnd.microsoft.card.adaptive",
                    content=card,
                    preview=MessagingExtensionAttachment(
                        content_type="application/vnd.microsoft.card.thumbnail",
                        content=_thumbnail("Link Preview", url, {}),
                    ),
                )
            ],
        )
    )


# ── composeExtension/querySettingUrl ───────────────────────────────────────

@TEAMS.message_extension.on_query_url_setting
async def on_query_settings_url(
    context: TurnContext, _state: TurnState, _query: MessagingExtensionQuery
) -> MessagingExtensionResponse:
    log.info("Query settings URL requested")
    return MessagingExtensionResponse(
        compose_extension=MessagingExtensionResult(
            type=MessagingExtensionResultType.CONFIG,
            suggested_actions={
                "actions": [
                    {
                        "type": "openUrl",
                        "title": "Configure",
                        "value": "https://example.com/settings",
                    }
                ]
            },
        )
    )


# ── composeExtension/setting (apply settings) ──────────────────────────────

@TEAMS.message_extension.on_configure_settings
async def on_configure_settings(
    context: TurnContext, _state: TurnState, settings
):
    log.info("Configure settings: %s", settings)


# ── composeExtension/fetchTask ─────────────────────────────────────────────

@TEAMS.message_extension.on_fetch_task()
async def on_fetch_task(
    context: TurnContext, _state: TurnState, action: MessagingExtensionAction
) -> MessagingExtensionActionResponse:
    log.info("FetchTask: command=%s", action.command_id)
    card = _adaptive_card(
        "Create a card",
        "Submit a title and description to generate an Adaptive Card.",
    )
    return MessagingExtensionActionResponse(
        task={
            "type": "continue",
            "value": {
                "title": "Create Card",
                "height": "small",
                "width": "small",
                "card": {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": card,
                },
            },
        }
    )


if __name__ == "__main__":
    start_server(
        agent_application=AGENT_APP,
        auth_configuration=CONNECTION_MANAGER.get_default_connection_configuration(),
    )
