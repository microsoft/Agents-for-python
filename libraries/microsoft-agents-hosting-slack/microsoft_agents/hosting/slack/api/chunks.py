"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.

Streaming chunk shapes for Slack ``chat.appendStream`` / ``chat.stopStream``.
See https://docs.slack.dev/reference/methods/chat.appendStream
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class SlackTaskStatus:
    """Status values accepted by :class:`TaskUpdateChunk`."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    ERROR = "error"


class TaskDisplayMode:
    """Values accepted by ``chat.startStream``'s ``task_display_mode``."""

    PLAN = "plan"
    TIMELINE = "timeline"


class Source(BaseModel):
    """Citation/source attached to a :class:`TaskUpdateChunk`."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    type: str = "url"
    url: str = ""
    text: str = ""


class MarkdownTextChunk(BaseModel):
    """Append a chunk of markdown-formatted text to a Slack stream."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    type: str = Field(default="markdown_text", frozen=True)
    text: str = ""


class BlocksChunk(BaseModel):
    """Append a chunk of Block Kit blocks to a Slack stream."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    type: str = Field(default="blocks", frozen=True)
    blocks: list[Any] = Field(default_factory=list)


class TaskUpdateChunk(BaseModel):
    """Append a task-status update chunk to a Slack stream."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    type: str = Field(default="task_update", frozen=True)
    id: str
    title: str
    status: str = SlackTaskStatus.IN_PROGRESS
    details: Optional[str] = None
    output: Optional[str] = None
    sources: Optional[list[Source]] = None


# Type alias for any chunk variant.
Chunk = (
    BaseModel  # all chunk classes are BaseModel subclasses with a `type` discriminator
)
