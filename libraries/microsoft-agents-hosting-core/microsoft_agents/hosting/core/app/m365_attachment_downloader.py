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
        self._client_factory = client_factory or (lambda: aiohttp.ClientSession())
        self._host_validator = host_validator

        self._token_provider_name = token_provider_name
        self._use_anonymous = use_anonymous
        self._scopes = scopes or []

    async def download_files(self, context: TurnContext) -> list[InputFile]:
        """Download files from the given context.

        :param context: The TurnContext instance.
        :return: A list of InputFile instances.
        """
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
            token_provider: AccessTokenProviderBase
            if not self._token_provider_name:
                token_provider = self._connections.get_token_provider_from_activity(
                    context.identity, context.activity
                )
            else:
                try:
                    token_provider = self._connections.get_connection(
                        self._token_provider_name
                    )
                except ValueError:
                    token_provider = self._connections.get_token_provider_from_activity(
                        context.identity, context.activity
                    )

            access_token = await token_provider.get_access_token(
                context.identity.get_outgoing_audience(), self._scopes
            )

        files: list[InputFile] = []
