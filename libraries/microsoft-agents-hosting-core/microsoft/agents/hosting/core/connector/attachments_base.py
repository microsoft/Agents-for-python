# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import abstractmethod
from typing import AsyncIterator, Optional, Protocol

from microsoft.agents.activity import AttachmentInfo


class AttachmentsBase(Protocol):
    @abstractmethod
    async def get_attachment_info(self, attachment_id: str) -> AttachmentInfo:
        raise NotImplementedError()

    @abstractmethod
    async def get_attachment(self) -> Optional[AsyncIterator[bytes]]:
        pass
