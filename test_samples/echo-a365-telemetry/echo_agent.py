# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Echo Agent — relays user text to an Azure OpenAI endpoint.

The entire agent logic is intentionally minimal so that the telemetry
infrastructure (spans, metrics, baggage, token caching) stays in the
foreground.  The AI call is a single-turn, stateless chat completion:

    User text → Azure OpenAI (openai) → reply to user

No conversation history, no tools, no state persistence.
"""

import logging
import traceback
from os import environ

from openai import AzureOpenAI

from microsoft_agents.hosting.core import Authorization, TurnContext, TurnState

from telemetry import invoke_observed_agent_operation_with_context

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = environ.get(
    "AGENT_SYSTEM_PROMPT",
    "You are a helpful assistant. Respond concisely to the user's message.",
)
_WELCOME_MESSAGE = environ.get(
    "AGENT_WELCOME_MESSAGE",
    "Hello! I'm the Echo Agent. Send me any message and I'll relay it to Azure OpenAI.",
)


def _build_client() -> AzureOpenAI:
    """Build an AzureOpenAI client.

    Requires AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY to be set.
    """
    return AzureOpenAI(
        azure_endpoint=environ["AZURE_OPENAI_ENDPOINT"],
        api_key=environ["AZURE_OPENAI_API_KEY"],
        api_version=environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    )


class EchoAgent:
    """Stateless agent that echoes user text through Azure OpenAI."""

    def __init__(self, user_authorization: Authorization = None):
        self._user_authorization = user_authorization
        self._client = _build_client()
        self._model = environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        logger.info("EchoAgent initialised (model=%s)", self._model)

    async def send_welcome(self, context: TurnContext, state: TurnState) -> None:
        """Greet each new participant when they join the conversation."""
        for member in context.activity.members_added or []:
            if member.id != context.activity.recipient.id:
                await context.send_activity(_WELCOME_MESSAGE)

    async def handle_message(self, context: TurnContext, state: TurnState) -> None:
        """Process an incoming message and relay the OpenAI reply to the user.

        The core logic is wrapped inside
        ``invoke_observed_agent_operation_with_context`` so that every
        invocation produces:
          - a distributed trace span with activity attributes
          - W3C baggage carrying tenant.id / agent.id
          - per-turn observability token caching
          - message counters and duration histograms
        """
        user_text = (context.activity.text or "").strip()
        if not user_text:
            return

        logger.info("Received: %s", user_text)

        async def _process() -> None:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_text},
                ],
            )
            reply = response.choices[0].message.content
            logger.info("OpenAI reply: %s", reply)
            await context.send_activity(reply)

        try:
            await invoke_observed_agent_operation_with_context(
                "OnMessageActivity",
                context,
                state,
                _process,
                user_authorization=self._user_authorization,
            )
        except Exception as exc:
            logger.error("Error processing message: %s", exc)
            traceback.print_exc()
            await context.send_activity(f"Sorry, I encountered an error: {exc}")
