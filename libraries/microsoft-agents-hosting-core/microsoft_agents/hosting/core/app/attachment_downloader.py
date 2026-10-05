# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json
import logging
from typing import Any, Callable

import aiohttp

from microsoft_agents.activity import (
    Attachment,
    Channels,
    ChannelId,
)

from microsoft_agents.hosting.core.turn_context import TurnContext
from microsoft_agents.hosting.core.security import (
    OutboundHostValidator,
    _SSRFError,
)

from .input_file import InputFileDownloader, InputFile
from ._utils import _parse_content_type, _basic_url_check

logger = logging.getLogger(__name__)


class AttachmentDownloader(InputFileDownloader):
    """Downloads attachments from a given turn context."""

    def __init__(
        self,
        host_validator: OutboundHostValidator | None = None,
        *,
        client_session_kwargs: dict | None = None,
        client_factory: Any = None,
    ):
        """Constructor for AttachmentDownloader.

        :param host_validator: An optional OutboundHostValidator instance.
        :param client_session_kwargs: Optional keyword arguments for the aiohttp.ClientSession.
        :param client_factory: (deprecated) A custom client factory, if any.
        """

        if client_factory is not None:
            logger.warning(
                "The 'client_factory' parameter is deprecated and will be ignored."
            )

        self._client_session_kwargs = client_session_kwargs or {}
        self._host_validator = host_validator

    async def download_files(self, context: TurnContext) -> list[InputFile]:
        """Downloads files for the given turn context.

        :param context: The TurnContext instance for the current turn.
        :return: A list of InputFile instances representing the downloaded files.
        """
        if ChannelId.get_channel(context.activity.channel_id) == Channels.ms_teams:
            return []

        if not context.activity.attachments:
            return []

        client_factory: Callable[[], aiohttp.ClientSession]
        if self._host_validator is not None:
            host_validator = self._host_validator  # to capture in lambda
            client_factory = lambda: host_validator.client(self._client_session_kwargs)
        else:
            client_factory = lambda: aiohttp.ClientSession(
                **self._client_session_kwargs
            )

        async with client_factory() as client:
            files: list[InputFile] = []
            for attachment in context.activity.attachments:
                file = await self._download_file(client, attachment)
                if file:
                    files.append(file)
        return files

    async def _download_file(
        self, client: aiohttp.ClientSession, attachment: Attachment
    ) -> InputFile | None:
        """Downloads a single file from the given attachment.

        :param client: The aiohttp.ClientSession instance to use for downloading the file.
        :param attachment: The attachment to download.
        :return: An InputFile instance if the download is successful, None otherwise.
        """
        if attachment.content_url and _basic_url_check(attachment.content_url):
            remote_file_url = attachment.content_url

            try:
                async with client.get(remote_file_url) as response:

                    if not (200 <= response.status < 300):
                        return None

                    content_type_val = response.headers.get("Content-Type", "")
                    result = _parse_content_type(content_type_val)
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
            except _SSRFError:
                logger.warning(
                    "Outbound host validation failed for download URL: %s",
                    remote_file_url,
                )
                return None
        else:
            content = bytes(json.dumps(attachment.content), "utf-8")
            return InputFile(
                content=content,
                content_type=attachment.content_type,
                content_url=attachment.content_url,
                filename=attachment.name,
            )
