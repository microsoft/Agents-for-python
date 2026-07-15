# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Teams Task Modules sample.

Mirrors the AgentApplication-based TaskModules sample from
microsoft/Agents-for-net PR #740 (src/samples/Teams/TaskModules), adapted
to Python's TeamsAgentExtension.
"""

import logging
from os import environ, path
from dotenv import load_dotenv

from microsoft_agents.activity import Attachment, load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    MessageFactory,
    TurnContext,
    TurnState,
)
from microsoft_agents.hosting.core.app.oauth.authorization import Authorization
from microsoft_agents.hosting.teams import TeamsAgentExtension
from microsoft_teams.api.models import TaskModuleRequest, TaskModuleResponse

from shared import start_server

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

load_dotenv(path.join(path.dirname(__file__), ".env"))
agents_sdk_config = load_configuration_from_env(environ)

APP_BASE_URL = environ.get("APP_BASE_URL", "http://localhost:3978")

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


def _launcher_card() -> Attachment:
    """Welcome card with buttons that open each task module via task/fetch."""
    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content={
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.5",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Task Module Demos",
                    "weight": "Bolder",
                    "size": "Large",
                },
                {
                    "type": "TextBlock",
                    "text": "Pick a task module to launch.",
                    "wrap": True,
                },
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Simple Form",
                    "data": {"msteams": {"type": "task/fetch"}, "data": {"verb": "simple_form"}},
                },
                {
                    "type": "Action.Submit",
                    "title": "Webpage Dialog",
                    "data": {"msteams": {"type": "task/fetch"}, "data": {"verb": "webpage_dialog"}},
                },
                {
                    "type": "Action.Submit",
                    "title": "Multi-Step Form",
                    "data": {"msteams": {"type": "task/fetch"}, "data": {"verb": "multi_step_form"}},
                },
            ],
        },
    )


def _continue_card_response(
    title: str, card_content: dict, *, height: str = "small", width: str = "small"
) -> TaskModuleResponse:
    return TaskModuleResponse.model_validate(
        {
            "task": {
                "type": "continue",
                "value": {
                    "title": title,
                    "height": height,
                    "width": width,
                    "card": {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": card_content,
                    },
                },
            }
        }
    )


def _continue_url_response(
    title: str, url: str, *, height: int = 500, width: int = 800
) -> TaskModuleResponse:
    return TaskModuleResponse.model_validate(
        {
            "task": {
                "type": "continue",
                "value": {
                    "title": title,
                    "height": height,
                    "width": width,
                    "url": url,
                    "fallbackUrl": url,
                },
            }
        }
    )


def _message_response(text: str) -> TaskModuleResponse:
    return TaskModuleResponse.model_validate(
        {"task": {"type": "message", "value": text}}
    )


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, _state: TurnState):
    await context.send_activity(MessageFactory.attachment(_launcher_card()))


# ── Simple Form ────────────────────────────────────────────────────────────

_SIMPLE_FORM_CARD = {
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "type": "AdaptiveCard",
    "version": "1.5",
    "body": [
        {"type": "TextBlock", "text": "Simple Form", "weight": "Bolder", "size": "Medium"},
        {"type": "Input.Text", "id": "name", "label": "Name", "isRequired": True},
    ],
    "actions": [
        {
            "type": "Action.Submit",
            "title": "Submit",
            "data": {"verb": "simple_form"},
        }
    ],
}


@TEAMS.task_module.on_fetch("simple_form")
async def on_simple_form_fetch(
    context: TurnContext, _state: TurnState, _request: TaskModuleRequest
) -> TaskModuleResponse:
    return _continue_card_response("Simple Form", _SIMPLE_FORM_CARD)


@TEAMS.task_module.on_submit("simple_form")
async def on_simple_form_submit(
    context: TurnContext, _state: TurnState, request: TaskModuleRequest
) -> TaskModuleResponse:
    data = request.data if isinstance(request.data, dict) else {}
    name = data.get("name", "Unknown")
    await context.send_activity(f"Hi {name}, thanks for submitting the form!")
    return _message_response("Form was submitted")


# ── Webpage Dialog ─────────────────────────────────────────────────────────

@TEAMS.task_module.on_fetch("webpage_dialog")
async def on_webpage_dialog_fetch(
    context: TurnContext, _state: TurnState, _request: TaskModuleRequest
) -> TaskModuleResponse:
    return _continue_url_response("Webpage Dialog", f"{APP_BASE_URL}/dialog-form")


@TEAMS.task_module.on_submit("webpage_dialog")
async def on_webpage_dialog_submit(
    context: TurnContext, _state: TurnState, request: TaskModuleRequest
) -> TaskModuleResponse:
    data = request.data if isinstance(request.data, dict) else {}
    name = data.get("name", "Unknown")
    email = data.get("email", "no email")
    await context.send_activity(
        f"Hi {name}, thanks for submitting the form! Your email is {email}."
    )
    return _message_response("Form submitted successfully")


# ── Multi-Step Form ────────────────────────────────────────────────────────

_MULTI_STEP_NAME_CARD = {
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "type": "AdaptiveCard",
    "version": "1.5",
    "body": [
        {"type": "TextBlock", "text": "Step 1 — your name", "weight": "Bolder"},
        {"type": "Input.Text", "id": "name", "label": "Name", "isRequired": True},
    ],
    "actions": [
        {
            "type": "Action.Submit",
            "title": "Next",
            "data": {"verb": "multi_step_form_submit_name"},
        }
    ],
}


def _multi_step_email_card(name: str) -> dict:
    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {"type": "TextBlock", "text": f"Step 2 — email for {name}", "weight": "Bolder"},
            {"type": "Input.Text", "id": "email", "label": "Email", "isRequired": True},
            {"type": "Input.Text", "id": "name", "value": name, "isVisible": False},
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Submit",
                "data": {"verb": "multi_step_form_submit_email"},
            }
        ],
    }


@TEAMS.task_module.on_fetch("multi_step_form")
async def on_multi_step_fetch(
    context: TurnContext, _state: TurnState, _request: TaskModuleRequest
) -> TaskModuleResponse:
    return _continue_card_response("Multi-step Form — Name", _MULTI_STEP_NAME_CARD)


@TEAMS.task_module.on_submit("multi_step_form_submit_name")
async def on_multi_step_submit_name(
    context: TurnContext, _state: TurnState, request: TaskModuleRequest
) -> TaskModuleResponse:
    data = request.data if isinstance(request.data, dict) else {}
    name = data.get("name", "Unknown")
    return _continue_card_response(
        f"Thanks {name} — your email", _multi_step_email_card(name)
    )


@TEAMS.task_module.on_submit("multi_step_form_submit_email")
async def on_multi_step_submit_email(
    context: TurnContext, _state: TurnState, request: TaskModuleRequest
) -> TaskModuleResponse:
    data = request.data if isinstance(request.data, dict) else {}
    name = data.get("name", "Unknown")
    email = data.get("email", "no email")
    await context.send_activity(
        f"Hi {name}, thanks for submitting the form! Your email is {email}."
    )
    return _message_response("Multi-step form completed successfully")


if __name__ == "__main__":
    start_server(
        agent_application=AGENT_APP,
        auth_configuration=CONNECTION_MANAGER.get_default_connection_configuration(),
    )
