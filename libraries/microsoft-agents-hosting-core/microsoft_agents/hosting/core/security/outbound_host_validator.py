# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Protocol, runtime_checkable
from yarl import URL

@runtime_checkable
class _OutboundHostValidator(Protocol):

    @property
    def enabled(self) -> bool:
        ...

    def is_allowed(self, url: str | URL) -> bool:
        ...

class OutboundHostValidator(_OutboundHostValidator):

    def __init__(self, enabled: bool):
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    def is_allowed(self, url: str | URL) -> bool:
        # Implement your logic to check if the URL is allowed
        return True