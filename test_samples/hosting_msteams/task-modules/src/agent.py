# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams Task Modules agent — Python port of the .NET TaskModules sample.

Demonstrates the task module (dialog) surface through ``task/fetch`` and
``task/submit`` invokes: an Adaptive Card form, a webpage dialog, a multi-step
form, and a deep-link "mixed" example. Mirrors src/samples/Teams/TaskModules
from the microsoft/Agents-for-net repository.
"""

import logging
from os import environ

from dotenv import load_dotenv

from microsoft_teams.api.models import TaskModuleRequest, TaskModuleResponse

from microsoft_agents.activity import Attachment, load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    AgentApplication,
    Authorization,
    MemoryStorage,
    MessageFactory,
    TurnState,
)
from microsoft_agents.hosting.core.storage import (
    ConsoleTranscriptLogger,
    TranscriptLoggerMiddleware,
)
from microsoft_agents.hosting.msteams import TeamsAgentExtension
from microsoft_agents.hosting.msteams.teams_turn_context import TeamsTurnContext

from .card_loader import load_card_json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

agents_sdk_config = load_configuration_from_env(environ)

# Public base URL of this agent (dev tunnel / host) used for the webpage dialog.
APP_BASE_URL = environ.get("APP_BASE_URL", "http://localhost:3978")

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
ADAPTER.use(TranscriptLoggerMiddleware(ConsoleTranscriptLogger()))
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE,
    adapter=ADAPTER,
    authorization=AUTHORIZATION,
    **agents_sdk_config,
)

teams = TeamsAgentExtension[TurnState](AGENT_APP)

_ADAPTIVE_CONTENT_TYPE = "application/vnd.microsoft.card.adaptive"


def _continue_card_response(
    title: str, card_content: dict, *, height: str = "small", width: str = "small"
) -> TaskModuleResponse:
    """Build a ``continue`` task response that renders an Adaptive Card dialog."""
    return TaskModuleResponse.model_validate(
        {
            "task": {
                "type": "continue",
                "value": {
                    "title": title,
                    "height": height,
                    "width": width,
                    "card": {
                        "contentType": _ADAPTIVE_CONTENT_TYPE,
                        "content": card_content,
                    },
                },
            }
        }
    )


def _continue_url_response(
    title: str, url: str, *, height: int = 500, width: int = 800
) -> TaskModuleResponse:
    """Build a ``continue`` task response that renders a hosted webpage dialog."""
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
    """Build a ``message`` task response that closes the dialog with a toast."""
    return TaskModuleResponse.model_validate(
        {"task": {"type": "message", "value": text}}
    )


def _launcher_card() -> Attachment:
    """Welcome card whose buttons launch each task module via task/fetch."""
    return Attachment(
        content_type=_ADAPTIVE_CONTENT_TYPE,
        content=load_card_json("launcher-card.json"),
    )


# ── Default message — send the launcher card ─────────────────────────────────


@teams.activity("message")
async def on_message(context: TeamsTurnContext, state: TurnState) -> None:
    await context.send_activity(MessageFactory.attachment(_launcher_card()))


# ── Simple Form ──────────────────────────────────────────────────────────────


@teams.task_modules.fetch("simple_form")
async def on_simple_form_fetch(
    context: TeamsTurnContext, state: TurnState, request: TaskModuleRequest
) -> TaskModuleResponse:
    return _continue_card_response(
        "Simple Form", load_card_json("simple-form-card.json")
    )


@teams.task_modules.submit("simple_form")
async def on_simple_form_submit(
    context: TeamsTurnContext, state: TurnState, request: TaskModuleRequest
) -> TaskModuleResponse:
    data = request.data if isinstance(request.data, dict) else {}
    name = data.get("name", "Unknown")
    await context.send_activity(f"Hi {name}, thanks for submitting the form!")
    return _message_response("Form was submitted")


# ── Webpage Dialog ───────────────────────────────────────────────────────────


@teams.task_modules.fetch("webpage_dialog")
async def on_webpage_dialog_fetch(
    context: TeamsTurnContext, state: TurnState, request: TaskModuleRequest
) -> TaskModuleResponse:
    return _continue_url_response("Webpage Dialog", f"{APP_BASE_URL}/dialog-form")


@teams.task_modules.submit("webpage_dialog")
async def on_webpage_dialog_submit(
    context: TeamsTurnContext, state: TurnState, request: TaskModuleRequest
) -> TaskModuleResponse:
    data = request.data if isinstance(request.data, dict) else {}
    name = data.get("name", "Unknown")
    email = data.get("email", "No email provided")
    await context.send_activity(
        f"Hi {name}, thanks for submitting the form! We got that your email is {email}"
    )
    return _message_response("Form submitted successfully")


# ── Multi-Step Form ──────────────────────────────────────────────────────────


@teams.task_modules.fetch("multi_step_form")
async def on_multi_step_fetch(
    context: TeamsTurnContext, state: TurnState, request: TaskModuleRequest
) -> TaskModuleResponse:
    return _continue_card_response(
        "Multi-step Form Dialog", load_card_json("multi-step-name-card.json")
    )


@teams.task_modules.submit("multi_step_form_submit_name")
async def on_multi_step_submit_name(
    context: TeamsTurnContext, state: TurnState, request: TaskModuleRequest
) -> TaskModuleResponse:
    data = request.data if isinstance(request.data, dict) else {}
    name = data.get("name", "Unknown")
    return _continue_card_response(
        f"Thanks {name} - Get Email",
        load_card_json("multi-step-email-card.json", tokens={"name": name}),
    )


@teams.task_modules.submit("multi_step_form_submit_email")
async def on_multi_step_submit_email(
    context: TeamsTurnContext, state: TurnState, request: TaskModuleRequest
) -> TaskModuleResponse:
    data = request.data if isinstance(request.data, dict) else {}
    name = data.get("name", "Unknown")
    email = data.get("email", "No email provided")
    await context.send_activity(
        f"Hi {name}, thanks for submitting the form! We got that your email is {email}"
    )
    return _message_response("Multi-step form completed successfully")


# ── Mixed Example (deep-link task module) ────────────────────────────────────


@teams.task_modules.fetch("mixed_example")
async def on_mixed_example_fetch(
    context: TeamsTurnContext, state: TurnState, request: TaskModuleRequest
) -> TaskModuleResponse:
    return _continue_url_response(
        "Mixed Example",
        "https://teams.microsoft.com/l/task/example-mixed",
        height=600,
        width=800,
    )
