# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Callable

import aiohttp

from microsoft_agents.activity import (
    Attachment,
    Channels,
)

from microsoft_agents.hosting.core.turn_context import TurnContext
from microsoft_agents.hosting.core.outbound_host_validator import OutboundHostValidator

from .input_file import InputFileDownloader, InputFile

class AttachmentDownloader(InputFileDownloader):
    

    def __init__(
            self,
            client_factory: Callable[[], aiohttp.ClientSession] | None = None,
            host_validator: OutboundHostValidator | None = None
    ):
        """Constructor for AttachmentDownloader.
        
        :param client_factory: A callable that returns an aiohttp.ClientSession instance.
        :param host_validator: An optional OutboundHostValidator instance.
        """

        self._client_factory = client_factory or (lambda: aiohttp.ClientSession())
        self._host_validator = host_validator

    async def download_files(self, context: TurnContext) -> list[InputFile]:
        """Downloads files for the given turn context.

        :param context: The TurnContext instance for the current turn.
        """
        if context.activity.channel_id.get_channel() == Channels.ms_teams:
            return []

        if not context.activity.attachments:
            return []

        files: list[InputFile] = []
        for attachment in context.activity.attachments:
            file = await self._download_file(attachment)
            if file:
                files.append(file)

        return files

    async def _download_file(self, attachment) -> InputFile | None:
        """Downloads a single file from the given attachment.

        :param attachment: The attachment to download.
        :return: An InputFile instance if the download is successful, None otherwise.
        """

        name = attachment.name

        if attachment.content_url and attachment.content_url.startswith("https://") || attachment.content_url.startswith("http://localhost"):
            remote_file_url = attachment.content_url

            if self._host_validator and self._host_validator.enabled and not self._host_validator.is_allowed(remote_file_url):
                return None

            async with self._client_factory() as client:
                async with client.get(remote_file_url) as response:
                    

            client = self._client_factory()


        # Implement the actual download logic here.
        # For now, just return an InputFile instance with the attachment.
        return InputFile(attachment)