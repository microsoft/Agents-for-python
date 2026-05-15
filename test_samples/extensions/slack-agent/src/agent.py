# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Slack sample agent. Ports the SlackAgent C# sample to Python.

- ``-stream`` triggers a streaming response built with ``SlackStream``.
- ``-buttons`` posts a Block Kit message with two interactive buttons.
- Any other Slack message echoes back via ``chat.postMessage`` (so we exercise
  the direct-to-Slack API path rather than ``context.send_activity``).
- All Slack events get a ``"Agent got: {name}"`` reply.
- ``conversationUpdate`` with members added sends a welcome via the standard
  activity pipeline.
"""

from __future__ import annotations

import asyncio

from microsoft_agents.activity import ConversationUpdateTypes
from microsoft_agents.hosting.core import RouteRank, TurnContext, TurnState
from microsoft_agents.hosting.slack import SlackAgentExtension
from microsoft_agents.hosting.slack.api import (
    MarkdownTextChunk,
    SlackChannelData,
    SlackTaskStatus,
    TaskUpdateChunk,
)

from .app import APP

slack = SlackAgentExtension[TurnState](APP)


@APP.conversation_update(ConversationUpdateTypes.MEMBERS_ADDED)
async def welcome_added_members(context: TurnContext, state: TurnState):
    for member in context.activity.members_added or []:
        if member.id != context.activity.recipient.id:
            await context.send_activity("Hello and Welcome!")


@slack.on_message("-stream")
async def on_slack_stream_message(context: TurnContext, state: TurnState):
    stream = await slack.create_stream(context)
    try:
        await stream.append(
            TaskUpdateChunk(
                id="task1", title="Working it", status=SlackTaskStatus.IN_PROGRESS
            )
        )
        await asyncio.sleep(2)

        await stream.append("This ")
        await asyncio.sleep(1.5)

        await stream.append(
            [
                MarkdownTextChunk(text="is "),
                TaskUpdateChunk(
                    id="task1",
                    title="Still working it",
                    status=SlackTaskStatus.IN_PROGRESS,
                ),
            ]
        )
        await asyncio.sleep(1.5)

        await stream.append("a ")
        await asyncio.sleep(1.5)

        await stream.append("test.")
        await stream.append(
            TaskUpdateChunk(id="task1", title="Done", status=SlackTaskStatus.COMPLETE)
        )
    except Exception:
        await stream.append(
            TaskUpdateChunk(id="task1", title="Error", status=SlackTaskStatus.ERROR)
        )
    finally:
        # Block Kit feedback buttons:
        # https://docs.slack.dev/reference/block-kit/blocks/context-actions-block
        feedback_blocks = [
            {
                "type": "context_actions",
                "elements": [
                    {
                        "type": "feedback_buttons",
                        "action_id": "feedback",
                        "positive_button": {
                            "text": {"type": "plain_text", "text": "👍"},
                            "value": "positive_feedback",
                        },
                        "negative_button": {
                            "text": {"type": "plain_text", "text": "👎"},
                            "value": "negative_feedback",
                        },
                    }
                ],
            }
        ]
        await stream.stop(blocks=feedback_blocks)


@slack.on_message("-buttons")
async def on_slack_buttons(context: TurnContext, state: TurnState):
    channel_data = SlackChannelData.from_activity(context.activity)
    payload = {
        "channel": channel_data.channel,
        "thread_ts": channel_data.thread_ts,
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "Pick an option:"},
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Yes"},
                        "action_id": "button_yes",
                        "value": "yes",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "No"},
                        "action_id": "button_no",
                        "value": "no",
                    },
                ],
            },
        ],
    }
    await slack.call(context, "chat.postMessage", payload, token=channel_data.api_token)


@slack.on_message(rank=RouteRank.LAST)
async def on_slack_message(context: TurnContext, state: TurnState):
    channel_data = SlackChannelData.from_activity(context.activity)
    await slack.call(
        context,
        "chat.postMessage",
        {
            "channel": channel_data.channel,
            "text": f"You said: {context.activity.text}",
        },
        token=channel_data.api_token,
    )


@slack.on_event(rank=RouteRank.LAST)
async def on_slack_event(context: TurnContext, state: TurnState):
    channel_data = SlackChannelData.from_activity(context.activity)
    await slack.call(
        context,
        "chat.postMessage",
        {
            "channel": channel_data.channel,
            "text": f"Agent got: {context.activity.name}",
        },
        token=channel_data.api_token,
    )
