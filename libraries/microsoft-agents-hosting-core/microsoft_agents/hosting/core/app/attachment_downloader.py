# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Callable
from email.message import Message

import aiohttp

from microsoft_agents.activity import (
    Attachment,
    Channels,
)

from microsoft_agents.hosting.core.turn_context import TurnContext
from microsoft_agents.hosting.core.outbound_host_validator import OutboundHostValidator

from .input_file import InputFileDownloader, InputFile

_CONTENT_TYPE = "Content-Type"


class AttachmentDownloader(InputFileDownloader):

    def __init__(
        self,
        client_factory: Callable[[], aiohttp.ClientSession] | None = None,
        host_validator: OutboundHostValidator | None = None,
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

    @staticmethod
    def _parse_content_type(content_type: str) -> tuple[str, dict[str, str]] | None:
        email = Message()
        email[_CONTENT_TYPE] = content_type
        params = email.get_params()
        if params is None:
            return None
        # the first param is the mime-type
        # the later ones are the attribtues like "charset"
        return params[0][0], dict(params[1:])

    async def _download_file(self, attachment: Attachment) -> InputFile | None:
        """Downloads a single file from the given attachment.

        :param attachment: The attachment to download.
        :return: An InputFile instance if the download is successful, None otherwise.
        """
        if attachment.content_url and (
            attachment.content_url.startswith("https://")
            or attachment.content_url.startswith("http://localhost")
        ):
            remote_file_url = attachment.content_url

            if (
                self._host_validator
                and self._host_validator.enabled
                and not self._host_validator.is_allowed(remote_file_url)
            ):
                return None

            async with self._client_factory() as client:
                async with client.get(remote_file_url) as response:

                    if not response.status == 200:
                        return None

                    content_type_val = response.headers.get("Content-Type", "")
                    result = AttachmentDownloader._parse_content_type(content_type_val)
                    if result is None:
                        return None
                    content_type, _ = result
                    if content_type.startswith("image/"):
                        content_type = "image/png"

                    res = await response.read()

                    return InputFile(
                        content=res,
                        content_type=content_type,
                        content_url=attachment.content_url,
                        filename=attachment.name,
                    )
        else:
            return InputFile(
                attachment.content,
                attachment.content_type,
                content_url=attachment.content_url,
                filename=attachment.name,
            )
