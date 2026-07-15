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
    pass

class ExchangeSelect(SelectBase[Exchange]):
    """Select class specifically for filtering and asserting on Exchange model collections."""
    pass