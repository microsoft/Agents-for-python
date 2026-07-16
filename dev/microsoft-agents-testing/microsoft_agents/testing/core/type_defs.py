# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.activity import Activity

from .fluent import ExpectBase, SelectBase
from .transport import Exchange

class ActivityExpect(ExpectBase[Activity]):
    """Expect class specifically for asserting on activity collections."""
    pass

class ExchangeExpect(ExpectBase[Exchange]):
    """Expect class specifically for asserting on Exchange model collections."""
    pass

class ActivitySelect(SelectBase[Activity]):
    """Select class specifically for filtering and asserting on activity collections."""

    def expect(self) -> ActivityExpect:
        """Get an ActivityExpect instance for assertions on the current selection."""
        return ActivityExpect(self._items)

class ExchangeSelect(SelectBase[Exchange]):
    """Select class specifically for filtering and asserting on Exchange model collections."""

    def expect(self) -> ExchangeExpect:
        """Get an ExchangeExpect instance for assertions on the current selection."""
        return ExchangeExpect(self._items)
