"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from microsoft_agents.hosting.core import TurnContext


@dataclass
class InputFile:
    """A file sent by the user to the bot.

    :param content: The downloaded content of the file.
    :type content: bytes
    :param content_type: The content type of the file.
    :type content_type: str
    :param content_url: Optional. URL to the content of the file.
    :type content_url: Optional[str]
    """

    content: bytes
    content_type: str
    content_url: Optional[str]


class InputFileDownloader(ABC):
    """
    Abstract base class for a plugin responsible for downloading files provided by the user.

    Implementations should download any files referenced by the incoming activity and return a
    list of :class:`InputFile` instances representing the downloaded content.
    """

    @abstractmethod
    async def download_files(self, context: TurnContext) -> List[InputFile]:
        """
        Download any files referenced by the incoming activity for the current turn.

        :param context: The turn context for the current request.
        :type context: :class:`microsoft_agents.hosting.core.turn_context.TurnContext`
        :return: A list of downloaded :class:`InputFile` objects.
        :rtype: list[:class:`microsoft_agents.hosting.core.app.input_file.InputFile`]
        """
