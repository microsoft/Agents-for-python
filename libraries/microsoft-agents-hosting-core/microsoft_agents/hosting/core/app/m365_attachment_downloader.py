# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Callable
from email.message import Message

import aiohttp

from microsoft_agents.activity import (
    Attachment,
    Channels,
)

from microsoft_agents.hosting.core.authorization import (
    AccessTokenProviderBase,
    Connections,
)
from microsoft_agents.hosting.core.turn_context import TurnContext
from microsoft_agents.hosting.core.outbound_host_validator import OutboundHostValidator

from .input_file import InputFileDownloader, InputFile


class M365AttachmentDownloader(InputFileDownloader):

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

        outgoing_app_id = context.identity.get_outgoing_app_id()
        if not outgoing_app_id:
            raise ValueError("No valid outgoing App ID found.")

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
                outgoing_app_id, self._scopes
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
        if not attachment.content_url:
            return None

        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        async with self._client_factory() as client:
            async with client.get(attachment.content_url, headers=headers) as response:
                if response.status != 200:
                    return None
                content = await response.read()

        return InputFile(
            content=content,
            filename=attachment.name or "unknown",
            content_type=attachment.content_type,
        )