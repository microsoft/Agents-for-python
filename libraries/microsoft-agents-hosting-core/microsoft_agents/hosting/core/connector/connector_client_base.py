# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import abstractmethod
from typing import Protocol, runtime_checkable

from .attachments_base import AttachmentsBase
from .conversations_base import ConversationsBase


@runtime_checkable
class ConnectorClientBase(Protocol):
    @property
    @abstractmethod
    def base_uri(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def attachments(self) -> AttachmentsBase:
        pass

    @property
    @abstractmethod
    def conversations(self) -> ConversationsBase:
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the client and release any resources."""
        raise NotImplementedError("close method must be implemented by subclasses.")