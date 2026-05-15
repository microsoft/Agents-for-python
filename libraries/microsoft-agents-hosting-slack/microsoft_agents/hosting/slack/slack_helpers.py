"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from typing import Optional


def slack_encode(value: Optional[str]) -> Optional[str]:
    """Encode text for Slack. See https://api.slack.com/docs/message-formatting."""
    if value is None:
        return None
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def slack_decode(value: Optional[str]) -> Optional[str]:
    """Decode text from Slack. See https://api.slack.com/docs/message-formatting."""
    if value is None:
        return None
    return value.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")


def create_conversation_id(
    slack_bot_id: str,
    slack_team_id: str,
    slack_channel_id: str,
    slack_thread_ts: Optional[str] = None,
) -> str:
    """Compose a Bot Service-compatible conversation id from Slack identifiers."""
    if slack_thread_ts is None:
        return f"{slack_bot_id}:{slack_team_id}:{slack_channel_id}"
    return f"{slack_bot_id}:{slack_team_id}:{slack_channel_id}:{slack_thread_ts}"


def _from_conversation_id(conversation_id: str, pos: int) -> Optional[str]:
    if conversation_id is None or not conversation_id.strip():
        raise ValueError("conversation_id must be a non-empty string")
    parts = conversation_id.split(":")
    if len(parts) not in (3, 4):
        raise ValueError(f"Invalid conversation_id: {conversation_id}")
    if pos >= len(parts):
        return None
    return parts[pos]


def slack_bot_id_from_conversation_id(conversation_id: str) -> Optional[str]:
    return _from_conversation_id(conversation_id, 0)


def slack_team_id_from_conversation_id(conversation_id: str) -> Optional[str]:
    return _from_conversation_id(conversation_id, 1)


def slack_channel_id_from_conversation_id(conversation_id: str) -> Optional[str]:
    return _from_conversation_id(conversation_id, 2)


def slack_thread_ts_from_conversation_id(conversation_id: str) -> Optional[str]:
    return _from_conversation_id(conversation_id, 3)
