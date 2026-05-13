"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from aiohttp import ClientSession, ClientTimeout
from pydantic import BaseModel

from .slack_response import SlackResponse, SlackResponseException

SLACK_API_BASE = "https://slack.com/api"


def _serialize_options(options: Any) -> str:
    """Serialize the ``options`` argument to a JSON string suitable for Slack.

    - ``None`` becomes ``"{}"``.
    - A pre-built JSON string is returned as-is.
    - A Pydantic model is dumped with ``exclude_none=True`` to match Slack's
      tolerance of omitted fields and the C# implementation's null-stripping.
    - Anything else is passed through :func:`json.dumps`, after recursively
      removing ``None`` values from dicts/lists.
    """
    if options is None:
        return "{}"
    if isinstance(options, str):
        return options
    if isinstance(options, BaseModel):
        return options.model_dump_json(by_alias=True, exclude_none=True)
    return json.dumps(_strip_nones(options), ensure_ascii=False)


def _strip_nones(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _strip_nones(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_strip_nones(v) for v in value]
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", by_alias=True, exclude_none=True)
    return value


class SlackApi:
    """
    Async HTTP client for the Slack Web API.

    Mirrors the C# ``SlackApi``: every call is a ``POST`` to
    ``https://slack.com/api/{method}`` with a JSON body and an optional bearer
    token. The response body is parsed into a :class:`SlackResponse`; a
    :class:`SlackResponseException` is raised on a non-2xx HTTP status or when
    Slack returns ``ok=false``.
    """

    def __init__(
        self,
        session: Optional[ClientSession] = None,
        *,
        base_url: str = SLACK_API_BASE,
        request_timeout: float = 30.0,
    ) -> None:
        self._session = session
        self._owns_session = session is None
        self._base_url = base_url
        self._timeout = ClientTimeout(total=request_timeout)

    async def call(
        self,
        method: str,
        options: Any = None,
        token: str = "",
    ) -> SlackResponse:
        """Invoke a Slack Web API method.

        :param method: The API method name (e.g. ``"chat.postMessage"``).
        :param options: Request payload. May be ``None``, a JSON string, a
            ``dict`` / ``list``, or a Pydantic model.
        :param token: Bearer token. Sent as ``Authorization: Bearer {token}``
            when non-empty.
        :returns: The parsed :class:`SlackResponse`.
        :raises ValueError: if ``method`` is empty or whitespace.
        :raises SlackResponseException: on HTTP error or ``ok=false``.
        """
        if not method or not method.strip():
            raise ValueError("method must be a non-empty string")

        body = _serialize_options(options)
        url = f"{self._base_url}/{method}"
        headers = {"Content-Type": "application/json"}
        if token and token.strip():
            headers["Authorization"] = f"Bearer {token}"

        session = self._session or ClientSession()
        try:
            async with session.post(
                url, data=body, headers=headers, timeout=self._timeout
            ) as response:
                text = await response.text()
                try:
                    payload = json.loads(text) if text else {}
                    data = SlackResponse.model_validate(payload)
                except Exception as exc:
                    raise SlackResponseException(
                        f"Slack API error on {method} (HTTP {response.status}):\n{text}"
                    ) from exc

                if not response.ok or not data.ok:
                    raise SlackResponseException(
                        f"Slack API error on {method} (HTTP {response.status}):\n{text}",
                        data,
                    )

                return data
        finally:
            if self._owns_session:
                await session.close()
