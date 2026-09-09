# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json
from typing import Callable, cast, Any

import aiohttp

from microsoft_agents.activity import (
    Attachment,
    Channels,
    ChannelId,
)

from microsoft_agents.hosting.core.authorization import (
    AccessTokenProviderBase,
    Connections,
)
from microsoft_agents.hosting.core.turn_context import TurnContext
from microsoft_agents.hosting.core.outbound_host_validator import OutboundHostValidator

from .input_file import InputFileDownloader, InputFile
from ._utils import _parse_content_type


class M365AttachmentDownloader(InputFileDownloader):
    """Downloads attachments from M365/Teams using the configured Token Provider (from Connections)."""

    def __init__(
        self,
        connections: Connections,
        client_factory: Callable[[], aiohttp.ClientSession] | None = None,
        host_validator: OutboundHostValidator | None = None,
        *,
        token_provider_name: str = "",
        use_anonymous: bool = False,
        scopes: list[str] | None = None,
    ):
        """Constructor for M365AttachmentDownloader.

        :param connections: A Connections instance.
        :param client_factory: A callable that returns an aiohttp.ClientSession instance.
        :param host_validator: An optional OutboundHostValidator instance.
        :param token_provider_name: The name of the token provider.
        :param use_anonymous: Whether to use anonymous access.
        :param scopes: A list of scopes for the access token.
        :param connections: A Connections instance.
        """

        self._connections = connections
        self._client_factory = client_factory or aiohttp.ClientSession
        self._host_validator = host_validator

        self._token_provider_name = token_provider_name
        self._use_anonymous = use_anonymous
        self._scopes = scopes or []

    async def download_files(self, context: TurnContext) -> list[InputFile]:
        """Download files from the given context.

        :param context: The TurnContext instance.
        :return: A list of InputFile instances.
        """

        if not context.identity:
            raise ValueError("No valid context identity found.")

        outgoing_audience_claim = context.identity.get_outgoing_audience_claim()
        if not outgoing_audience_claim:
            raise ValueError("No valid outgoing App ID found.")

        if context.activity.channel_id not in (Channels.ms_teams, Channels.m365_copilot):
            return []

        attachments: list[Attachment]
        if not context.activity.attachments:
            return []
        attachments = [
            att
            for att in context.activity.attachments
            if not att.content_type.startswith("text/html")
        ]
        if not attachments:
            return []

        access_token = ""

        if not self._use_anonymous:
            token_provider: AccessTokenProviderBase | None = None
            if self._token_provider_name:
                try:
                    token_provider = self._connections.get_connection(self._token_provider_name)
                except ValueError:
                    pass
            if not token_provider:
                token_provider = self._connections.get_token_provider_from_activity(
                    context.identity, context.activity
                )
            if not token_provider:
                raise RuntimeError("No valid token provider found.")
            
            access_token = await token_provider.get_access_token(
                outgoing_audience_claim, self._scopes
            )

        files: list[InputFile] = []
        for att in attachments:
            file = await self._download_file(att, access_token)
            if file:
                files.append(file)

        return files

    async def _download_file(self, attachment: Attachment, access_token: str) -> InputFile | None:
        """Download a single file from the given attachment.

        :param attachment: The Attachment instance.
        :param access_token: The access token for authentication.
        :return: An InputFile instance or None if the download fails.
        """
        name = attachment.name

        if attachment.content_url and (
            attachment.content_url.startswith("https://")
            or attachment.content_url.startswith("http://localhost")
        ):
            download_url: str
            if isinstance(attachment.content, dict):
                content_dict = cast(dict[str, Any], attachment.content)
                download_url = content_dict.get("downloadUrl", attachment.content_url)
            else:
                download_url = attachment.content_url

            if (
                self._host_validator is not None
                and self._host_validator.enabled
                and not self._host_validator.is_allowed(download_url)
            ):
                return None

            async with self._client_factory() as client:
                async with client.get(download_url, headers={"Authorization": f"Bearer {access_token}"}) as response:
                    if response.status >= 300:
                        return None
                    content = await response.read()
                    result = _parse_content_type(response.headers.get("Content-Type", ""))
                    if result is None:
                        return None
                    content_type, _ = result
                    if content_type.startswith("image/"):
                        content_type = "image/png"

                    return InputFile(
                        content=content,
                        content_type=content_type,
                        content_url=attachment.content_url,
                        filename=name,
                    )
        else:
            content = bytes(json.dumps(attachment.content), "utf-8")
            return InputFile(
                content=content,
                content_type=attachment.content_type,
                content_url=attachment.content_url,
                filename=attachment.name,
            )