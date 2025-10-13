# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import asyncio
import json
import os
import re

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from .transcript_logger import TranscriptLogger
from .transcript_logger import PagedResult
from .transcript_info import TranscriptInfo

from microsoft_agents.activity import Activity  # type: ignore


class FileTranscriptStore(TranscriptLogger):
    """
    Python port of the .NET FileTranscriptStore which creates a single
    `.transcript` file per conversation and appends each Activity as newline-delimited JSON.

    Layout on disk:
        <root>/<channelId>/<conversationId>.transcript

    - Each line is a JSON object representing one Activity.
    - Methods are async to match the Agents SDK shape.

    Notes
    -----
    * Continuation tokens are simple integer byte offsets encoded as strings.
    * Activities are written using UTF-8 with newline separators (JSONL).
    * Filenames are sanitized to avoid path traversal and invalid characters.

    Inspired by the .NET design for FileTranscriptLogger. See:
      - Microsoft.Bot.Builder FileTranscriptLogger docs (for behavior)  [DOTNET]
      - Microsoft.Agents.Storage.Transcript namespace overview           [AGENTS]
    """

    def __init__(self, root_folder: Union[str, Path]) -> None:
        self._root = Path(root_folder).expanduser().resolve()
        self._root.mkdir(parents=True, exist_ok=True)

        # precompiled regex for safe names (letters, digits, dash, underscore, dot)
        self._safe = re.compile(r"[^A-Za-z0-9._-]+")

    # -------- Logger surface --------

    async def log_activity(self, activity: Activity) -> None:
        """
        Asynchronously persist a transcript activity to the file system.
        This method computes the transcript file path based on the activity’s channel
        and conversation identifiers, ensures the directory exists, and appends the
        activity data to the transcript file in JSON format using a background thread.
        If the activity lacks a timestamp, one is assigned prior to serialization.
        :param activity: The activity to log.
        """
        if not activity:
            raise ValueError("Activity is required")

        channel_id, conversation_id = _get_ids(activity)
        file_path = self._file_path(channel_id, conversation_id)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure a stable timestamp property if absent
        # Write in a background thread to avoid blocking the event loop
        def _write() -> None:
            # Normalize to a dict to ensure json serializable content.
            if not activity.timestamp:
                activity.timestamp = datetime.now(timezone.utc)

            with open(file_path, "a", encoding="utf-8", newline="\n") as f:
                f.write(activity.model_dump_json(exclude_none=True, exclude_unset=True))
                f.write("\n")

        await asyncio.to_thread(_write)

    # -------- Store surface --------

    async def list_transcripts(self, channel_id: str) -> PagedResult[TranscriptInfo]:
        """
        List transcripts (conversations) for a channel.
        :param channel_id: The channel ID to list transcripts for."""
        channel_dir = self._channel_dir(channel_id)

        def _list() -> List[TranscriptInfo]:
            if not channel_dir.exists():
                return []
            results: List[TranscriptInfo] = []
            for p in channel_dir.glob("*.transcript"):
                # mtime is a reasonable proxy for 'created/updated'
                created = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
                results.append(
                    TranscriptInfo(
                        channel_id=_sanitize(self._safe, channel_id),
                        conversation_id=p.stem,
                        created_on=created,
                    )
                )
            # Sort newest first (consistent, useful default)
            results.sort(key=lambda t: t.created_on, reverse=True)
            return results

        items = await asyncio.to_thread(_list)
        return PagedResult(items=items, continuation_token=None)

    async def get_transcript_activities(
        self,
        channel_id: str,
        conversation_id: str,
        continuation_token: Optional[str] = None,
        start_date: Optional[datetime] = None,
        page_bytes: int = 512 * 1024,
    ) -> PagedResult[Activity]:
        """
        Read activities from the transcript file (paged by byte size).
        :param channel_id: The channel ID of the conversation.
        :param conversation_id: The conversation ID to read activities from.
        :param continuation_token: Optional continuation token (byte offset as string).
        :param start_date: Optional filter to only include activities on or after this date.
        :param page_bytes: Maximum number of bytes to read (default: 512kB).
        :return: A PagedResult containing a list of Activities and an optional continuation token.
        """
        file_path = self._file_path(channel_id, conversation_id)

        def _read_page() -> Tuple[List[Activity], Optional[str]]:
            if not file_path.exists():
                return [], None

            offset = int(continuation_token) if continuation_token else 0
            results: List[Activity] = []

            with open(file_path, "rb") as f:
                f.seek(0, os.SEEK_END)
                end = f.tell()
                if offset > end:
                    return [], None
                f.seek(offset)
                # Read a chunk
                raw = f.read(page_bytes)
                # Extend to end of current line to avoid cutting a JSON record in half
                # (read until newline or EOF)
                while True:
                    ch = f.read(1)
                    if not ch:
                        break
                    raw += ch
                    if ch == b"\n":
                        break

                next_offset = f.tell()
            # Decode and split lines
            text = raw.decode("utf-8", errors="ignore")
            lines = [ln for ln in text.splitlines() if ln.strip()]

            # Parse JSONL
            for ln in lines:
                try:
                    a = Activity.model_validate_json(ln)
                except Exception:
                    # Skip malformed lines
                    continue
                if start_date:
                    if a.timestamp and a.timestamp < start_date.astimezone(
                        timezone.utc
                    ):
                        continue
                results.append(a)

            token = str(next_offset) if next_offset < end else None
            return results, token

        items, token = await asyncio.to_thread(_read_page)
        return PagedResult(items=items, continuation_token=token)

    async def delete_transcript(self, channel_id: str, conversation_id: str) -> None:
        """Delete the specified conversation transcript file (no-op if absent)."""
        file_path = self._file_path(channel_id, conversation_id)

        def _delete() -> None:
            try:
                file_path.unlink(missing_ok=True)
            except Exception:
                # Best-effort deletion: ignore failures (locked file, etc.)
                pass

        await asyncio.to_thread(_delete)

    # ----------------------------
    # Helpers
    # ----------------------------

    def _channel_dir(self, channel_id: str) -> Path:
        return self._root / _sanitize(self._safe, channel_id)

    def _file_path(self, channel_id: str, conversation_id: str) -> Path:
        safe_channel = _sanitize(self._safe, channel_id)
        safe_conv = _sanitize(self._safe, conversation_id)
        return self._root / safe_channel / f"{safe_conv}.transcript"


