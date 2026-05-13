"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import json
from typing import Any, Optional, Sequence, Union

from pydantic import BaseModel

from .chunks import MarkdownTextChunk, TaskDisplayMode
from .slack_api import SlackApi


def _chunk_to_dict(chunk: Any) -> Any:
    if isinstance(chunk, BaseModel):
        return chunk.model_dump(mode="json", by_alias=True, exclude_none=True)
    return chunk


class SlackStream:
    """
    Incrementally builds and updates a single Slack message via
    ``chat.startStream`` / ``chat.appendStream`` / ``chat.stopStream``.

    Not thread-safe; concurrent operations on the same instance produce
    undefined behavior. Call :meth:`start` before :meth:`append`, and
    :meth:`stop` when finished.
    """

    def __init__(
        self,
        slack_api: SlackApi,
        channel: str,
        thread_ts: str,
        token: str,
    ) -> None:
        self._slack_api = slack_api
        self._channel = channel
        self._thread_ts = thread_ts
        self._token = token
        self._message_ts: Optional[str] = None

    async def start(
        self, task_display_mode: str = TaskDisplayMode.PLAN
    ) -> "SlackStream":
        """Start a new Slack stream.

        See https://docs.slack.dev/reference/methods/chat.startStream
        """
        result = await self._slack_api.call(
            "chat.startStream",
            {
                "channel": self._channel,
                "thread_ts": self._thread_ts,
                "task_display_mode": task_display_mode,
            },
            self._token,
        )
        self._message_ts = result.ts
        return self

    async def append(
        self,
        chunk_or_text: Union[str, BaseModel, Sequence[BaseModel]],
    ) -> "SlackStream":
        """Append one or more chunks to the stream.

        Accepts a plain string (wrapped in a :class:`MarkdownTextChunk`), a
        single chunk model, or an iterable of chunk models.

        See https://docs.slack.dev/reference/methods/chat.appendStream
        """
        if chunk_or_text is None:
            raise ValueError("chunk_or_text must not be None")

        if isinstance(chunk_or_text, str):
            chunks: list[Any] = [MarkdownTextChunk(text=chunk_or_text)]
        elif isinstance(chunk_or_text, BaseModel):
            chunks = [chunk_or_text]
        else:
            chunks = list(chunk_or_text)

        if not chunks:
            return self

        await self._slack_api.call(
            "chat.appendStream",
            {
                "channel": self._channel,
                "ts": self._message_ts,
                "thread_ts": self._thread_ts,
                "chunks": [_chunk_to_dict(c) for c in chunks],
            },
            self._token,
        )
        return self

    async def stop(
        self,
        chunks: Optional[Sequence[BaseModel]] = None,
        blocks: Union[str, Sequence[Any], dict, None] = None,
    ) -> None:
        """Stop the active stream, optionally finalizing with chunks and/or
        Block Kit blocks.

        ``blocks`` may be a JSON-array string, a JSON-object string containing
        a ``"blocks"`` array, a Python list of block dicts, or a dict with a
        top-level ``"blocks"`` key.

        See https://docs.slack.dev/reference/methods/chat.stopStream
        """
        if not self._message_ts:
            return

        resolved_blocks = self._resolve_blocks(blocks)
        resolved_chunks = (
            [_chunk_to_dict(c) for c in chunks] if chunks is not None else None
        )

        body: dict[str, Any] = {
            "channel": self._channel,
            "ts": self._message_ts,
            "thread_ts": self._thread_ts,
        }
        if resolved_chunks is not None:
            body["chunks"] = resolved_chunks
        if resolved_blocks is not None:
            body["blocks"] = resolved_blocks

        await self._slack_api.call("chat.stopStream", body, self._token)

    @staticmethod
    def _resolve_blocks(blocks: Any) -> Optional[list[Any]]:
        if blocks is None:
            return None
        if isinstance(blocks, str):
            try:
                parsed = json.loads(blocks)
            except json.JSONDecodeError as exc:
                raise ValueError("blocks string is not valid JSON") from exc
            return SlackStream._resolve_blocks(parsed)
        if isinstance(blocks, dict):
            if "blocks" not in blocks or not isinstance(blocks["blocks"], list):
                raise ValueError("blocks object must contain a 'blocks' array property")
            return blocks["blocks"]
        if isinstance(blocks, list):
            return blocks
        raise ValueError(
            "blocks must be a JSON array, a JSON object with a 'blocks' array, "
            "or a string encoding either"
        )