# ----------------------------
# Module-level helpers
# ----------------------------


def _sanitize(pattern: re.Pattern[str], value: str) -> str:
    # Replace path-separators and illegal filename chars with '-'
    value = (value or "").strip().replace(os.sep, "-").replace("/", "-")
    value = pattern.sub("-", value)
    return value or "unknown"


def _get_ids(activity: Activity) -> Tuple[str, str]:
    # Works with both dict-like and object-like Activity
    def _get(obj: Any, *path: str) -> Optional[Any]:
        cur = obj
        for key in path:
            if cur is None:
                return None
            if isinstance(cur, dict):
                cur = cur.get(key)
            else:
                cur = getattr(cur, key, None)
        return cur

    channel_id = _get(activity, "channel_id") or _get(activity, "channelId")
    conversation_id = _get(activity, "conversation", "id")
    if not channel_id or not conversation_id:
        raise ValueError("Activity must include channel_id and conversation.id")
    return str(channel_id), str(conversation_id)


def _to_plain_dict(activity: Activity) -> Dict[str, Any]:

    if isinstance(activity, dict):
        return activity
    # Best-effort conversion for dataclass/attr/objects
    try:
        import dataclasses

        if dataclasses.is_dataclass(activity):
            return dataclasses.asdict(activity)  # type: ignore[arg-type]
    except Exception:
        pass
    try:
        return json.loads(
            json.dumps(activity, default=lambda o: getattr(o, "__dict__", str(o)))
        )
    except Exception:
        # Fallback: minimal projection
        channel_id, conversation_id = _get_ids(activity)
        return {
            "type": getattr(activity, "type", "message"),
            "id": getattr(activity, "id", None),
            "channel_id": channel_id,
            "conversation": {"id": conversation_id},
            "text": getattr(activity, "text", None),
        }
